import ezdxf
from ezdxf.math import BoundingBox2d
from ezdxf.colors import aci2rgb
import os
import sqlite3
import json
from DXFUtils import *
import datetime,math

def DXFSystem2(DXFFile,client):
    Project = EmptyProject()

    DXFItems = {
        "Regions": [],
        "Layouts": {},
        "Levels": {},
        "Grounds": {},
        "Connections": [],
        "TurningPosses": {},
    }

    CarrObjects = {}
    ShelfObjects = {}
    RoomObjects = []

    print(os.getcwd())
    SendMessage("Info", "Reading file... It takes some time. It is normal!",client)
    doc = ezdxf.readfile(DXFFile)
    SendMessage("Success", "Reading file complete.",client)
    msp = doc.modelspace()

    def GetShelfCapacity(entity):
        block = doc.blocks[entity.dxf.name]
        bbox = BoundingBox2d()
        for e in block:
            if e.DXFTYPE == "POINT":
                bbox.extend([e.dxf.location])
        return round((list(bbox)[1][1] + 110) / 226)

    SendMessage("Info", "Analyzing Entities...",client)

    PKEntities = {}

    for DXFEntity in msp.query("INSERT"):
        Attribs = [(attrib.dxf.tag, attrib.dxf.text) for attrib in DXFEntity.attribs]
        PKEntity = {}
        for tag, text in Attribs:
            PKEntity[tag] = text
        # Eğer COMP_TYPE varsa bize ait bir bloktur.

        if "COMP_TYPE" in PKEntity:
            PKEntity["absx"] = DXFEntity.dxf.insert[0]
            PKEntity["absy"] = DXFEntity.dxf.insert[1]
            PKEntity["Angle"] = DXFEntity.dxf.rotation
            PKEntity["dxf"] = DXFEntity
            if EncodeCompType(PKEntity)["Base"] == "REGION":
                block = doc.blocks[DXFEntity.dxf.name]
                bbox = BoundingBox2d()
                for e in block:
                    if hasattr(e, "vertices"):
                        bbox.extend(list(e.vertices()))
                DXFItems["Regions"].append({"xmin": PKEntity["absx"], "ymin": PKEntity["absy"], "xmax": PKEntity["absx"] + list(bbox)[1][0], "ymax": PKEntity["absy"] + list(bbox)[1][1]})
                SendMessage("Success",f"Region added at {(round(PKEntity['absx'],2), round(PKEntity['absy'],2))}.",client)
                Project["Name"] = PKEntity["PROJECT"]
                Project["Version"] = PKEntity["VERSION"]
                Project["Code"] = PKEntity["CODE"] if PKEntity["CODE"] else PKEntity["PROJECT"]

            else:
                if EncodeCompType(PKEntity)["Base"] in PKEntities:
                    PKEntities[EncodeCompType(PKEntity)["Base"]].append(PKEntity)
                else:
                    PKEntities[EncodeCompType(PKEntity)["Base"]] = [PKEntity]
        # Eğer COMP_TYPE yoksa da bize ait olabilir. O Zaman içindeki bloğa bakmak lazım

        else:
            for block in doc.blocks[DXFEntity.dxf.name]:
                if block.dxftype() == "INSERT":
                    Attribs2 = [(attrib.dxf.tag, attrib.dxf.text) for attrib in block.attribs]
                    PKAltEntity = {}
                    for tag2, text2 in Attribs2:
                        PKAltEntity[tag2] = text2
                    if "COMP_TYPE" in PKAltEntity:
                        PKEntity["dxf"] = DXFEntity
                        PKEntity["absx"] = DXFEntity.dxf.insert[0]
                        PKEntity["absy"] = DXFEntity.dxf.insert[1]
                        PKEntity["Angle"] = DXFEntity.dxf.rotation
                        color_aci= block.dxf.color
                        if block.dxf.color == 256:
                            layer_name = block.dxf.layer
                            layer = doc.layers.get(layer_name)
                            color_aci = layer.dxf.color  # This is the layer color ACI

                        # Convert ACI to RGB
                        color_rgb =  aci2rgb(color_aci)                        
                        PKEntity["Color"] =  color_rgb
                        if EncodeCompType(PKAltEntity)["Base"] == "BLOCK" or EncodeCompType(PKAltEntity)["Base"] == "STEELSTR" or EncodeCompType(PKAltEntity)["Base"] == "WALL":
                            PKEntity["Props"] = PKAltEntity
                            if EncodeCompType(PKAltEntity)["Base"] in PKEntities:
                                PKEntities[EncodeCompType(PKAltEntity)["Base"]].append(PKEntity)
                            else:
                                PKEntities[EncodeCompType(PKAltEntity)["Base"]] = [PKEntity]

    
    if DXFItems["Regions"]:
        TempEnt={}
        for Key in PKEntities:
            TempKey=[Entity for Entity in PKEntities[Key] if InTheBox(Entity, DXFItems)]
            if TempKey:
                TempEnt[Key] = TempKey 
        PKEntities=TempEnt    
    else:
        SendMessage("Warning", "There is no REGION found.",client)

    # Eğer REGION içinde eleman yoksa çık
    if not PKEntities:
        SendMessage("Error", "There are no valid entities!",client)
        return None

    if "PROJECT" in PKEntities:
        Project["Code"] = PKEntities["PROJECT"][0]["PROJECT_CODE"] if PKEntities["PROJECT"][0]["PROJECT_CODE"] else PKEntities["PROJECT"][0]["PROJECT_NAME"]
        Project["Name"] = PKEntities["PROJECT"][0]["PROJECT_NAME"]
        Project["Version"] = PKEntities["PROJECT"][0]["VERSION"]
    else:
        if not DXFItems["Regions"]:
            SendMessage("Error", "There must be at least one REGION or one PROJECT block at the project.",client)
            return None


    # GROUND elemanları ayıkla
    if "GROUND" in PKEntities:
        for Entity in PKEntities["GROUND"]:
            if Entity["GROUND_ID"] in DXFItems["Grounds"]:
                SendMessage("Error",f"Multiple Ground Id:{Entity['GROUND_ID']} at {(round(Entity['absx'],2), round(Entity['absy'],2))}.",client)
                return None
            else:
                if Entity["GROUND_ID"]:
                    DXFItems["Grounds"][Entity["GROUND_ID"]] = Entity
                    SendMessage("Success",f"Ground {Entity['GROUND_ID']} added at {(round(Entity['absx'],2), round(Entity['absy'],2))}.",client)


    # Eğer ROOM'lardan GROUND olarak kullanılan varsa onları Grounds'a ekle
    if "ROOM" in PKEntities:
        for Entity in PKEntities["ROOM"]:
            if "GROUND_ID" in Entity and Entity["GROUND_ID"]: # ensures iti is top side or back view
                if Entity["GROUND_ID"] not in DXFItems["Grounds"]:
                    DXFItems["Grounds"][Entity["GROUND_ID"]] = Entity
                    SendMessage("Success",f"Room added as Ground {Entity['GROUND_ID']} at {(round(Entity['absx'],2), round(Entity['absy'],2))}.",client)

    for Part in PKEntities.values():
        for Entity in Part:
            if "GROUND_ID" in Entity and "LEVEL_ID" in Entity and Entity["GROUND_ID"]:
                if Entity["GROUND_ID"] in DXFItems["Grounds"]: # demek ki bu ground id kayıtlı
                        Entity["Z"] = round(Entity["absy"] - DXFItems["Grounds"][Entity["GROUND_ID"]]["absy"], 3)
                        if Entity["LEVEL_ID"]: 
                            if Entity["LEVEL_ID"] not in DXFItems["Levels"]:
                                if Entity["LEVEL_ID"][0]=='L':
                                    DXFItems["Levels"][Entity["LEVEL_ID"]] = Entity
                                    SendMessage("Success",f"LEVEL {Entity['LEVEL_ID']} added for Z: {Entity['Z']} at {(round(Entity['absx'],2), round(Entity['absy'],2))}.",client)
                                else:
                                    SendMessage("Error",f"LEVEL_ID {Entity['LEVEL_ID']} must start with 'L' in the block at {(round(Entity['absx'],2), round(Entity['absy'],2))}.",client)
                                    return None
                            else:
                                SendMessage("Warning",f"Ignored block! Multiple LEVEL_ID {Entity['LEVEL_ID']} at {(round(Entity['absx'],2), round(Entity['absy'],2))}.",client)
                        else:
                            SendMessage("Warning",f"Ignored block! No LEVEL_ID entered at {(round(Entity['absx'],2), round(Entity['absy'],2))}",client)
                else:
                    SendMessage("Warning",f"Ignored block! Entered GROUND_ID not available {Entity['GROUND_ID']} at {(round(Entity['absx'],2), round(Entity['absy'],2))}.",client)


    if "LAYOUT" in PKEntities:
        for Entity in PKEntities["LAYOUT"]:
            Ids = Entity["LAYOUT_ID"].split(",") if Entity["LAYOUT_ID"] else []
            Levs = Entity["LEVEL"].split(",") if Entity["LEVEL"] else []
            if Ids: 
                if Levs: 
                    if len(Ids) == len(Levs):
                        for ind in range(len(Ids)):
                            Ent1 = {}
                            for e in Entity:
                                Ent1[e] = Entity[e]
                            Ent1["LAYOUT_ID"] = Ids[ind]
                            Ent1["LEVEL"] = Levs[ind]
                            Z1 = GetLevel(Levs[ind], DXFItems["Levels"])
                            if Z1 is None:
                                SendMessage("Error",f"LEVEL {Levs[ind]} is not valid in LAYOUT at {(round(Entity['absx'],2), round(Entity['absy'],2))}.",client)
                                return None
                            if Ids[ind] in DXFItems["Layouts"]:
                                SendMessage("Error",f"Multiple Layout Id in LAYOUT at {(round(Entity['absx'],2), round(Entity['absy'],2))}.",client)
                                return None
                            else:
                                if Ids[ind]:
                                    DXFItems["Layouts"][Ids[ind]] = Ent1
                                    SendMessage("Success",f"LAYOUT {Ent1['LAYOUT_ID']} added at {(round(Entity['absx'],2), round(Entity['absy'],2))}.",client)
                                else:
                                    SendMessage("Error",f"Layout Id is empty in LAYOUT at {(round(Entity['absx'],2), round(Entity['absy'],2))}.",client)
                                    return None
                    else:
                        SendMessage("Error",f"Count of LAYOUT_ID and LEVEL should be equal in LAYOUT at {(round(Entity['absx'],2), round(Entity['absy'],2))}.",client)
                        return None
                else:
                    SendMessage("Error",f"LEVEL should not be empty in LAYOUT at {(round(Entity['absx'],2), round(Entity['absy'],2))}.",client)
                    return None
    else:
        SendMessage("Error",f"There must be at least one LAYOUT in the Project",client)
        return None


            
    if "STEELSTR" in PKEntities:
        CompId=1
        for Entity in PKEntities["STEELSTR"]:
            BName = Entity["dxf"].dxf.name
            BDef = doc.blocks[BName]
            Lyts = Entity["Props"]["LAYOUT_ID"].split(",") if Entity["Props"]["LAYOUT_ID"] else []
            Tos = Entity["Props"]["TO"].split(",") if Entity["Props"]["TO"] else []
            Levs = Entity["Props"]["BEAM_LEVEL"].split(",") if Entity["Props"]["BEAM_LEVEL"] else []
            if Lyts[0] in DXFItems["Layouts"]:
                RefX = DXFItems["Layouts"][Lyts[0]]["absx"]
                RefY = DXFItems["Layouts"][Lyts[0]]["absy"]
            else:
                SendMessage("Error",f"LAYOUT_ID {Lyts[0]} is not valid in STEELSTR at {(round(Entity['absx'],2), round(Entity['absy'],2))}.",client)
                return None

            ColumnAdded=False
            BeamAdded=False
            if len(Lyts) == len(Tos):
                for Ent in BDef:
                    if Ent.dxftype() == "INSERT":
                        Attribs = [(attrib.dxf.tag, attrib.dxf.text) for attrib in Ent.attribs]
                        Enti = {}
                        for tag, text in Attribs:

                            Enti[tag] = text
                        if IsValidComp(Enti):
                            CompType = EncodeCompType(Enti)
                            if CompType["Base"] == "STEEL":
                                for i in range(len(Lyts)):

                                    if Lyts[i] in DXFItems["Layouts"]:
                                        Z1 = GetLevel(DXFItems["Layouts"][Lyts[i]]["LEVEL"], DXFItems["Levels"])
                                        if Z1 is None:
                                            SendMessage("Error",f"LEVEL {DXFItems['Layouts'][Lyts[i]]['LEVEL']} is not valid in STEELSTR at {(round(Entity['absx'],2), round(Entity['absy'],2))}.",client)
                                            return None
                                    else:
                                        SendMessage("Error",f"LAYOUT_ID {Lyts[i]} is not valid in STEELSTR at {(round(Entity['absx'],2), round(Entity['absy'],2))}.",client)
                                        return None
                                    Z2 = GetLevel(Tos[i], DXFItems["Levels"])
                                    if Z2 is None:
                                        SendMessage("Error",f"LEVEL {Tos[i]} is not valid in STEELSTR at {(round(Entity['absx'],2), round(Entity['absy'],2))}.",client)
                                        return None

                                    Steel = {
                                        "Type": CompType["PVar"],
                                        "Id":CompId,
                                        "X1": int(round(RefX - Entity["absx"] + Ent.dxf.insert[0], 0)) * 10,
                                        "Y1": int(round(RefY - Entity["absy"] + Ent.dxf.insert[1], 0)) * 10,
                                        "Z1": Z1 * 10,
                                        "X2": int(round(RefX - Entity["absx"] + Ent.dxf.insert[0], 0)) * 10,
                                        "Y2": int(round(RefY - Entity["absy"] + Ent.dxf.insert[1], 0)) * 10,
                                        "Z2": Z2 * 10 + int(Entity["Props"]["OFFSET"]) * 10,
                                        "Material":"Steel"
                                    }
                                    Project["_Steels"][CompId]=Steel
                                    ColumnAdded=True
                                    CompId+=1
                                    
                    elif Ent.dxftype() == "LINE":
                        for i in range(len(Levs)):
                            Z = GetLevel(Levs[i], DXFItems["Levels"])
                            if Z is None:
                                SendMessage("Error",f"LEVEL {Levs[i]} is not valid in STEELSTR at {(round(Entity['absx'],2), round(Entity['absy'],2))}.",client)
                                return None
                            Steel = {
                                "Type": Entity["Props"]["BEAM_TYPE"],
                                "Id":CompId,
                                "X1": int(round(RefX - Entity["absx"] + Ent.dxf.start[0], 0)) * 10,
                                "Y1": int(round(RefY - Entity["absy"] + Ent.dxf.start[1], 0)) * 10,
                                "Z1": int(Z) * 10 + int(Entity["Props"]["BEAM_OFFSET"]) * 10,
                                "X2": int(round(RefX - Entity["absx"] + Ent.dxf.end[0], 0)) * 10,
                                "Y2": int(round(RefY - Entity["absy"] + Ent.dxf.end[1], 0)) * 10,
                                "Z2": int(Z) * 10 + int(Entity["Props"]["BEAM_OFFSET"]) * 10,
                                "Material":"Steel"
                            }
                            Project["_Steels"][CompId]=Steel
                            CompId+=1
                if ColumnAdded:
                    SendMessage("Success",f"Steel columns added at {(round(Entity['absx'],2), round(Entity['absy'],2))}",client)
                if BeamAdded:
                    SendMessage("Success",f"Steel beams added at {(round(Entity['absx'],2), round(Entity['absy'],2))}",client)
            else:
                SendMessage("Error",f"Count of LAYOUT_ID and TO should be equal in STEELSTR at {(round(Entity['absx'],2), round(Entity['absy'],2))}.",client)
                return None
    else:
        SendMessage("Warning",f"No Steel Structure added in the Project",client)

    if "LIGHT" in PKEntities:
        CompId=1
        for Entity in PKEntities["LIGHT"]:
            BName = Entity["dxf"].dxf.name
            BDef = doc.blocks[BName]
            if Entity["LAYOUT_ID"] in DXFItems["Layouts"]:
                RefX = DXFItems["Layouts"][Entity["LAYOUT_ID"]]["absx"]
                RefY = DXFItems["Layouts"][Entity["LAYOUT_ID"]]["absy"]
            else:
                SendMessage("Error",f"LAYOUT_ID {Entity['LAYOUT_ID']} is not valid in LIGHT at {(round(Entity['absx'],2), round(Entity['absy'],2))}.",client)
                return None            
            Light = {
                "Id":CompId,
                "X": int(round(Entity["absx"]-RefX, 0)) * 10,
                "Y": int(round(Entity["absy"]-RefY, 0)) * 10,
                "Z": int(Entity["Z"]) * 10,
                "Type": Entity["LIGHT_TYPE"],
                "Intensity": Entity["INTENSITY"]
            }
            Project["_Lights"][CompId]=Light
            CompId+=1
            SendMessage("Success",f"Light added at {(round(Entity['absx'],2), round(Entity['absy'],2))}.",client)
    else:
        SendMessage("Warning",f"No Light added in the Project.",client)


    if "3DOBJECT" in PKEntities:
        CompId=1
        for Entity in PKEntities["3DOBJECT"]:
            BName = Entity["dxf"].dxf.name
            BDef = doc.blocks[BName]
            if Entity["LAYOUT_ID"] in DXFItems["Layouts"]:
                RefX = DXFItems["Layouts"][Entity["LAYOUT_ID"]]["absx"]
                RefY = DXFItems["Layouts"][Entity["LAYOUT_ID"]]["absy"]
            else:
                SendMessage("Error",f"LAYOUT_ID {Entity['LAYOUT_ID']} is not valid in 3DOBJECT at {(round(Entity['absx'],2), round(Entity['absy'],2))}.",client)
                return None            
            Light = {
                "Id":CompId,
                "X": int(round(Entity["absx"]-RefX , 0)) * 10,
                "Y": int(round(Entity["absy"]-RefY, 0)) * 10,
                "Z": GetLevel(DXFItems["Layouts"][Entity["LAYOUT_ID"]]["LEVEL"], DXFItems["Levels"]) * 10,
                "Angle":Entity["Angle"],
                "Name": Entity["OBJECT_NAME"],
                "Scale": Entity["SCALE"]
            }
            Project["_3DObjects"][CompId]=Light
            CompId+=1
            SendMessage("Success",f"3D Object {Entity['OBJECT_NAME']} added at {(round(Entity['absx'],2), round(Entity['absy'],2))}.",client)
    else:
        SendMessage("Warning",f"No Custom 3d Object added in the Project.",client)

    if "BLOCK" in PKEntities:
        CompId=1
        for Entity in PKEntities["BLOCK"]:
            BName = Entity["dxf"].dxf.name
            BDef = doc.blocks[BName]
            Lyts = Entity["Props"]["LAYOUT_ID"].split(",") if Entity["Props"]["LAYOUT_ID"] else []
            Offsets = Entity["Props"]["OFFSET"].split(",") if Entity["Props"]["OFFSET"] else []
            Thicknesses = Entity["Props"]["THICKNESS"].split(",") if Entity["Props"]["THICKNESS"] else []


            if Lyts[0] in DXFItems["Layouts"]:
                RefX = DXFItems["Layouts"][Lyts[0]]["absx"]
                RefY = DXFItems["Layouts"][Lyts[0]]["absy"]
            else:
                SendMessage("Error",f"LAYOUT_ID {Lyts[0]} is not valid in BLOCK at {(round(Entity['absx'],2), round(Entity['absy'],2))}.",client)
                return None

            if len(Offsets)!=len(Lyts):
                if len(Offsets)==1:
                    Offsets=Offsets*len(Lyts)
                else:
                    SendMessage("Error",f"Count of OFFSET should be equal to count of LAYOUT_ID or (1) in BLOCK at {(round(Entity['absx'],2), round(Entity['absy'],2))}",client)
                    return None

            if len(Thicknesses)!=len(Lyts):
                if len(Thicknesses)==1:
                    Thicknesses=Thicknesses*len(Lyts)
                else:
                    SendMessage("Error",f"Count of THICKESS should be equal to count of LAYOUT_ID or (1) in BLOCK at {(round(Entity['absx'],2), round(Entity['absy'],2))}",client)
                    return None

            i=0
            for ly in Lyts:
                if int(Thicknesses[i]) > 0:
                    blc = int(Thicknesses[i]) * 10
                else:
                    blc = 0

                Block = {
                    "Id":CompId,
                    "X": int(round(RefX - Entity["absx"], 0)) * 10,
                    "Y": int(round(RefY - Entity["absy"], 0)) * 10,
                    "Z": GetLevel(DXFItems["Layouts"][ly]["LEVEL"], DXFItems["Levels"]) * 10 + int(Offsets[i]) * 10 + blc,
                    "Thickness": abs(int(Thicknesses[i])) * 10,
                    "Material": str(Entity["Color"][0])+','+ str(Entity["Color"][1])+','+str(Entity["Color"][2])+','+ Entity["Props"]["OPACITY"],
                    "Name": Entity["Props"]["NAME"],
                    "GroupName":Entity["Props"]["GROUP"],
                    "Vertices": [],
                    "Holes": [],
                }
                for Poly in BDef:
                    Polis = []
                    Hole = []
                    if Poly.dxftype() == "LWPOLYLINE" or Poly.dxftype() == "POLYLINE":
                        if Poly.dxf.color == 3:
                            Pnts=Segmentify(Poly,client,10)
                            for pnt in Pnts:
                                Polis.append({"x": round(pnt[0], 3) * 10-Block["X"], "y": round(pnt[1], 3) * 10-Block["Y"], "z": Block["Z"]})
                            
                            if EncodeCompType(Entity["Props"])["PVar"]=="MULTI": 
                                Block["Vertices"].append(Polis)
                            else:
                                Block["Vertices"]=[Polis]
                        if EncodeCompType(Entity["Props"])["PVar"]=="HOLE":
                            if Poly.dxf.color == 1:
                                Pnts=Segmentify(Poly,client,10)
                                for pnt in Pnts:
                                    Hole.append({"x": round(pnt[0], 3) * 10-Block["X"], "y": round(pnt[1], 3) * 10-Block["Y"], "z": Block["Z"]})
                                Block["Holes"].append(Hole)
                if Block["Vertices"]:
                    Project["_PolyParts"][CompId]=Block
                    SendMessage("Success",f"Block {Entity['Props']['NAME']} added at {(round(Entity['absx'],2), round(Entity['absy'],2))}",client)
                    CompId+=1
                else:
                    SendMessage("Warning",f"Ignored block! There was no valid polylines in BLOCK at {(round(Entity['absx'],2), round(Entity['absy'],2))}.",client)
                i+=1
    else:
        SendMessage("Warning",f"No BLOCK added in the Project.",client)
            

    if "WALL" in PKEntities:
        CompId=1
        for Entity in PKEntities["WALL"]:
            BName = Entity["dxf"].dxf.name
            BDef = doc.blocks[BName]
            if Entity["Props"]["LAYOUT_ID"] in DXFItems["Layouts"]:
                RefX = DXFItems["Layouts"][Entity["Props"]["LAYOUT_ID"]]["absx"]
                RefY = DXFItems["Layouts"][Entity["Props"]["LAYOUT_ID"]]["absy"]
            else:
                SendMessage("Error",f"LAYOUT_ID {Entity['Props']['LAYOUT_ID']} is not valid in WALL at {(round(Entity['absx'],2), round(Entity['absy'],2))}.",client)
                return None            
            Wall = {
                "Id":CompId,
                "X": int(round(RefX - Entity["absx"], 0)) * 10,
                "Y": int(round(RefY - Entity["absy"], 0)) * 10,
                "Z": GetLevel(DXFItems["Layouts"][Entity["Props"]["LAYOUT_ID"]]["LEVEL"], DXFItems["Levels"]) * 10,
                "Thickness": abs(int(Entity["Props"]["WALL_THICKNESS"])) * 10,
                "Material": str(Entity["Color"][0])+','+ str(Entity["Color"][1])+','+str(Entity["Color"][2])+','+ Entity["Props"]["OPACITY"],
                "GroupName": Entity["Props"]["GROUP"],
                "Height": abs(int(Entity["Props"]["HEIGHT"]))*10,
                "Polyline": [],
            }
            for Poly in BDef:
                Polis = []
                Hole = []
                if Poly.dxftype() == "LWPOLYLINE" or Poly.dxftype() == "POLYLINE":
                    for pnt in Poly:
                        Polis.append({"x": round(pnt[0], 3) * 10-Wall["X"], "y": round(pnt[1], 3) * 10-Wall["Y"], "z": Wall["Z"]})
                    Wall["Polyline"].append(Polis)
            if Wall["Polyline"]:
                Project["_PolyWalls"][CompId]=Wall
                SendMessage("Success",f"Wall added at {(round(Entity['absx'],2), round(Entity['absy'],2))}",client)
                CompId+=1
            else:
                SendMessage("Warning",f"Ignored block! There was no valid polylines in WALL at {(round(Entity['absx'],2), round(Entity['absy'],2))}.",client)
    else:
        SendMessage("Warning",f"No WALL added in the Project.",client)


    if "SHELF" in PKEntities:
        ShelfEnts = [Entity for Entity in PKEntities["SHELF"] if EncodeCompType(Entity)["Dir"] == "TOP"]
        NewShelfEnts = []
        for Shelf in ShelfEnts:
            Shelf["CAPACITY"] = GetShelfCapacity(Shelf["dxf"])            
            if "NFP" in EncodeCompType(Shelf)["PVar"]:
                Shelf["CAPACITY"] -= 1
            LayIds = Shelf["LAYOUT_ID"].split(",") if Shelf["LAYOUT_ID"] else []
            CarrIds = Shelf["CARRIER_ID"].split(",") if Shelf["CARRIER_ID"] else []
            if LayIds:
                if CarrIds:
                    if len(CarrIds) == 1:
                        CarrIds = [CarrIds[0]] * len(LayIds)

                    if len(CarrIds) == len(LayIds):
                        for ind in range(len(LayIds)):
                            Ent1 = {}
                            for e in Shelf:
                                Ent1[e] = Shelf[e]
                            Ent1["LAYOUT_ID"] = LayIds[ind]
                            Ent1["CARRIER_ID"] = CarrIds[ind]
                            if LayIds[ind] not in DXFItems["Layouts"]:
                                SendMessage("Error",f"LAYOUT_ID is not valid in Shelf at {(round(Shelf['absx'],2), round(Shelf['absy'],2))}",client)
                                return None
                            NewShelfEnts.append(Ent1)
                            SendMessage("Success",f"SHELF added at {(round(Shelf['absx'],2), round(Shelf['absy'],2))}",client)
                            Project["Systems"][Shelf["SYSTEM_ID"]] = {"Id": Shelf["SYSTEM_ID"], "OPCActive": False, "AutoDoNext": False}
                    else:
                        SendMessage("Error",f"Count of CARRIER_ID should be equal to count of LAYOUT_ID or (1) in SHELF at {(round(Shelf['absx'],2), round(Shelf['absy'],2))}",client)
                        return None
                else:
                    SendMessage("Error",f"CARRIER_ID should not be empty in SHELF at {(round(Shelf['absx'],2), round(Shelf['absy'],2))}",client)
                    return None
            else:
                SendMessage("Error",f"LAYOUT_ID should not be empty in SHELF at {(round(Shelf['absx'],2), round(Shelf['absy'],2))}",client)
                return None
        PKEntities["SHELF"] = NewShelfEnts
        SendMessage("Success",f"SHELF added at {(round(Shelf['absx'],2), round(Shelf['absy'],2))}",client)
    else:
        SendMessage("Warning",f"No SHELF added in the Project.",client)

    CarrList=[]
    ShuttleTypes = ["SHUTTLE", "SHUTTLETT"]
    for SType in ShuttleTypes:
        NewShuttleEnts = []
        if SType in PKEntities:
            ShuttleEnts = [Entity for Entity in (PKEntities[SType]) if EncodeCompType(Entity)["Dir"] == "TOP"]
            for Shuttle in ShuttleEnts:
                LayIds = Shuttle["LAYOUT_ID"].split(",") if Shuttle["LAYOUT_ID"] else []
                CarrIds = Shuttle["CARRIER_ID"].split(",") if Shuttle["CARRIER_ID"] else []
                CarrList+=CarrIds
                if LayIds:
                    if CarrIds:
                        if len(CarrIds) == len(LayIds):
                            for ind in range(len(LayIds)):
                                Ent1 = {}
                                for e in Shuttle:
                                    Ent1[e] = Shuttle[e]
                                Ent1["LAYOUT_ID"] = LayIds[ind]
                                Ent1["CARRIER_ID"] = CarrIds[ind]
                                if LayIds[ind] not in DXFItems["Layouts"]:
                                    SendMessage("Error",f"LAYOUT_ID is not valid in {SType} at {(round(Shuttle['absx'],2), round(Shuttle['absy'],2))}",client)
                                    return None
                                NewShuttleEnts.append(Ent1)
                                SendMessage("Success",f"{SType} added at {(round(Shuttle['absx'],2), round(Shuttle['absy'],2))}",client)
                                Project["Systems"][Shuttle["SYSTEM_ID"]] = {"Id": Shuttle["SYSTEM_ID"], "OPCActive": False, "AutoDoNext": False}
                        else:
                            SendMessage("Error",f"Count of CARRIER_ID should be equal to count of LAYOUT_ID or (1) in {SType} at {(round(Shuttle['absx'],2), round(Shuttle['absy'],2))}",client)
                            return None
                    else:
                        SendMessage("Error",f"CARRIER_ID should not be empty in {SType} at {(round(Shuttle['absx'],2), round(Shuttle['absy'],2))}",client)
                        return None
                else:
                    SendMessage("Error",f"LAYOUT_ID should not be empty in {SType} at {(round(Shuttle['absx'],2), round(Shuttle['absy'],2))}",client)
                    return None
        else:
            SendMessage("Warning",f"No {SType} added in the Project.",client)
        PKEntities[SType] = NewShuttleEnts

    LiftTypes = ["ELIFT", "ELIFTTT", "ELIFTUG", "LIFTSHUTTLETT"]
    for LType in LiftTypes:
        NewLiftEnts = {}
        if LType in PKEntities:
            LiftEnts = [Entity for Entity in (PKEntities[LType]) if EncodeCompType(Entity)["Dir"] == "TOP"]
            for Lift in LiftEnts:
                LayIds = Lift["LAYOUT_ID"].split(",") if Lift["LAYOUT_ID"] else []
                CarrIds = Lift["CARRIER_ID"].split(",") if Lift["CARRIER_ID"] else []
                CarrList+=CarrIds
                if len(CarrIds) == 1: 
                    if len(LayIds) >= 1:
                        if CarrIds[0] not in NewLiftEnts:
                            Ent1 = {}
                            for e in Lift:
                                Ent1[e] = Lift[e]
                            Ent1["LAYOUT_ID"] = LayIds
                            Ent1["CARRIER_ID"] = CarrIds[0]
                            # if LayIds[ind] not in DXFItems["Layouts"]:
                            #     SendMessage("Error",f"LAYOUT_ID is not valid in {LType} at {(round(Lift['absx'],2), round(Lift['absy'],2))}")
                            #     return None
                            NewLiftEnts[CarrIds[0]]=Ent1
                        else:
                            NewLiftEnts[CarrIds[0]]["LAYOUT_ID"]+=LayIds
                        Project["Systems"][Lift["SYSTEM_ID"]] = {"Id": Lift["SYSTEM_ID"], "OPCActive": False, "AutoDoNext": False}
                    else:
                        SendMessage("Error",f"There should be only at least one LAYOUT_ID in {LType} at {(round(Shuttle['absx'],2), round(Shuttle['absy'],2))}",client)
                        return None
                else:
                    SendMessage("Error",f"There should be only one CARRIER_ID in {LType} at {(round(Shuttle['absx'],2), round(Shuttle['absy'],2))}",client)
                    return None
        else:
            SendMessage("Warning",f"No {LType} added in the Project.",client)
        PKEntities[LType] = [nl for nl in NewLiftEnts.values()] 

    NewRoomEnts = []
    if "ROOM" in PKEntities:
        RoomEnts = [Entity for Entity in (PKEntities["ROOM"]) if EncodeCompType(Entity)["Dir"] == "TOP"]
        for Room in RoomEnts:
            LayIds = Room["LAYOUT_ID"].split(",") if Room["LAYOUT_ID"] else []
            CarrIds = Room["CARRIER_ID"].split(",") if Room["CARRIER_ID"] else []
            if len(CarrIds) == 1:
                if len(LayIds) == 1:
                    if CarrIds[0] not in CarrList:
                        SendMessage("Error",f"CARRIER_ID is not valid in ROOM at {(round(Lift['absx'],2), round(Lift['absy'],2))}",client)
                        return None
                    if LayIds[0] not in DXFItems["Layouts"]:
                        SendMessage("Error",f"LAYOUT_ID is not valid in ROOM at {(round(Lift['absx'],2), round(Lift['absy'],2))}",client)
                        return None
                    if not [nr for nr in NewRoomEnts if nr["CARRIER_ID"] == CarrIds[0]]:
                        NewRoomEnts.append(Room)
                        Project["Systems"][Room["SYSTEM_ID"]] = {"Id": Room["SYSTEM_ID"], "OPCActive": False, "AutoDoNext": False}
                else:
                    SendMessage("Error",f"There should be one LAYOUT_ID in ROOM at {(round(Shuttle['absx'],2), round(Shuttle['absy'],2))}",client)
                    return None
            else:
                SendMessage("Error",f"There should be one CARRIER_ID in ROOM at {(round(Shuttle['absx'],2), round(Shuttle['absy'],2))}",client)
                return None
    else:
        SendMessage("Warning",f"No ROOM added in the Project.",client)
    PKEntities["ROOM"] = NewRoomEnts

    for Section in PKEntities:
        if Section in ShuttleTypes or Section in LiftTypes:
            for Entity in PKEntities[Section]:
                CarrObjects[int(Entity["CARRIER_ID"])] = Entity
        if Section == "SHELF":
            for Entity in PKEntities[Section]:
                if int(Entity["CARRIER_ID"]) in ShelfObjects:
                    ShelfObjects[int(Entity["CARRIER_ID"])].append(Entity)
                else:
                    ShelfObjects[int(Entity["CARRIER_ID"])] = [Entity]
        elif Section == "ROOM":
            for Entity in PKEntities[Section]:
                RoomObjects.append(Entity)

    # region Carrier Objelerden Sistem Nesneleri oluştur

    CarrId = RoomId = ConvId = 1
    for Carr in CarrObjects.values():
        if Carr["CON_CARS"]:
            Conn = Carr["CON_CARS"].split(",")
            for c in Conn:
                if c not in CarrList:
                    SendMessage("Error",f"CON_CARS {c} is not valid in {EncodeCompType(Carr)['Base']} at {(round(Carr['absx'],2), round(Carr['absy'],2))}",client)
                    return None
            Conns = [{"Obj1": int(Carr["CARRIER_ID"]), "Obj2": int(c), "Conv1": None, "Conv2": None, "Car1": None, "Car2": None} for c in Conn]
            for cn in Conns:
                CheckCon = [c for c in DXFItems["Connections"] if (c["Obj1"] == cn["Obj1"] and c["Obj2"] == cn["Obj2"]) or (c["Obj2"] == cn["Obj1"] and c["Obj1"] == cn["Obj2"])]
                if not CheckCon:
                    DXFItems["Connections"].append(cn)

    for Carr in CarrObjects.values():
        if int(Carr["CARRIER_ID"]) in ShelfObjects:
            CarrShelves = ShelfObjects[int(Carr["CARRIER_ID"])]
        else:
            CarrShelves = []
        ShelfId = 1
        for s in CarrShelves:
            Project["Shelves"][ConvId * 100 + ShelfId] = CreateShelf(ShelfId, s, ConvId, Carr, DXFItems)
            ShelfId += 1
        for r in RoomObjects:
            if r["CARRIER_ID"] == Carr["CARRIER_ID"]:
                if r["LAYOUT_ID"] not in Carr["LAYOUT_ID"]:
                    Carr["LAYOUT_ID"].append(r["LAYOUT_ID"])
                if RoomId not in Project["Rooms"]:
                    Project["Rooms"][RoomId] = CreateRoom(RoomId, r, ConvId, DXFItems)
                    RoomId += 1
        
        BaseCarrId=CarrId
        if EncodeCompType(Carr)["Base"] == "ELIFT" or EncodeCompType(Carr)["Base"] == "ELIFTUG":
            Product = "ELU" if EncodeCompType(Carr)["Base"] == "ELIFTUG" else "EL"
            Project["Carriers"][CarrId] = CreateLift(CarrId, Carr, DXFItems,Product)
            Project["Conveyors"][ConvId] = CreateConveyor(ConvId, Carr, CarrId,DXFItems)
            Project["Carriers"][CarrId]["TopConvId"] = ConvId
        elif EncodeCompType(Carr)["Base"] == "ELIFTTT":
            Project["Carriers"][CarrId] = CreateLift(CarrId, Carr, DXFItems,"ELTT")
            CarrId += 1
            Project["Carriers"][CarrId] = CreateTurntable(CarrId, Carr, DXFItems,"ETT4L")
            Project["Carriers"][CarrId]["ParentId"] = CarrId - 1
            Project["Conveyors"][ConvId] = CreateConveyor(ConvId, Carr, CarrId, DXFItems)
            Project["Carriers"][CarrId]["TopConvId"] = ConvId
            Project["Carriers"][CarrId - 1]["TopConvId"] = ConvId
        if EncodeCompType(Carr)["Base"] == "SHUTTLE":
            Project["Carriers"][CarrId] = CreateShuttle(CarrId, Carr, DXFItems,"ES")
            Project["Conveyors"][ConvId] = CreateConveyor(ConvId, Carr, CarrId, DXFItems)
            Project["Carriers"][CarrId]["TopConvId"] = ConvId
        elif EncodeCompType(Carr)["Base"] == "SHUTTLETT":
            Project["Carriers"][CarrId] = CreateShuttle(CarrId, Carr, DXFItems)
            Project["Carriers"][CarrId]["Product"] = "ESTT"
            CarrId += 1
            Project["Carriers"][CarrId] = CreateTurntable(CarrId, Carr, DXFItems)
            Project["Carriers"][CarrId]["Product"] = "ETT4S"
            Project["Carriers"][CarrId]["ParentId"] = CarrId - 1
            Project["Conveyors"][ConvId] = CreateConveyor(ConvId, Carr, CarrId, DXFItems)
            Project["Carriers"][CarrId]["TopConvId"] = ConvId
            Project["Carriers"][CarrId - 1]["TopConvId"] = ConvId
        elif EncodeCompType(Carr)["Base"] == "LIFTSHUTTLE":
            Product="ELS"+EncodeCompType(Carr)["PVar"] #ELS2 or ELS3 
            Project["Carriers"][CarrId] = CreateLift(CarrId, Carr, DXFItems, Product)
            CarrId += 1
            Project["Carriers"][CarrId] = CreateShuttle(CarrId, Carr, DXFItems,"ES4LS")
            Project["Carriers"][CarrId]["ParentId"] = CarrId - 1
            Project["Conveyors"][ConvId] = CreateConveyor(ConvId, Carr, CarrId, DXFItems)
            Project["Carriers"][CarrId]["TopConvId"] = ConvId
            Project["Carriers"][CarrId - 1]["TopConvId"] = ConvId
        elif EncodeCompType(Carr)["Base"] == "LIFTSHUTTLETT":
            Product="ELST"+EncodeCompType(Carr)["PVar"] #ELST2 or ELST3 
            Project["Carriers"][CarrId] = CreateLift(CarrId, Carr, DXFItems,Product)
            CarrId += 1
            Project["Carriers"][CarrId] = CreateShuttle(CarrId, Carr, DXFItems,"ES4LST")
            Project["Carriers"][CarrId]["ParentId"] = CarrId - 1
            CarrId += 1
            Project["Carriers"][CarrId] = CreateTurntable(CarrId, Carr, DXFItems,"ETT4LST")
            Project["Carriers"][CarrId]["ParentId"] = CarrId - 1
            Project["Conveyors"][ConvId] = CreateConveyor(ConvId, Carr, CarrId, DXFItems)
            Project["Carriers"][CarrId]["TopConvId"] = ConvId
            Project["Carriers"][CarrId - 1]["TopConvId"] = ConvId
            Project["Carriers"][CarrId - 2]["TopConvId"] = ConvId
        UpdateConnection(Carr, Project["Carriers"][BaseCarrId], Project["Conveyors"][ConvId],DXFItems)
        CarrId += 1
        ConvId += 1

    # endregion

    # region Conveyor ilişkikerine göre transfer conveyörleri oluştur
    CreateTransferConveyors(DXFItems,Project)

    for Carr in Project["Carriers"].values():
        c = Carr["TopConvId"]
        p=Carr["ParentId"]
        CarrX=0 
        while p !="NULL":
            CarrX=Project["Carriers"][p]["X"]
            p=Project["Carriers"][p]["ParentId"] 
        
        for s in Project["Shelves"].values():
            if s["ConveyorId"] == c:
                if Carr["CarrierType"] == "Lift":
                    pass
                    # if s["Z"] * 10 < Carr["MinPos"]:
                    #     Carr["MinPos"] = s["Z"] * 10
                    # if s["Z"] * 10 > Carr["MaxPos"]:
                    #     Carr["MaxPos"] = s["Z"] * 10
                elif Carr["CarrierType"] == "Shuttle":
                    if (s["X"]-CarrX) * 10 < Carr["MinPos"]:
                        Carr["MinPos"] = (s["X"]-CarrX) * 10
                    if (s["X"]-CarrX)*10 > Carr["MaxPos"]:
                        Carr["MaxPos"] = (s["X"]-CarrX) * 10
        for s in Project["Rooms"].values():
            if s["ConveyorId"] == c:
                if Carr["CarrierType"] == "Lift":
                    pass
                    # if s["Z"] * 10 < Carr["MinPos"]:
                    #     Carr["MinPos"] = s["Z"] * 10
                    # if s["Z"] * 10 > Carr["MaxPos"]:
                    #     Carr["MaxPos"] = s["Z"] * 10
                elif Carr["CarrierType"] == "Shuttle":
                    if (s["X"]-Carr["X"]) * 10 < Carr["MinPos"]:
                        Carr["MinPos"] = (s["X"]-Carr["X"]) * 10
                    if (s["X"]-Carr["X"]) * 10 > Carr["MaxPos"]:
                        Carr["MaxPos"] = (s["X"]-Carr["X"]) * 10

                        
        if Carr["ParentId"] == "NULL":
            Carr["PosOffset"] = 0
        else:
            Carr["PosOffset"] = -Carr["MinPos"]
    # region Dönme Noktalarının atamasını yap

    for Carr in Project["Carriers"].values():
        del Carr["TopConvId"]
    # endregion
    
    CreatePallets(Project)
    FormatProjectForDB(Project)
    return Project

