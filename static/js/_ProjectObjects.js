function CreateMaterials() {
  Materials.Steel = setMat4(
    "Steel",
    [0.75 * 255, 0.75 * 255, 0.75 * 255, 100],
    scene
  );
  Materials.Chain = setMat4(
    "Chain",
    [0.056 * 255, 0.056 * 255, 0.056 * 255, 100],
    scene
  );
}

function AddMesh(task) {
  var COT = new BABYLON.TransformNode(task.name, scene);
  Object.values(task.loadedMeshes).forEach((tlm) => {
    tlm.parent = COT;
    tlm.scaling = new BABYLON.Vector3(1, 1, -1); //Carr.MinPos / 10
  });
  loadedMeshes[task.name] = COT;

  DisplayMessage("Success", task.name + " loaded.");
}

function setMat4(Name, Renk, sc) {
  if (Name in Materials) return Materials[Name];
  else {
    Materials[Name] = new BABYLON.StandardMaterial(Name, sc);
    Materials[Name].diffuseColor = new BABYLON.Color3(
      Renk[0] / 255,
      Renk[1] / 255,
      Renk[2] / 255
    );
    Materials[Name].alpha = Renk[3] / 100;
    Materials[Name].specularColor = new BABYLON.Color3(0, 0, 0);
    return Materials[Name];
  }
}

function InitNewProject(data) {
  Project = data;
  console.log(Project);
  // Cleanup prev elements
  if (scene && engine) {
    engine.stopRenderLoop();
    engine.dispose();
    engine = null;
    scene.dispose();
    scene = null;
    ObjectGroups = InitObjectGroups();
  }

  engine = new BABYLON.Engine(canvas, true);
  scene = createScene();
  engine.runRenderLoop(function () {
    if (scene) {
      scene.render();
    }
  });

  document.getElementById("BOMContainer").innerHTML = "";
  document.getElementById("DivBuildingPart").innerHTML = "";
  document.getElementById("CBCarrPart").innerHTML = "";

  var GroupsToCheck = ["Shelves", "Carriers", "Pallets"];

  Object.values(GroupsToCheck).forEach((Group) => {
    Object.values(Project["_3DObjects"]).forEach((Item) => {
      if (!(Item.Name in Tasks)) {
        Tasks[Item.Name] = assetsManager.addMeshTask(
          Item.Name,
          "",
          "static/3dobjs/CustomObjects/",
          Item.Name + ".obj"
        );
        Tasks[Item.Name].onSuccess = AddMesh;
      }
    });
    if (Group in Project)
      Object.values(Project[Group]).forEach((Item) => {
        if (Item.Product in ProductResources) {
          ProductResources[Item.Product].Meshes.forEach(function (Msh) {
            if (!(Msh in Tasks)) {
              Tasks[Msh] = assetsManager.addMeshTask(
                Msh,
                "",
                "static/3dobjs/ParKompact/",
                Msh + ".obj"
              );
              Tasks[Msh].onSuccess = AddMesh;
            }
          });
          ProductResources[Item.Product].Polies.forEach(function (Poly) {
            if (!(Poly in Tasks)) {
              Tasks[Poly] = assetsManager.addTextFileTask(
                Poly,
                "static/3dobjs/Polies/" + Poly + ".json"
              );
              Tasks[Poly].onSuccess = function AddPoly(task) {
                loadedPolies[task.name] = JSON.parse(task.text);
                DisplayMessage("Success", task.name + " loaded.");
              };
            }
          });
        }
      });
  });

  assetsManager.load();
  assetsManager.onFinish = function (tasks) {
    CreateSceneElements();
    CreateCarrElements();
    CreateBOMElements();
    InitClipPlanes();
    setPersView();
    CreateAllObjectsList();
    scene.registerBeforeRender(AnimateScene);
  };

  loadedMeshes = {};
  loadedPolies = {};
  Tasks = {};
  meshTasks = [];
}

