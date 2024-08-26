import time
import json
import websocket_server

ws = None


def CreateWs():
    return websocket_server.WebsocketServer("0.0.0.0", 9000)


def SendMessage(Command, Message, client):
    global ws
    if client:
        ws.send_message(client, json.dumps({"Command": Command, "Data": Message}))
    if Command != "Project" and Command != "ProjectList" :
        print(Command, Message)


def EmptyProject():
    return {
        "Name": "",
        "Version": "",
        "Settings": {},
        "Systems": {},
        "Carriers": {},
        "Conveyors": {},
        "Rooms": {},
        "Shelves": {},
        "ShelfGroups": {},
        "Pallets": {},
        "Doors": {},
        "PLC": {},
        "_PolyParts": {},
        "_PolyWalls": {},
        "_Steels": {},
        "_Lights": {},
        "_3DObjects": {},
        "BOM": [],
    }



def IsValidComp(Entity):
    if "COMP_TYPE" not in Entity:
        return False

    Params = Entity["COMP_TYPE"].split("-")
    if len(Params) != 6:
        return False
    Cmp = EncodeCompTypeStr(Entity["COMP_TYPE"])
    return Cmp["Lib"] == "PK24" or Cmp["Lib"] == "PKE24"


def EncodeCompType(Entity):
    return EncodeCompTypeStr(Entity["COMP_TYPE"])


def EncodeCompTypeStr(ParamStr: str):
    Params = ParamStr.split("-")
    return {
        "Base": Params[0],
        "PVar": Params[1],
        "VVar": Params[2],
        "Dir": Params[3],
        "Class": Params[4],
        "Lib": Params[5],
    }


def QT(text):
    return "'" + text + "'"


def GetLevel(Level, Levels):
    if Level[0] == "L":
        if Level in Levels:
            return Levels[Level]["Z"]
        else:
            return None
    else:
        return int(Level)


def CreateLift(CarrId, Carr, DXFItems, Product):
    if int(Carr["CARRIER_ID"]) in DXFItems["TurningPosses"]:
        TP = DXFItems["TurningPosses"][int(Carr["CARRIER_ID"])]
        TPos = (
            GetLevel(DXFItems["Layouts"][TP["LAYOUT_ID"]]["LEVEL"], DXFItems["Levels"])
            * 100
        )
    else:
        TPos = 0

    Min = 1000000
    Max = -1000000
    for ly in Carr["LAYOUT_ID"]:
        Lev = GetLevel(DXFItems["Layouts"][ly]["LEVEL"], DXFItems["Levels"]) * 100
        Min = Lev if Lev < Min else Min
        Max = Lev if Lev > Max else Max
    return {
        "SystemId": Carr["SYSTEM_ID"],
        "Id": CarrId,
        "CarrierType": "Lift",
        "X": int(
            round(Carr["absx"] - DXFItems["Layouts"][Carr["LAYOUT_ID"][0]]["absx"], 0)
        )
        * 10,
        "Y": int(
            round(Carr["absy"] - DXFItems["Layouts"][Carr["LAYOUT_ID"][0]]["absy"], 0)
        )
        * 10,
        "Z": 0,
        "Angle": int(Carr["Angle"]),
        "MinPos": Min,
        "MaxPos": Max,
        "TurningPos": TPos,
        "ParentId": "NULL",
        "Product": Product,
    }


def CreateShuttle(CarrId, Carr, DXFItems, Product):
    if int(Carr["CARRIER_ID"]) in DXFItems["TurningPosses"]:
        TP = DXFItems["TurningPosses"][int(Carr["CARRIER_ID"])]
        TPos = (
            int(round(TP["absx"] - DXFItems["Layouts"][TP["LAYOUT_ID"]]["absx"], 0))
            * 100
        )
    else:
        TPos = 0
    if Product == "ES4LST":
        XX = 0
        YY= 0
        ZZ = 0
    else:
        XX = int(round(Carr["absx"] - DXFItems["Layouts"][Carr["LAYOUT_ID"]]["absx"]))*10
        YY = int(round(Carr["absy"] - DXFItems["Layouts"][Carr["LAYOUT_ID"]]["absy"]))* 10
        ZZ = GetLevel(DXFItems["Layouts"][Carr["LAYOUT_ID"]]["LEVEL"], DXFItems["Levels"])*10
    return {
        "SystemId": Carr["SYSTEM_ID"],
        "Id": CarrId,
        "CarrierType": "Shuttle",
        "X": XX,
        "Y": YY,
        "Z": ZZ,
        "Angle": int(Carr["Angle"]),
        "MinPos": 1000000,
        "MaxPos": -1000000,
        "TurningPos": TPos,
        "ParentId": "NULL",
        "Product": Product,
    }