# DXFSystem2("PK24Sablons1Deneme2.dxf",False)


def RestoreFromDXF(afolder, DXFFile,client):
    Project=DXFSystem2(DXFFile,client)
    if Project:
        FileSuffix=Project["Name"]+"_V"+Project["Version"]+"_"
        print(os.getcwd(), os.path.abspath(afolder + "/" + FileSuffix + "CFG.sqlite"))
        import shutil


        CopiedDXF="static//dxf_files//" + FileSuffix + ".dxf"
        shutil.copyfile(DXFFile, CopiedDXF)
        shutil.copyfile(afolder + "//BaseCFG.sqlite", afolder + "//" + FileSuffix + "CFG.sqlite")
        # shutil.copyfile(afolder + "/BasePallets.sqlite", afolder + "/" + FileSuffix + "Pallets.sqlite")
        SendMessage("Info", "Creating CFG DB files...",client)

        DBFile=afolder + "//" + FileSuffix + "CFG.sqlite"
        dbShortFile="static//db//"+FileSuffix + "CFG.sqlite"
        conn = sqlite3.connect(DBFile)
        crs = conn.cursor()
        crs.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = crs.fetchall()
        for t in tables:
            if t[0] != "Settings":
                crs.execute(f"DELETE FROM {t[0]}")
                conn.commit()
        for Part in Project:
            if isinstance(Project[Part], dict):        
                    for s in Project[Part].values():
                        sql = f"INSERT INTO {Part} ({','.join(s)}) VALUES ({','.join(s.values())})"
                        #crs.execute(sql)
                        try:
                            crs.execute(sql)
                        except Exception as e:
                            print(e, sql)
        conn.commit()

        conn = sqlite3.connect(afolder + "//..//Projects.sqlite")
        crs = conn.cursor()

        sql =f'insert or replace into Projects (Code, Version, Name, DB, DXF, UpdateTime) values ("{Project["Code"]}","{Project["Version"]}","{Project["Name"]}","{dbShortFile}","{CopiedDXF}","{datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}")'
        crs.execute(sql)
        conn.commit()
        conn.close()        
        SendMessage("Primary", f"All done! {DXFFile} analyzed and {FileSuffix}CFG.sqlite created",client)
        path = afolder + "/" + FileSuffix
        #files = {"CFG": path + "CFG.sqlite", "Pallets": path + "Pallets.sqlite"}
        files = {"CFG": path + "CFG.sqlite"}
        RestoreFromDB(files,client)
    else:
        SendMessage("Error", f"No Project created")