function CreateSceneElements() {
  // Init BOM elements
  Project.BOM = {
    Shelves: {},
    Systems: {},
    Rooms: {},
    Pallets: {},
    SUV: 0,
    SEDAN: 0,
    EmptyPallet: 0,
    Carriers: {},
  };

  // Create Lights
  Object.values(Project._Lights).forEach((Light) => {
    switch (Light.Type) {
      case "POINT":
        li = new BABYLON.PointLight(
          "hemiLight",
          new BABYLON.Vector3(Light.X, Light.Z, Light.Y),
          scene
        );
        li.intensity = Light.Intensity / 100;
        break;
    }
  });

  // Create BLOCK elements
  Object.values(Project._PolyParts).forEach((Part) => {
    Sections = JSON.parse(Part.Vertices);
    Object.values(Sections).forEach((Section) => {
      let polygonShape = new BABYLON.PolygonMeshBuilder("Part", Section, scene);
      JSON.parse(Part.Holes).forEach((Hole) => {
        polygonShape.addHole(Hole);
      });
      let flatPolygon = polygonShape.build(false, Part["Thickness"]);
      flatPolygon.position.y = Part["Z"];
      //flatPolygon.createNormals(true);
      Renk = Part["Material"].split(",").map(Number);
      flatPolygon.material = setMat4(Part["Material"], Renk, scene); // Materials[Part["Material"]];
      //flatPolygon.material.backFaceCulling = false;
      if (!(Part.GroupName in ObjectGroups)) {
        ObjectGroups[Part.GroupName] = [];
        AddBuildingRow(Part.GroupName);
      }
      ObjectGroups[Part.GroupName].push(flatPolygon);
    });
  });

  // Create Sttel Structure
  Project.BOM.Steel = {};
  Object.values(Project._Steels).forEach((Steel) => {
    Polypoints = [];
    loadedPolies[Steel.Type].polylines[0].points.forEach((p) => {
      Polypoints.push(new BABYLON.Vector3(p.y, p.x, 0));
    });
    const options = {
      shape: Polypoints,
      path: [
        new BABYLON.Vector3(Steel.X1, Steel.Z1, Steel.Y1),
        new BABYLON.Vector3(Steel.X2, Steel.Z2, Steel.Y2),
      ],
      updatable: false,
      sideOrientation: BABYLON.Mesh.DOUBLESIDE,
      closeShape: true,
    };
    if (!(Steel.Type in Project.BOM.Steel)) Project.BOM.Steel[Steel.Type] = 0;
    Project.BOM.Steel[Steel.Type] += Math.round(
      BABYLON.Vector3.Distance(options.path[0], options.path[1]) / 1000
    );

    let SteelExt = new BABYLON.ExtrudeShape("Steel", options, scene);
    SteelExt.material = Materials.Steel;
    ObjectGroups.Steel.push(SteelExt);
  });

  // Create Walls
  Object.values(Project._PolyWalls).forEach((Wall) => {
    DuvarKesit = [
      new BABYLON.Vector3(-Wall.Thickness / 2, 0, 0),
      new BABYLON.Vector3(-Wall.Thickness / 2, Wall.Height, 0),
      new BABYLON.Vector3(-Wall.Thickness / 2, Wall.Height, 0),
      new BABYLON.Vector3(Wall.Thickness / 2, Wall.Height, 0),
      new BABYLON.Vector3(Wall.Thickness / 2, Wall.Height, 0),
      new BABYLON.Vector3(Wall.Thickness / 2, 0, 0),
      new BABYLON.Vector3(Wall.Thickness / 2, 0, 0),
      new BABYLON.Vector3(-Wall.Thickness / 2, 0, 0),
    ];

    Sections = JSON.parse(Wall.Polyline);
    Object.values(Sections).forEach((Section) => {
      pbas = Section[0];
      Section.forEach((p) => {
        if (pbas != p) {
          // İlk elemanı atla
          var path = [
            new BABYLON.Vector3(pbas.x, 0, pbas.y),
            new BABYLON.Vector3(p.x, 0, p.y),
          ];
          const options = {
            shape: DuvarKesit,
            path: path,
            updatable: false,
            sideOrientation: BABYLON.Mesh.DOUBLESIDE,
            closeShape: true,
            cap: 3,
          };
          pbas = p;
          let WallExt = new BABYLON.ExtrudeShape("Steel", options, scene);
          Renk = Wall["Material"].split(",").map(Number);
          WallExt.material = setMat4(Wall["Material"], Renk, scene); // Materials[Part["Material"]];
          WallExt.material.backFaceCulling = false;
          //SteelExt.material = Materials.Steel;
          if (!(Wall.GroupName in ObjectGroups)) {
            ObjectGroups[Wall.GroupName] = [];
            AddBuildingRow(Wall.GroupName);
          }
          ObjectGroups[Wall.GroupName].push(WallExt);
        }
      });
    });
  });

  // Create 3d Obkects
  if ("_3DObjects" in Project)
    Object.values(Project["_3DObjects"]).forEach((Obj) => {
      COTNo += 1;
      Obj.COT = loadedMeshes[Obj.Name].clone(Obj.Name + COTNo);

      Obj.COT.position = new BABYLON.Vector3(Obj.X, Obj.Z, Obj.Y);
      Obj.COT.scaling.x = Obj.Scale / 100;
      Obj.COT.scaling.y = Obj.Scale / 100;
      Obj.COT.scaling.z = Obj.Scale / 100;
      Obj.COT.rotation.y = (Math.PI * Obj.Angle) / 180;
      ObjectGroups.Objects.push(Obj.COT);
    });

  //Create Carriers
  if ("Carriers" in Project)
    Object.values(Project.Carriers).forEach((Carr) => {
      LSTDist = 0;
      Carr.RightPos = 0;
      if (Carr.Product == "ELST2") {
        Object.values(Project.Carriers).forEach((Carr2) => {
          console.log(Carr.Product, Carr2.Product);
          if (Carr2.Product == "ES4LST" && Carr2.ParentId == Carr.Id) {
            LSTDist = (Carr2.MaxPos - Carr2.MinPos) / 10 - 5955;
            Carr.RightPos = LSTDist + 5985;
          }
        });
      }
      console.log(Carr.Product, LSTDist);
      Carr.COT = new BABYLON.TransformNode(Carr.Name, scene);
      Carr.COT.position = new BABYLON.Vector3(Carr.X, 0, Carr.Y);
      Carr.Position = 0;
      if (!Carr.ParentId) {
        mes = Math.abs(Math.round((Carr.MaxPos - Carr.MinPos) / 100));

        if (!(Carr.Product in Project.BOM.Carriers))
          Project.BOM.Carriers[Carr.Product] = {};

        if (!(mes in Project.BOM.Carriers[Carr.Product]))
          Project.BOM.Carriers[Carr.Product][mes] = 0;
        Project.BOM.Carriers[Carr.Product][mes] += 1;
      }
      Carr.Exts = [];
      ProductResources[Carr.Product].Meshes.forEach(function (Msh) {
        COTNo += 1;
        var clone = loadedMeshes[Msh].clone(Msh + COTNo);

        switch (Msh) {
          case "ELIFT-CHASIS":
          case "ELIFTTT-CHASIS":
          case "ELIFTUG-CHASIS":
          case "LST2-LEFT":
          case "LST2-RIGHT":
          case "LST2-MID":
          case "LST3-LEFT":
          case "LST3-RIGHT":
          case "LST3-MID":
            clone.rotation.y = (Carr.Angle / 180) * Math.PI;
            clone.parent = Carr.COT;
            if (Msh == "LST2-LEFT") clone.position.x += LSTDist;
            ObjectGroups.Carriers.push(Carr.COT);
            if (Carr.Exts.length == 0) {
              var ChainCOT = new BABYLON.TransformNode("Chain", scene);
              for (i = 4; i < 8; i++) {
                if (i == 4 || i == 5) chainmes = Carr.RightPos;
                else chainmes = 0;
                ChainPoints = [];
                loadedPolies["ELIFTCHAIN24B1"].polylines[i].points.forEach(
                  (p) => {
                    ChainPoints.push(new BABYLON.Vector3(p.y, p.x, 0));
                  }
                );
                const options = {
                  shape: ChainPoints,
                  path: [
                    new BABYLON.Vector3(chainmes, Carr.COT.position.y, 0),
                    new BABYLON.Vector3(
                      chainmes,
                      Carr.Product == "ELU" ? -1909 : Carr.MaxPos / 10 + 400,
                      0
                    ),
                  ],
                  updatable: true,
                  sideOrientation: BABYLON.Mesh.DOUBLESIDE,
                  closeShape: true,
                };
                let LiftChain = new BABYLON.ExtrudeShape(
                  "LiftChain",
                  options,
                  scene
                );
                Carr.Exts.push(LiftChain);
                LiftChain.parent = ChainCOT;
                LiftChain.material = Materials.Chain;
              }
              ObjectGroups.Carriers.push(ChainCOT);
              ChainCOT.rotation.y = (Carr.Angle / 180) * Math.PI;
              ChainCOT.position = new BABYLON.Vector3(Carr.X, 0, Carr.Y);
            }
            break;
          case "LIFT-CW":
          case "LIFT-CWUG":
            clone.position = new BABYLON.Vector3(
              Carr.X + Carr.RightPos,
              Carr.MaxPos / 10,
              Carr.Y
            );
            clone.rotation.y = (Carr.Angle / 180) * Math.PI;
            Carr.CW = clone;
            var ChainCOT = new BABYLON.TransformNode("CWChain", scene);
            Carr.CWExts = [];
            for (i = 0; i < 4; i++) {
              ChainPoints = [];
              loadedPolies["ELIFTCHAIN24B1"].polylines[i].points.forEach(
                (p) => {
                  ChainPoints.push(new BABYLON.Vector3(p.y, p.x, 0));
                }
              );
              const options = {
                shape: ChainPoints,
                path: [
                  new BABYLON.Vector3(Carr.RightPos, Carr.CW.position.y, 0),
                  new BABYLON.Vector3(
                    Carr.RightPos,
                    Carr.Product == "ELU" ? -1909 : Carr.MaxPos / 10 + 400,
                    0
                  ),
                ],
                updatable: true,
                sideOrientation: BABYLON.Mesh.DOUBLESIDE,
                closeShape: true,
              };
              let CWChain = new BABYLON.ExtrudeShape("CWChain", options, scene);
              Carr.CWExts.push(CWChain);
              CWChain.parent = ChainCOT;
              CWChain.material = Materials.Chain;
            }
            ObjectGroups.Carriers.push(ChainCOT);
            ObjectGroups.Carriers.push(Carr.CW);
            ChainCOT.rotation.y = (Carr.Angle / 180) * Math.PI;
            ChainCOT.position = new BABYLON.Vector3(Carr.X, 0, Carr.Y);
            break;
          case "LIFT-DUL":
          case "LIFT-DUM":
          case "LIFT-DUR":
            if (Carr.Product == "ELU")
              clone.position = new BABYLON.Vector3(Carr.X, -1909, Carr.Y);
            else
              clone.position = new BABYLON.Vector3(
                Carr.X,
                Carr.MaxPos / 10 + 400,
                Carr.Y
              );
            if (Msh == "LIFT-DUR") {
              clone.position.x += LSTDist;
              if (Carr.Product == "ELST2") {
                clone.position.x += 5985;
              }
            }
            clone.rotation.y = (Carr.Angle / 180) * Math.PI;
            Carr[Msh] = clone;
            ObjectGroups.Carriers.push(Carr[Msh]);
            break;
          case "LIFT-FND":
            break;
          case "LST-SHUTTLE":
          case "TT-ONCARR":
            clone.position = new BABYLON.Vector3(Carr.X, Carr.Z, Carr.Y);
            clone.rotation.y = Math.PI / 180;
            Carr.COT = clone;
            ObjectGroups.Carriers.push(Carr.COT);
            var Parent = Project.Carriers[Carr.ParentId];
            if (Parent) {
              clone.parent = Parent.COT;
            }
            break;
          case "SHUTTLE":
            clone.position = new BABYLON.Vector3(Carr.X, Carr.Z, Carr.Y);
            Carr.COT = clone;
            RailPoints = [];
            Carr.Exts = [];
            ObjectGroups.Carriers.push(Carr.COT);
            loadedPolies["SHUTTLELEFTRAIL"].polylines[0].points.forEach((p) => {
              RailPoints.push(new BABYLON.Vector3(p.x, p.y, 0));
            });
            const leftoptions = {
              shape: RailPoints,
              path: [
                new BABYLON.Vector3(Carr.MinPos / 10 - 3000, Carr.Z, Carr.Y),
                new BABYLON.Vector3(Carr.MaxPos / 10 + 3000, Carr.Z, Carr.Y),
              ],
              updatable: true,
              sideOrientation: BABYLON.Mesh.DOUBLESIDE,
            };
            let LeftRailExt = new BABYLON.ExtrudeShape(
              "LeftRail",
              leftoptions,
              scene
            );
            LeftRailExt.material = Materials.Shelf;
            ObjectGroups.Carriers.push(LeftRailExt);
            Carr.Exts.push(LeftRailExt);

            RailPoints = [];
            loadedPolies["SHUTTLERIGHTRAIL"].polylines[0].points.forEach(
              (p) => {
                RailPoints.push(new BABYLON.Vector3(p.x, p.y, 0));
              }
            );
            const rightoptions = {
              shape: RailPoints,
              path: [
                new BABYLON.Vector3(Carr.MinPos / 10 - 3000, Carr.Z, Carr.Y),
                new BABYLON.Vector3(Carr.MaxPos / 10 + 3000, Carr.Z, Carr.Y),
              ],
              updatable: true,
              sideOrientation: BABYLON.Mesh.DOUBLESIDE,
            };
            let RightRailExt = new BABYLON.ExtrudeShape(
              "RightRail",
              rightoptions,
              scene
            );
            RightRailExt.material = Materials.Shelf;
            ObjectGroups.Carriers.push(RightRailExt);
            Carr.Exts.push(RightRailExt);
            break;
        }
      });
      CarrierPosChanged(Carr.Id, Carr.MinPos / 10);
      if (Carr.CarrierType == "Lift") {
        if (Object.values(Project.Rooms).length > 0)
          if (Carr.MinPos / 10 < Object.values(Project.Rooms)[0].Z)
            CarrierPosChanged(Carr.Id, Object.values(Project.Rooms)[0].Z);
      }
      if (Carr.CarrierType == "Turntable") {
        if (Object.values(Project.Rooms).length > 0)
          if (Object.values(Project.Rooms)[0].RoomType == "Adliye")
            CarrierPosChanged(Carr.Id, 90);
      }
    });

  // Create Shelves
  if ("Shelves" in Project)
    Object.values(Project.Shelves).forEach((Shelf) => {
      if (!(Shelf.Product in Project.BOM.Shelves))
        Project.BOM.Shelves[Shelf.Product] = 0;

      if (!(Shelf.SystemId in Project.BOM.Systems)) {
        Project.BOM.Systems[Shelf.SystemId] = {
          SUV: 0,
          SEDAN: 0,
          EmptyPallet: 0,
          Pallet: 0,
        };
      }

      Project.BOM.Shelves[Shelf.Product] += 1;
      Project.BOM.Systems[Shelf.SystemId][Shelf.CHCat] += Shelf.Capacity;
      Project.BOM[Shelf.CHCat] += Shelf.Capacity;

      ProductResources[Shelf.Product].Meshes.forEach(function (Msh) {
        COTNo += 1;
        Shelf.COT = loadedMeshes[Msh].clone(Msh + COTNo);

        Shelf.COT.position = new BABYLON.Vector3(Shelf.X, Shelf.Z, Shelf.Y);
        if (Shelf.Side == "Left") Shelf.COT.scaling.z = -1;
        //Shelf.COT.scaling.x = -1;
        ObjectGroups.Shelves.push(Shelf.COT);
      });
    });

  if (Project.BOM.SUV) {
    Project.BOM.SUV -=
      Project.BOM.SUV +
      Project.BOM.SEDAN -
      Object.values(Project.Pallets).length;
  }

  // Create Rooms
  if ("Rooms" in Project)
    Object.values(Project.Rooms).forEach((Room) => {
      if (!(Room.Product in Project.BOM.Rooms))
        Project.BOM.Rooms[Room.Product] = 0;
      Project.BOM.Rooms[Room.Product] += 1;
    });

  // Create Pallets
  if ("Pallets" in Project)
    Object.values(Project.Pallets).forEach((Pallet) => {
      if (!(Pallet.SystemId in Project.BOM.Systems)) {
        Project.BOM.SystemId[Pallet.SystemId] = {
          SUV: 0,
          SEDAN: 0,
          EmptyPallet: 0,
          Pallet: 0,
        };
      }

      if (!(Pallet.Product in Project.BOM.Pallets))
        Project.BOM.Pallets[Pallet.Product] = 0;

      Project.BOM.Pallets[Pallet.Product] += 1;
      Project.BOM.Systems[Pallet.SystemId]["Pallet"] += 1;
      COTNo += 1;
      Pallet.COT = null;
      if (Pallet.SBID in Project.Shelves) {
        Parent = Project.Shelves[Pallet.SBID];
        Pallet.COT = loadedMeshes["PALLET"].clone("PALLET" + COTNo);
        Pallet.COT.parent = Parent.COT;
        if (Parent.ShelfType == "NoFirstPallet") Indoff = 1;
        else Indoff = 0;
        Pallet.COT.position = new BABYLON.Vector3(
          0,
          0,
          -(Pallet.Index + Indoff) * 2260
        );
      } else if (Pallet.SBID in Project.Conveyors) {
        Parent = Project.Conveyors[Pallet.SBID];
        ParentCarr = Project.Carriers[Parent.SelfCarrierId];
        Pallet.COT = loadedMeshes["PALLET"].clone("PALLET" + COTNo);

        Pallet.COT.parent = ParentCarr.COT;
      }
      ObjectGroups.Pallets.push(Pallet.COT);
      if (Pallet.COT) {
        if (Pallet.CHCat == "SUV") {
          var araba = getRandomElement(MSUVS);
        } else {
          var araba = getRandomElement(MSedans);
        }
        var car = loadedMeshes[araba].clone(araba + COTNo);
        car.scaling = new BABYLON.Vector3(1000, 1000, 1000);
        car.parent = Pallet.COT;
        car.position.y = -91;
        ObjectGroups.Cars.push(car);
      }
    });

  Object.values(ObjectGroups).forEach((Section) => {
    Section.sort(SortXZ);
  });

  Object.values(Project.BOM.Systems).forEach((Sys) => {
    if (Sys.SUV) {
      Sys.SUV -= Sys.SUV + Sys.SEDAN - Sys.Pallet;
    }
  });

  // Clean up loaded base meshes
  Object.values(loadedMeshes).forEach((mesh) => {
    mesh.dispose();
  });
}