def CreateTurntable(CarrId, Carr, DXFItems, Product):
    return {
        "SystemId": Carr["SYSTEM_ID"],
        "Id": CarrId,
        "CarrierType": "Turntable",
        "X": 0,
        "Y": 0,
        "Z": 0,
        "Angle": 0,
        "MinPos": 0,
        "MaxPos": 36000,
        "TurningPos": 0,
        "ParentId": "NULL",
        "Product": Product,
    }


def CreateConveyor(ConvId, Carr, SelfCarr, DXFItems):
    return {
        "SystemId": Carr["SYSTEM_ID"],
        "Id": ConvId,
        "SBID": ConvId,
        "SelfCarrierId": SelfCarr,
        "CHCat": "SUV",
    }


def CreateShelf(ShelfId, Shelf, ConvId, Carr, DXFItems):
    Carry = (
        int(round(Carr["absy"] - DXFItems["Layouts"][Carr["LAYOUT_ID"][0]]["absy"], 0))
        * 10
    )
    x = (
        int(round(Shelf["absx"] - DXFItems["Layouts"][Shelf["LAYOUT_ID"]]["absx"], 0))
        * 10
    )
    y = (
        int(round(Shelf["absy"] - DXFItems["Layouts"][Shelf["LAYOUT_ID"]]["absy"], 0))
        * 10
    )
    Yon = "Left" if y > Carry else "Right"
    SType = EncodeCompType(Shelf)["PVar"]
    Cap=int(Shelf["CAPACITY"])
    if "NFP" in SType:
        ShelfType = "NoFirstPallet"
        MPos = SType[0]
        Cap=int(Shelf["CAPACITY"])-1
    else:
        ShelfType = "Standard"
        MPos = SType

    return {
        "SystemId": Shelf["SYSTEM_ID"],
        "Id": ConvId * 100 + ShelfId,
        "SBID": ConvId * 100 + ShelfId,
        "Capacity": Cap,
        "ConveyorId": ConvId,
        "X": x,
        "Y": y,
        "Z": GetLevel(
            DXFItems["Layouts"][Shelf["LAYOUT_ID"]]["LEVEL"], DXFItems["Levels"]
        )
        * 10,
        "Angle": 0,
        "Side": Yon,
        "CHCat": Shelf["CAR_TYPE"],
        "ShelfType": ShelfType,
        "MotorPos": MPos,
        "Product": "ESH" + MPos + str(Shelf["CAPACITY"]),
        "SharedShelfId": "NULL",
    }


def CreateDoors(Room):
    Door1Ang = int(Room["DOOR1_ANGLE"]) + int(Room["Angle"])
    Door2Ang = int(Room["DOOR2_ANGLE"]) + int(Room["Angle"])
    Door = {
        "RoomId": str(Room["Id"]),
        "Id": str(Room["Id"] * 10 + 1),
        "Angle": str(Door1Ang),
        "Pos1": str(Door1Ang * 100),
        "Pos2": str(((Door1Ang - 180)) * 100),
    }
    Doors = [Door]
    if int(Room["DOOR_COUNT"]) == 2:
        Door = {
            "RoomId": str(Room["Id"]),
            "Id": str(Room["Id"] * 10 + 1),
            "Angle": str(Door2Ang),
            "Pos1": str(Door2Ang * 100),
            "Pos2": str(((Door2Ang - 180)) * 100),
        }
        Doors.append(Door)

    return Doors


