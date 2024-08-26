function setLeftView() {
  camera.alpha = Math.PI / 2;
  camera.beta = Math.PI / 2;
  camera.radius = Math.max(BoundingBox.x, BoundingBox.y, BoundingBox.z) * 2;
}

function setRightView() {
  camera.alpha = -Math.PI / 2;
  camera.beta = Math.PI / 2;
  camera.radius = BoundingBox.x * 2;
}

function setFrontView() {
  camera.alpha = Math.PI;
  camera.beta = Math.PI / 2;
  camera.radius = BoundingBox.z * 2;
}

function setBackView() {
  camera.alpha = 0;
  camera.beta = Math.PI / 2;
  camera.radius = BoundingBox.z * 2;
}

function setTopView() {
  camera.alpha = -Math.PI / 2;
  camera.beta = 0;
  camera.radius = BoundingBox.y * 2;
}

function setBottomView() {
  camera.alpha = Math.PI / 2;
  camera.beta = Math.PI;
  camera.radius = BoundingBox.y * 2;
}

function setPersView() {
  camera.alpha = (210 * Math.PI) / 180;
  camera.beta = (75 * Math.PI) / 180;
  //camera.radius = Math.max(BoundingBox.x,BoundingBox.y,BoundingBox.z)*1.5;
  var vextends = scene.getWorldExtends();
  var center = vextends.min.add(vextends.max).scale(0.5);

  var maxDiameter = vextends.max.subtract(vextends.min).length();
  var distance = maxDiameter / (2 * Math.tan(camera.fov / 2));

  camera.target = center;
  camera.radius = distance;
}

function updateTargetX(value) {
  document.getElementById("TargetX").value = Math.round(value);
}

function updateTargetY(value) {
  document.getElementById("TargetY").value = Math.round(value);
}

function updateTargetZ(value) {
  document.getElementById("TargetZ").value = Math.round(value);
}

function SetTargetX(value) {
  camera.target.x = parseFloat(value);
}

function SetTargetY(value) {
  camera.target.y = parseFloat(value);
}

function SetTargetZ(value) {
  camera.target.z = parseFloat(value);
}

function updateLightValue(value) {
  light.intensity = value / 100;
  document.getElementById("LightValue").textContent = value + "%";
}

function updateAlphaValue(value) {
  console.log(camera, "here check camera");
  camera.alpha = (value / 180) * Math.PI;
  document.getElementById("AlphaRange").value = value; // Math.round(value % 360);
  document.getElementById("AlphaValue").textContent = Math.round(
    (Math.round(value * 100) / 100) % 360,
    2
  );
}

function updateFOVValue(value) {
  camera.fov = (value / 180) * Math.PI;
  document.getElementById("FOVRange").value = value; // Math.round(value % 360);
  document.getElementById("FOVValue").textContent =
    (Math.round(value * 100) / 100) % 360;
}

function updateBetaValue(value) {
  camera.beta = (value / 180) * Math.PI;
  document.getElementById("BetaRange").value = value; // Math.round(value % 180);
  document.getElementById("BetaValue").textContent = Math.round(
    (Math.round(value * 100) / 100) % 180,
    2
  );
}

function updateDistanceValue(value) {
  camera.radius = value;
  document.getElementById("DistanceInput").value = Math.round(value);
}

function updateNearValue(value) {
  camera.minZ = value;
}

function updateFarValue(value) {
  camera.maxZ = value;
}

function toggleDebug(value) {
  if (value) scene.debugLayer.show();
  else scene.debugLayer.hide();
}

function toggleMessages(value) {
  if (value)
    document.getElementById("LoadingScreenDiv").style.display = "block";
  else document.getElementById("LoadingScreenDiv").style.display = "none";
}

function toggleOrtho(value) {
  if (value) {
    // Switch to orthographic camera
    camera.mode = BABYLON.Camera.ORTHOGRAPHIC_CAMERA;

    // Adjust these values as needed
    var aspect = engine.getAspectRatio(camera);
    var orthoHeight = 10000;
    camera.orthoTop = orthoHeight;
    camera.orthoBottom = -orthoHeight;
    camera.orthoLeft = -orthoHeight * aspect;
    camera.orthoRight = orthoHeight * aspect;
  } else {
    // Switch back to perspective camera
    camera.mode = BABYLON.Camera.PERSPECTIVE_CAMERA;
  }
}

function VisCheckboxChanged(Section) {
  ObjectGroups[Section].forEach((COT) => {
    var cb = document.getElementById("CB" + Section + "Vis");
    COT.setEnabled(cb.checked);
  });
}

function CBBuildAnimChg() {
  var cb = document.getElementById("CBBuildAnim");
  Object.values(ObjectGroups).forEach((Section) => {
    Section.forEach((COT) => {
      COT.setEnabled(!cb.checked);
    });
  });
  BuildAnimStep = 0;
}

function CBLiftAnimChg() {
  var cb = document.getElementById("CBLiftAnim");
  if (cb.checked) {
    Object.values(Project.Carriers).forEach((Carr) => {
      if (Carr.CarrierType == "Lift") {
        CarrierPosChanged(
          Carr.Id,
          Math.random() * ((Carr.MaxPos - Carr.MinPos) / 10)
        );
        Carr.AnimYon = Math.random() < 0.5 ? -1 : 1;
      }
    });
  }
  // else
  //   Object.values(Project.Carriers).forEach(Carr => {
  //     if (Carr.CarrierType == "Lift")
  //       CarrierPosChanged(Carr.Id, Carr.MinPos / 10)
  //   });
}