function CreateAllObjectsList() {
  let NewSections = (result = Object.keys(ObjectGroups).filter(
    (item) => !AnimOrder.includes(item)
  ));
  NewSections.sort();

  NewGroup = {};

  NewSections.forEach((Section) => {
    NewGroup[Section] = ObjectGroups[Section];
  });

  AnimOrder.forEach((Section) => {
    NewGroup[Section] = ObjectGroups[Section];
  });
  AllObjects = Object.values(NewGroup).flat();
}

function AnimateScene() {
  cbturn = document.getElementById("CBTurningAnim");
  slturn = document.getElementById("TurningAnimSpeed");
  cbclip = document.getElementById("CBClipAnim");
  slclip = document.getElementById("ClipAnimSpeed");
  cbbuild = document.getElementById("CBBuildAnim");
  cblift = document.getElementById("CBLiftAnim");
  sllift = document.getElementById("LiftAnimSpeed");
  cbshuttle = document.getElementById("CBShuttleAnim");
  slshuttle = document.getElementById("ShuttleAnimSpeed");
  cbtt = document.getElementById("CBTTAnim");

  if (cbturn.checked) {
    camera.alpha = LastAnimAlpha;
    LastAnimAlpha += parseInt(slturn.value) / 10000;
  } else LastAnimAlpha = 0;

  if (cbclip.checked) {
    scene.clipPlane4.d = LastAnimClip;
    LastAnimClip += AnimClipYon * parseInt(slclip.value);
    if (-LastAnimClip > maxPoint.y + 1000 && AnimClipYon == -1) AnimClipYon = 1;
    if (-LastAnimClip < minPoint.y - 1000 && AnimClipYon == 1) AnimClipYon = -1;
  } else {
    LastAnimClip = 0;
    AnimClipYon = 1;
  }

  if (cbbuild.checked) {
    AllObjects[BuildAnimStep].setEnabled(true);
    BuildAnimStep += 1;
    if (BuildAnimStep >= AllObjects.length) cbbuild.checked = false;
  }

  if (cblift.checked) {
    Object.values(Project.Carriers).forEach((Carr) => {
      if (Carr.CarrierType == "Lift") {
        if (Carr.Position > Carr.MaxPos / 10 && Carr.AnimYon == 1)
          Carr.AnimYon = -1;
        if (Carr.Position < Carr.MinPos / 10 && Carr.AnimYon == -1)
          Carr.AnimYon = 1;
        CarrierPosChanged(Carr.Id, Carr.Position + sllift.value * Carr.AnimYon);
      }
    });
  }
  if (cbshuttle.checked) {
    Object.values(Project.Carriers).forEach((Carr) => {
      if (Carr.CarrierType == "Shuttle") {
        if (Carr.Position > Carr.MaxPos / 10 && Carr.AnimYon == 1)
          Carr.AnimYon = -1;
        if (Carr.Position < Carr.MinPos / 10 && Carr.AnimYon == -1)
          Carr.AnimYon = 1;
        CarrierPosChanged(
          Carr.Id,
          Carr.Position + slshuttle.value * Carr.AnimYon
        );
      }
    });
  }
}