def CreateRoom(RoomId, Room, ConvId, DXFItems):
    return {
        "SystemId": Room["SYSTEM_ID"],
        "Id": RoomId,
        "X": int(
            round(Room["absx"] - DXFItems["Layouts"][Room["LAYOUT_ID"]]["absx"], 0)
        )
        * 10,
        "Y": int(
            round(Room["absy"] - DXFItems["Layouts"][Room["LAYOUT_ID"]]["absy"], 0)
        )
        * 10,
        "Z": GetLevel(
            DXFItems["Layouts"][Room["LAYOUT_ID"]]["LEVEL"], DXFItems["Levels"]
        )
        * 10,
        "Angle": 0,
        "RoomType": Room["ROOM_TYPE"],
        "ConveyorId": ConvId,
    }


def UpdateConnection(Obj, Carr, Conv, DXFItems):
    for c in DXFItems["Connections"]:
        if c["Obj1"] == int(Obj["CARRIER_ID"]):
            c["Car1"] = Carr
            c["Conv1"] = Conv
        elif c["Obj2"] == int(Obj["CARRIER_ID"]):
            c["Car2"] = Carr
            c["Conv2"] = Conv


def InTheBox(e, DXFItems):
    sonuc = False
    for r in DXFItems["Regions"]:
        sonuc = sonuc or (
            r["xmin"] < e["absx"]
            and r["xmax"] > e["absx"]
            and r["ymin"] < e["absy"]
            and r["ymax"] > e["absy"]
        )
    return sonuc