def RestoreFromDB(files,client):
    Project = EmptyProject()
    if files["CFG"]:
        conn = sqlite3.connect(files["CFG"])
        crs = conn.cursor()
        crs.execute("SELECT name FROM sqlite_master WHERE type='table' AND name<>'sqlite_sequence';")
        tables = crs.fetchall()
        for t in tables:
            crs.execute("SELECT * FROM " + t[0])
            recs = crs.fetchall()
            descs = [dsc[0] for dsc in crs.description]
            for r in recs:
                i = 0
                line = {}
                for d in descs:
                    line[d] = r[i]
                    i += 1
                if t[0]=="Settings":
                    Key=line["Key"]
                else:
                    Key=line["Id"]
                Project[t[0]][Key]=line
    # if files["Pallets"]:
    #     conn = sqlite3.connect(files["Pallets"])
    #     crs = conn.cursor()
    #     crs.execute("SELECT * FROM Pallets")
    #     recs = crs.fetchall()
    #     descs = [dsc[0] for dsc in crs.description]
    #     for r in recs:
    #         i = 0
    #         line = {}
    #         for d in descs:
    #             line[d] = r[i]
    #             i += 1
    #         Project["Pallets"][line["Id"]]=line
    conn.close()
    SendMessage("Project",Project,client)