function AddBuildingRow(Group) {
  var cont = document.getElementById("DivBuildingPart");
  const htmlSegment = `
  <div class="row mb-0">
    <div class="col">
      <input type="checkbox" id="CB${Group}Vis" name="CB${Group}Vis" onchange="VisCheckboxChanged('${Group}')" checked>
      <label for="CB${Group}Vis">${Group}</label>
    </div>
  </div>`;
  cont.innerHTML += htmlSegment;
}

function AddCarrRow(Carr) {
  var cont = document.getElementById("CBCarrPart");
  if (Carr.CarrierType == "Turntable") Step = 1;
  else Step = 10;
  const htmlSegment = `
    <div class="row mb-0">
      <div class="col-4 text-right" style="text-align:right;" >
      <label for="CBCarrier${Carr.Id}">${Carr.Id}</label>
      <input type="checkbox" id="CBCarrier${
        Carr.Id
      }" name="CBClipAnim" onchange="CarrierVisChanged(${Carr.Id})" checked>
      </div>
      <div class="col-8">
        <input type="range" class="form-range short-range" min="${
          Carr.MinPos / Carr.PosScale
        }" max="${Carr.MaxPos / Carr.PosScale}" step="${Step}" id="CarrRange${
    Carr.Id
  }" value="0" oninput="CarrierPosChanged(${Carr.Id},value)">
      </div>
    </div>`;
  cont.innerHTML += htmlSegment;
}