def FormatProjectForDB(Project):
    for a in Project["Systems"].values():
        for key in a:
            a[key] = str(a[key])
        a["Name"] = QT("System " + a["Id"])
        a["OPCActive"] = QT(a["OPCActive"])
        a["AutoDoNext"] = QT(a["AutoDoNext"])
        Project["PLC"][a["Id"]] = {
            "Id": a["Id"],
            "SystemId": a["Id"],
            "IP": QT("192.168.20.11"),
            "OPCPath": QT("ns=4;s=|var|c300.Application"),
            "DriveCount": "3",
            "SafetyNVLIndex": "1",
        }
    for a in Project["Carriers"].values():
        for key in a:
            a[key] = str(a[key])
        a["Name"] = QT(a["CarrierType"] + " " + a["Id"])
        a["PLCId"] = a["SystemId"]
        a["OPCNode"] = QT(a["CarrierType"] + "_Control.F" + a["CarrierType"])
        a["DriveInd"] = "1"
        a["DriveAddr"] = "1001"
        a["ParamInd"] = "0"
        a["SafetyNVLInd"] = a["Id"]
        a["PositioningType"] = QT("AbsolutePos")
        a["Margin"] = "50"
        if a["CarrierType"] == "Lift":
            a["DistanceRatio"] = "12.61"
            a["PosScale"] = "10"
        elif a["CarrierType"] == "Turntable":
            a["DistanceRatio"] = "6.91"
            a["TurningPos"] = "0"
            a["PosScale"] = "100"
        elif a["CarrierType"] == "Shuttle":
            a["DistanceRatio"] = "47.67"
            a["PosScale"] = "10"
        a["MaxSpeedPct"] = "100"
        a["AppDistCfg"] = "1500"
        a["RefR"] = "2500"
        a["MaxR"] = "2500"
        a["RApp"] = "150"
        a["ACCTime"] = "40"
        a["DECTime"] = "40"
        a["CalcPosTolerance"] = "400"
        a["XTolerance"] = "40"
        a["Product"] = QT(a["Product"])
        a["CarrierType"] = QT(a["CarrierType"])
    for a in Project["Conveyors"].values():
        Project["ShelfGroups"][a["Id"]] = {
            "Id": str(a["Id"]),
            "SystemId": str(a["SystemId"]),
            "Name": QT("ShelfGroup " + str(a["Id"])),
            "PLCId": str(a["SystemId"]),
            "OPCNode": QT("Shelf_Control.FGroup"),
            "DriveInd": "1",
            "DriveAddr": "1001",
            "SafetyNVLInd": str(a["Id"]),
        }
        for key in a:
            a[key] = str(a[key])
        a["Name"] = QT("Conveyor " + a["Id"])
        a["ConveyorType"] = QT("Type1")
        a["CHCat"] = QT(a["CHCat"])
        a["PLCId"] = a["SystemId"]
        a["OPCNode"] = QT("Conveyor_Control.FConveyor")
        a["DriveInd"] = "1"
        a["DriveAddr"] = "1001"
        a["ParamInd"] = "0"
        a["SafetyNVLInd"] = a["Id"]
        a["ShelfGroupId"] = a["Id"]
        a["TakeACC"] = "15"
        a["TakeDEC"] = "38"
        a["TakeSpeed"] = "1300"
        a["GiveACC"] = "15"
        a["GiveDEC"] = "10"
        a["GiveSpeed"] = "1600"
        a["PalletWeight"] = "550"
        a["MaxCarWeight"] = "2500"
    for a in Project["Rooms"].values():
        for key in a:
            a[key] = str(a[key])
        a["RoomType"] = QT(a["RoomType"])
        a["Name"] = QT("Room " + a["Id"])
        a["PLCId"] = a["SystemId"]
        a["OPCNode"] = QT("Room_Control.FRoom")
        a["SafetyNVLInd"] = a["Id"]
        a["FlapDriveInd"] = "1"
        a["FlapParamInd"] = "1"
        a["FlapDriveAddr"] = "1001"
        a["CanEnter"] = QT("True")
        a["CanExit"] = QT("True")
        a["HasPedestrianDoor"] = QT("True")
        a["CardReaderIP"] = QT("192.168.20.121")
        a["LPRIP"] = QT("192.168.20.141")
        a["WallTop"] = "0"
        a["WallBottom"] = "0"
        a["LiftPos"] = str(float(a["Z"]) * 10)
        a["ShuttlePos"] = str(float(a["X"]) * 10)
        a["TTPos1"] = "0"
        a["TTPos2"] = "0"
        a["Margin"] = "50"
    for a in Project["Shelves"].values():
        for key in a:
            a[key] = str(a[key])
        a["ShelfType"] = QT(a["ShelfType"])
        a["Side"] = QT(a["Side"])
        a["CHCat"] = QT(a["CHCat"])
        if a["MotorPos"] == "":
            a["MotorPos"] = "NULL"
        else:
            a["MotorPos"] = QT(a["MotorPos"])
        a["Name"] = QT("Shelf " + a["Id"])
        a["GroupId"] = a["ConveyorId"]
        a["GroupIndex"] = "0"
        a["ParamInd"] = "0"
        a["Enabled"] = QT("True")
        a["RunTimeId"] = "1"
        a["LiftPos"] = str(float(a["Z"]) * 10)
        a["ShuttlePos"] = str(float(a["X"]) * 10)
        a["TTPos1"] = "0"
        a["TTPos2"] = "0"
        a["HasLock"] = QT("True")
        a["Product"] = QT(a["Product"])
        a["OppositeShelfId"] = "NULL"
    # for a in Doors:
    #     a["Angle"]=str(int(a["Angle"])-int(int(Project["Rooms"][int(a["RoomId"])]["Angle"])))

    for a in Project["Pallets"].values():
        for key in a:
            a[key] = str(a[key])
        a["Name"] = QT("Pallet " + a["Id"])
        a["Direction"] = QT(a["Direction"])
        a["CHCat"] = QT(a["CHCat"])
        a["RequestType"] = QT("NoRequest")
        a["Product"] = QT(a["Product"])

    for a in Project["_PolyParts"].values():
        for key in a:
            if key != "Vertices" and key != "Holes":
                a[key] = str(a[key])
        a["Material"] = QT(a["Material"])
        a["Name"] = QT(a["Name"])
        a["GroupName"] = QT(a["GroupName"])
        a["Vertices"] = QT(json.dumps(a["Vertices"]))
        a["Holes"] = QT(json.dumps(a["Holes"]))

    for a in Project["_PolyWalls"].values():
        for key in a:
            if key != "Polyline":
                a[key] = str(a[key])
        a["GroupName"] = QT(a["GroupName"])
        a["Material"] = QT(a["Material"])
        a["Polyline"] = QT(json.dumps(a["Polyline"]))

    for a in Project["_Steels"].values():
        for key in a:
            a[key] = str(a[key])
        a["Material"] = QT(a["Material"])
        a["Type"] = QT(a["Type"])

    for a in Project["_Lights"].values():
        for key in a:
            a[key] = str(a[key])
        a["Type"] = QT(a["Type"])

    for a in Project["_3DObjects"].values():
        for key in a:
            a[key] = str(a[key])
        a["Name"] = QT(a["Name"])