function CBShuttleAnimChg() {
  var cb = document.getElementById("CBShuttleAnim");
  if (cb.checked) {
    Object.values(Project.Carriers).forEach((Carr) => {
      if (Carr.CarrierType == "Shuttle") {
        CarrierPosChanged(
          Carr.Id,
          Math.random() * ((Carr.MaxPos - Carr.MinPos) / 10)
        );
        Carr.AnimYon = Math.random() < 0.5 ? -1 : 1;
      }
    });
  }
  // else
  //   Object.values(Project.Carriers).forEach(Carr => {
  //     if (Carr.CarrierType == "Shuttle")
  //       CarrierPosChanged(Carr.Id, Carr.MinPos / 10)
  //   });
}

function InitClipPlanes() {
  var bb = CenterTarget();
  minPoint = bb.min;
  maxPoint = bb.max;
  margin = 100;
  scene.clipPlane = new BABYLON.Plane(-1, 0, 0, minPoint.x - margin);
  scene.clipPlane2 = new BABYLON.Plane(1, 0, 0, -maxPoint.x - margin);
  scene.clipPlane3 = new BABYLON.Plane(0, -1, 0, minPoint.y - margin);
  scene.clipPlane4 = new BABYLON.Plane(0, 1, 0, -maxPoint.y - margin);
  scene.clipPlane5 = new BABYLON.Plane(0, 0, -1, minPoint.z - margin);
  scene.clipPlane6 = new BABYLON.Plane(0, 0, 1, -maxPoint.z - margin);

  document.getElementById("XClipRange").min = minPoint.x - margin;
  document.getElementById("XClipRange").max = maxPoint.x + margin;
  document.getElementById("XClipRange").value = minPoint.x;
  document.getElementById("EXClipRange").min = minPoint.x - margin;
  document.getElementById("EXClipRange").max = maxPoint.x + margin;
  document.getElementById("EXClipRange").value = maxPoint.x;

  document.getElementById("YClipRange").min = minPoint.y - margin;
  document.getElementById("YClipRange").max = maxPoint.y + margin;
  document.getElementById("YClipRange").value = minPoint.y;
  document.getElementById("EYClipRange").min = minPoint.y - margin;
  document.getElementById("EYClipRange").max = maxPoint.y + margin;
  document.getElementById("EYClipRange").value = maxPoint.y;

  document.getElementById("ZClipRange").min = minPoint.z - margin;
  document.getElementById("ZClipRange").max = maxPoint.z + margin;
  document.getElementById("ZClipRange").value = minPoint.z;
  document.getElementById("EZClipRange").min = minPoint.z - margin;
  document.getElementById("EZClipRange").max = maxPoint.z + margin;
  document.getElementById("EZClipRange").value = maxPoint.z;
}

function CenterTarget() {
  var sceneExtends = scene.getWorldExtends();
  minPoint = sceneExtends.min;
  maxPoint = sceneExtends.max;
  BoundingBox = maxPoint.subtract(minPoint);
  console.log("Bounding Box", BoundingBox);
  var centerPoint = BABYLON.Vector3.Center(minPoint, maxPoint);
  camera.target = centerPoint;
  updateTargetX(camera.target.x);
  updateTargetY(camera.target.y);
  updateTargetZ(camera.target.z);
  return { min: minPoint, max: maxPoint };
}

function updateClipPlane(pl, value) {
  switch (pl) {
    case 0:
      scene.clipPlane = new BABYLON.Plane(-1, 0, 0, value);
      break;
    case 1:
      scene.clipPlane2 = new BABYLON.Plane(1, 0, 0, -value);
      break;
    case 2:
      scene.clipPlane3 = new BABYLON.Plane(0, -1, 0, value);
      break;
    case 3:
      scene.clipPlane4 = new BABYLON.Plane(0, 1, 0, -value);
      break;
    case 4:
      scene.clipPlane5 = new BABYLON.Plane(0, 0, -1, value);
      break;
    case 5:
      scene.clipPlane6 = new BABYLON.Plane(0, 0, 1, -value);
      break;
  }
}

function GetSceneProps() {
  savedSceneProps = {
    "light.intensity": light.intensity,
    "camera.mode": camera.mode,
    "camera.target.x": camera.target.x,
    "camera.target.y": camera.target.y,
    "camera.target.z": camera.target.z,
    "camera.alpha": camera.alpha,
    "camera.beta": camera.beta,
    "camera.radius": camera.radius,
    "camera.fov": camera.fov,
    "scene.clipPlane.d": scene.clipPlane.d,
    "scene.clipPlane2.d": scene.clipPlane2.d,
    "scene.clipPlane3.d": scene.clipPlane3.d,
    "scene.clipPlane4.d": scene.clipPlane4.d,
    "scene.clipPlane5.d": scene.clipPlane5.d,
    "scene.clipPlane6.d": scene.clipPlane6.d,
  };
  return savedSceneProps;
}

function SetSceneProps(Props) {
  light.intensity = Props["light.intensity"];
  camera.mode = Props["camera.mode"];
  camera.target.x = Props["camera.target.x"];
  camera.target.y = Props["camera.target.y"];
  camera.target.z = Props["camera.target.z"];
  camera.alpha = Props["camera.alpha"];
  camera.beta = Props["camera.beta"];
  camera.radius = Props["camera.radius"];
  camera.fov = Props["camera.fov"];
  scene.clipPlane.d = Props["scene.clipPlane.d"];
  scene.clipPlane2.d = Props["scene.clipPlane2.d"];
  scene.clipPlane3.d = Props["scene.clipPlane3.d"];
  scene.clipPlane4.d = Props["scene.clipPlane4.d"];
  scene.clipPlane5.d = Props["scene.clipPlane5.d"];
  scene.clipPlane6.d = Props["scene.clipPlane6.d"];
}