function CarrierVisChanged(CarrId) {
  cb = document.getElementById("CBCarrier" + CarrId);
  Carr = Project.Carriers[CarrId];

  if ("COT" in Carr) Carr.COT.setEnabled(cb.checked);
  if ("LIFT-DUL" in Carr) Carr["LIFT-DUL"].setEnabled(cb.checked);
  if ("LIFT-DUR" in Carr) Carr["LIFT-DUR"].setEnabled(cb.checked);
  if ("CW" in Carr) Carr.CW.setEnabled(cb.checked);
  if ("Exts" in Carr)
    Object.values(Carr.Exts).forEach((Ext) => {
      Ext.setEnabled(cb.checked);
    });
  if ("CWExts" in Carr)
    Object.values(Carr.CWExts).forEach((Ext) => {
      Ext.setEnabled(cb.checked);
    });
}

function CarrierPosChanged(CarrId, value) {
  Carr = Project.Carriers[CarrId];
  Carr.Position = value;
  if (Carr.CarrierType == "Lift") {
    Carr.COT.position.y = parseInt(value);
    Carr.CW.position.y =
      (Carr.MaxPos + Carr.MinPos) / Carr.PosScale - parseInt(value);
    i = 0;
    Carr.CWExts.forEach((Ext) => {
      ChainPoints = [];
      loadedPolies["ELIFTCHAIN24B1"].polylines[i].points.forEach((p) => {
        ChainPoints.push(new BABYLON.Vector3(p.y, p.x, 0));
      });
      i++;
      const options = {
        shape: ChainPoints,
        path: [
          new BABYLON.Vector3(Carr.RightPos, Carr.CW.position.y - 1300, 0),
          new BABYLON.Vector3(
            Carr.RightPos,
            Carr.Product == "ELU" ? -1909 : Carr.MaxPos / 10 + 400,
            0
          ),
        ],
        updatable: true,
        sideOrientation: BABYLON.Mesh.DOUBLESIDE,
        closeShape: true,
        instance: Ext,
      };
      new BABYLON.ExtrudeShape("Steel", options, scene);
    });

    //i=0
    Carr.Exts.forEach((Ext) => {
      if (i == 4 || i == 6) chainmes = Carr.RightPos;
      else chainmes = 0;
      ChainPoints = [];
      loadedPolies["ELIFTCHAIN24B1"].polylines[i].points.forEach((p) => {
        ChainPoints.push(new BABYLON.Vector3(p.y, p.x, 0));
      });
      i++;
      const options = {
        shape: ChainPoints,
        path: [
          new BABYLON.Vector3(chainmes, Carr.COT.position.y - 373, 0),
          new BABYLON.Vector3(
            chainmes,
            Carr.Product == "ELU" ? -1909 : Carr.MaxPos / 10 + 400,
            0
          ),
        ],
        updatable: true,
        sideOrientation: BABYLON.Mesh.DOUBLESIDE,
        closeShape: true,
        instance: Ext,
      };
      new BABYLON.ExtrudeShape("Steel", options, scene);
    });
  }
  if (Carr.CarrierType == "Turntable")
    Carr.COT.rotation.y = (value / 180) * Math.PI;
  if (Carr.CarrierType == "Shuttle") Carr.COT.position.x = value;
}