def CreateTransferConveyors(DXFItems, Project):
    for Con in DXFItems["Connections"]:
        cl = None
        cs = None
        if (
            Con["Car1"] is not None
            and Con["Car2"] is not None
            and Con["Conv1"] is not None
            and Con["Conv2"] is not None
        ):
            if Con["Car1"]["CarrierType"] == "Lift":
                if Con["Car2"]["CarrierType"] == "Shuttle":
                    cl = Con["Car1"]
                    cs = Con["Car2"]
                    conl = Con["Conv1"]
                    cons = Con["Conv2"]
            if Con["Car1"]["CarrierType"] == "Shuttle":
                if Con["Car2"]["CarrierType"] == "Lift":
                    cs = Con["Car1"]
                    cl = Con["Car2"]
                    cons = Con["Conv1"]
                    conl = Con["Conv2"]
            if cl and cs:
                if abs(cl["Y"] - cs["Y"]) < 4800:
                    ShelfType = "Conveyor"
                    BOMName = "Transfer Roller"
                else:
                    ShelfType = "Transfer"
                    BOMName = "Transfer Shelf"
                for b in Project["BOM"]:
                    if b[0] == BOMName and b[1] == int(
                        round(abs(cl["Y"] - cs["Y"]) - 2400) / 10
                    ):
                        b[2] += 1
                        break
                else:
                    Project["BOM"].append(
                        [BOMName, (int(round(abs(cl["Y"] - cs["Y"]) - 2400) / 10)), 1]
                    )
                MaxId = max([ss["Id"] for ss in Project["Shelves"].values()])
                if ShelfType == "Conveyor":
                    ShelfOnLift = {
                        "SystemId": cons["SystemId"],
                        "Id": MaxId + 1,
                        "SBID": conl["Id"],
                        "Capacity": 1,
                        "ConveyorId": cons["Id"],
                        "X": cl["X"],
                        "Y": cl["Y"],
                        "Z": cs["Z"],
                        "Angle": 0,
                        "Side": "Left" if cl["Y"] > cs["Y"] else "Right",
                        "CHCat": conl["CHCat"],
                        "MotorPos": "",
                        "SharedShelfId": "NULL",
                        "Product": "ECS",  # Enine Conv Shelf
                        "ShelfType": ShelfType,
                    }
                    ShelfOnShuttle = {
                        "SystemId": conl["SystemId"],
                        "Id": MaxId + 2,
                        "SBID": cons["Id"],
                        "Capacity": 1,
                        "ConveyorId": conl["Id"],
                        "X": cl["X"],
                        "Y": cs["Y"],
                        "Z": cs["Z"],
                        "Angle": 0,
                        "Side": "Left" if cl["Y"] < cs["Y"] else "Right",
                        "CHCat": cons["CHCat"],
                        "MotorPos": "",
                        "SharedShelfId": "NULL",
                        "Product": "ECS",  # Enine Conv Shelf
                        "ShelfType": ShelfType,
                    }
                else:
                    ShelfOnLift = {
                        "SystemId": cons["SystemId"],
                        "Id": MaxId + 1,
                        "SBID": MaxId + 1,
                        "Capacity": 1,
                        "ConveyorId": cons["Id"],
                        "X": cl["X"],
                        "Y": cs["Y"] - 2300 if cs["Y"] > cl["Y"] else cs["Y"] + 2300,
                        "Z": cs["Z"],
                        "Angle": 0,
                        "Side": "Left" if cl["Y"] > cs["Y"] else "Right",
                        "CHCat": conl["CHCat"],
                        "MotorPos": "",
                        "Product": "ECS",  # Enine Conv Shelf
                        "ShelfType": ShelfType,
                    }
                    ShelfOnShuttle = {
                        "SystemId": conl["SystemId"],
                        "Id": MaxId + 2,
                        "SBID": MaxId + 2,
                        "Capacity": 1,
                        "ConveyorId": conl["Id"],
                        "X": cl["X"],
                        "Y": cl["Y"] - 2300 if cl["Y"] > cs["Y"] else cl["Y"] + 2300,
                        "Z": cs["Z"],
                        "Angle": 0,
                        "Side": "Left" if cl["Y"] < cs["Y"] else "Right",
                        "CHCat": cons["CHCat"],
                        "MotorPos": "",
                        "Product": "ECS",  # Enine Conv Shelf
                        "ShelfType": ShelfType,
                    }
                    ShelfOnLift["SharedShelfId"] = ShelfOnShuttle["Id"]
                    ShelfOnShuttle["SharedShelfId"] = ShelfOnLift["Id"]
                Project["Shelves"][ShelfOnLift["Id"]] = ShelfOnLift
                Project["Shelves"][ShelfOnShuttle["Id"]] = ShelfOnShuttle