def ReadFromDB(path):
    files = {"CFG": path + "CFG.sqlite", "Pallets": path + "Pallets.sqlite"}
    RestoreFromDB(files)

def Segmentify(polyline, client, segmentl=10):
    vertices = polyline.get_points()
    is_closed = polyline.closed
    if is_closed:
        vertices.append(vertices[0])
    allp = []
    for i in range(len(vertices) - 1):
        start = vertices[i][:2]
        end = vertices[i + 1][:2]
        bulge = vertices[i][4] if len(vertices[i]) >= 5 else 0
        allp.append(start)
        if bulge != 0:  # Line
            center, start_angle, end_angle, radius = ezdxf.math.bulge_to_arc(
                start, end, bulge
            )
            total_angle = end_angle - start_angle
            if total_angle <= 0:
                total_angle += 2 * math.pi
            num_segments = int(total_angle * radius / segmentl)
            segment_angle = total_angle / num_segments if num_segments>0 else total_angle
            arc_points = [
                (
                    center[0] + radius * math.cos(start_angle + i * segment_angle),
                    center[1] + radius * math.sin(start_angle + i * segment_angle),
                )
                for i in range(num_segments + 1)
            ]
            prec=1000000
            if int(arc_points[-1][0]*prec) == int(start[0]*prec) and int(arc_points[-1][1]*prec) == int(start[1]*prec) :
                arc_points.reverse()
            for j in range(len(arc_points) - 1):
                allp.append(arc_points[j])
    allp.append(end)
    return allp