function AddBOMRow(Label, Data, unit) {
  var cont = document.getElementById("BOMContainer");

  const rowDiv = document.createElement("div");
  rowDiv.className = "row mb-0 " + unit;

  const col5Div = document.createElement("div");
  col5Div.className = "col-7 small ";
  const spanForName = document.createElement("span");
  spanForName.textContent = Label;
  col5Div.appendChild(spanForName);

  // Create the column for the material quantity
  const col7Div = document.createElement("div");
  col7Div.className = "col-5 text-right small";
  const spanForValue = document.createElement("span");
  spanForValue.textContent = Data;
  col7Div.appendChild(spanForValue);

  // Append columns to the row
  rowDiv.appendChild(col5Div);
  rowDiv.appendChild(col7Div);
  cont.appendChild(rowDiv);
}

function CreateCarrElements() {
  Object.values(Project.Carriers).forEach((Carr) => {
    AddCarrRow(Carr);
  });
}
function CreateBOMElements() {
  Object.keys(Project.BOM.Steel).forEach((Steel) => {
    AddBOMRow(Steel + " (m):", Project.BOM.Steel[Steel], "");
  });

  Object.keys(Project.BOM.Carriers).forEach((Carrier) => {
    Object.keys(Project.BOM.Carriers[Carrier]).forEach((Boy) => {
      AddBOMRow(
        Carrier + "-" + Boy + ":",
        Project.BOM.Carriers[Carrier][Boy],
        ""
      );
    });
  });

  Object.keys(Project.BOM.Shelves).forEach((Shelf) => {
    AddBOMRow("Shelf-" + Shelf + ":", Project.BOM.Shelves[Shelf], "");
  });

  Object.keys(Project.BOM.Rooms).forEach((Room) => {
    AddBOMRow("Room-" + Room + ":", Project.BOM.Rooms[Room], "");
  });

  AddBOMRow("SUV:", Project.BOM.SUV, "");
  AddBOMRow("Sedan:", Project.BOM.SEDAN, "");
  AddBOMRow("Buffer:", Project.BOM.EmptyPallet, "");
  Object.keys(Project.BOM.Pallets).forEach((Pallet) => {
    AddBOMRow("Pallet-" + Pallet + ":", Project.BOM.Pallets[Pallet], "");
  });

  if (Object.keys(Project.BOM.Systems).length > 1) {
    Object.keys(Project.BOM.Systems).forEach((System) => {
      AddBOMRow(
        "System-" + System + ":",
        Project.BOM.Systems[System]["Pallet"],
        "mt-2"
      );
      AddBOMRow("  SUV:", Project.BOM.Systems[System]["SUV"], "");
      AddBOMRow("  Sedan:", Project.BOM.Systems[System]["SEDAN"], "");
    });
  }
}