def CreatePallets(Project):
    MaxCap = {}
    PCount = {}

    def CreatePallet(Shelf, Id, Ind):
        return {
            "SystemId": int(Shelf["SystemId"]),
            "Id": Id,
            QT("Index"): Ind,
            "SBID": Shelf["SBID"],
            "Direction": "Left",
            "CHCat": Shelf["CHCat"],
            "Product": "EP",
        }

    for s in Project["Systems"]:
        PCount[s] = 0
        MaxCap[s] = 0

    for s in Project["Shelves"].values():
        if s["CHCat"] != "EmptyPallet" and (
            s["ShelfType"] == "Standard" or s["ShelfType"] == "NoFirstPallet"
        ):
            PCount[s["SystemId"]] += s["Capacity"]
            if s["Capacity"] > MaxCap[s["SystemId"]]:
                MaxCap[s["SystemId"]] = s["Capacity"]
    ps = {}
    for s in Project["Systems"]:
        PCount[s] -= MaxCap[s] - 1
        ps[s] = 0
    # endregion

    p = 1
    for a in Project["Rooms"].values():
        if ps[a["SystemId"]] < PCount[a["SystemId"]]:
            Project["Pallets"][p] = {
                "SystemId": int(a["SystemId"]),
                "Id": p,
                QT("Index"): 0,
                "SBID": a["ConveyorId"],
                "Direction": "Left",
                "CHCat": "EmptyPallet",
                "Product": "EP",
            }
            ps[a["SystemId"]] += 1
            p += 1

    for a in Project["Shelves"].values():
        if a["ShelfType"] == "NoFirstPallet":
            if ps[a["SystemId"]] < PCount[a["SystemId"]]:
                if a["ShelfType"] != "Conveyor":
                    for i in range(a["Capacity"]):
                        Project["Pallets"][p] = CreatePallet(a, p, i)
                        ps[a["SystemId"]] += 1
                        p += 1
                        if ps[a["SystemId"]] >= PCount[a["SystemId"]]:
                            break

    for a in Project["Shelves"].values():
        if a["ShelfType"] != "NoFirstPallet":
            if a["CHCat"] == "SEDAN":
                if ps[a["SystemId"]] < PCount[a["SystemId"]]:
                    if a["ShelfType"] != "Conveyor":
                        for i in range(a["Capacity"]):
                            Project["Pallets"][p] = CreatePallet(a, p, i)
                            ps[a["SystemId"]] += 1
                            p += 1
                            if ps[a["SystemId"]] >= PCount[a["SystemId"]]:
                                break

    for a in Project["Shelves"].values():
        if a["ShelfType"] != "NoFirstPallet":
            if a["CHCat"] == "SUV":
                if ps[a["SystemId"]] < PCount[a["SystemId"]]:
                    if a["ShelfType"] != "Conveyor":
                        for i in range(a["Capacity"]):
                            Project["Pallets"][p] = CreatePallet(a, p, i)
                            ps[a["SystemId"]] += 1
                            p += 1
                            if ps[a["SystemId"]] >= PCount[a["SystemId"]]:
                                break
