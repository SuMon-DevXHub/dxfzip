var Project = null;
var scene = null;
var light = null;
var COTNo = 0;
var assetsManager = null;
var loadedMeshes = {};
var loadedPolies = {};
var Tasks = {};
var meshTasks = [];
var BoundingBox = new BABYLON.Vector3.Zero();
var minPoint = new BABYLON.Vector3.Zero();
var maxPoint = new BABYLON.Vector3.Zero();
var WSID = 0;
var savedSceneProps = null;
var MSUVS = ["SUV04"];
var MSedans = ["SEDAN08"];
var LastAnimAlpha = 0;
var LastAnimClip = 0;
var AnimClipYon = 1;
var AnimOrder = [
  "Steel",
  "Carriers",
  "Rooms",
  "Shelves",
  "Pallets",
  "Cars",
  "Objects",
];
var AllObjects = [];
var BuildAnimStep = 0;
var Materials = {};
var canvas = document.getElementById("babylon-container");
var engine = null; // new BABYLON.Engine(canvas, true);
var camera = null;

let isDragging = false;
let startingPoint = { x: 0, y: 0 };
let PanningSensitivity = -1;

//var MSUVS = ["SUV04", "SUV18", "SUV22", "SUV30",]
//var MSedans = ["SEDAN01", "SEDAN02", "SEDAN03", "SEDAN05", "SEDAN06", "SEDAN07", "SEDAN08", "SEDAN09", "SEDAN10", "SEDAN11", "SEDAN12", "SEDAN13", "SEDAN14", "SEDAN15", "SEDAN16", "SEDAN17", "SEDAN19", "SEDAN20", "SEDAN21", "SEDAN23", "SEDAN24", "SEDAN25", "SEDAN26", "SEDAN27", "SEDAN28", "SEDAN29"]

const ws = new WebSocket("ws://" + "51.195.203.15" + ":9000/");

var ObjectGroups = InitObjectGroups();

function InitObjectGroups() {
  return {
    Steel: [],
    Carriers: [],
    Rooms: [],
    Shelves: [],
    Pallets: [],
    Cars: [],
    Objects: [],
  };
}

var ProductResources = {
  EL: {
    Meshes: ["ELIFT-CHASIS", "LIFT-CW", "LIFT-DUR", "LIFT-DUL"],
    Polies: ["HEA260", "ELIFTCHAIN24B1"],
  },
  ELTT: {
    Meshes: ["ELIFTTT-CHASIS", "LIFT-CW", "LIFT-DUR", "LIFT-DUL"],
    Polies: ["HEA260", "ELIFTCHAIN24B1"],
  },
  ELU: {
    Meshes: ["ELIFTUG-CHASIS", "LIFT-CWUG", "LIFT-DUR", "LIFT-DUL"],
    Polies: ["HEA260", "ELIFTCHAIN24B1"],
  },
  ELST2: {
    Meshes: [
      "LST2-LEFT",
      "LST2-RIGHT",
      "LST2-MID",
      "LIFT-CW",
      "LIFT-DUR",
      "LIFT-DUL",
      "LIFT-DUM",
    ],
    Polies: ["HEA260", "ELIFTCHAIN24B1"],
  },
  ES4LST: { Meshes: ["LST-SHUTTLE"], Polies: [] },
  ETT4LST: { Meshes: ["TT-ONCARR"], Polies: [] },
  ETT4L: { Meshes: ["TT-ONCARR"], Polies: [] },
  ESHB1: { Meshes: ["SHELF-B-1"], Polies: ["HEA260", "HEA200"] },
  ESHB2: { Meshes: ["SHELF-B-2"], Polies: ["HEA260", "HEA200"] },
  ESHB3: { Meshes: ["SHELF-B-3"], Polies: ["HEA260", "HEA200"] },
  ESHB4: { Meshes: ["SHELF-B-4"], Polies: ["HEA260", "HEA200"] },
  ESHB5: { Meshes: ["SHELF-B-5"], Polies: ["HEA260", "HEA200"] },
  ESHB6: { Meshes: ["SHELF-B-6"], Polies: ["HEA260", "HEA200"] },
  ESHS1: { Meshes: ["SHELF-S-1"], Polies: ["HEA260", "HEA200"] },
  ESHS2: { Meshes: ["SHELF-S-2"], Polies: ["HEA260", "HEA200"] },
  ESHS3: { Meshes: ["SHELF-S-3"], Polies: ["HEA260", "HEA200"] },
  ESHS4: { Meshes: ["SHELF-S-4"], Polies: ["HEA260", "HEA200"] },
  ESHS5: { Meshes: ["SHELF-S-5"], Polies: ["HEA260", "HEA200"] },
  ESHS6: { Meshes: ["SHELF-S-6"], Polies: ["HEA260", "HEA200"] },
  ESHU1: { Meshes: ["SHELF-U-1"], Polies: ["HEA260", "HEA200"] },
  ESHU2: { Meshes: ["SHELF-U-2"], Polies: ["HEA260", "HEA200"] },
  ESHU3: { Meshes: ["SHELF-U-3"], Polies: ["HEA260", "HEA200"] },
  ESHU4: { Meshes: ["SHELF-U-4"], Polies: ["HEA260", "HEA200"] },
  ESHU5: { Meshes: ["SHELF-U-5"], Polies: ["HEA260", "HEA200"] },
  ESHU6: { Meshes: ["SHELF-U-6"], Polies: ["HEA260", "HEA200"] },
  ECS: { Meshes: [], Polies: [] },
  ES: {
    Meshes: ["SHUTTLE"],
    Polies: ["SHUTTLELEFTRAIL", "SHUTTLERIGHTRAIL", "BOX250X250"],
  },
  EP: {
    Meshes: [
      "PALLET",
      "SUV04",
      //"SUV18", "SUV22", "SUV30", "SEDAN01", "SEDAN02", "SEDAN03", "SEDAN05", "SEDAN06", "SEDAN07",
      "SEDAN08",
      //"SEDAN09", "SEDAN10", "SEDAN11", "SEDAN12", "SEDAN13", "SEDAN14", "SEDAN15", "SEDAN16", "SEDAN17", "SEDAN19", "SEDAN20", "SEDAN21", "SEDAN23", "SEDAN24", "SEDAN25", "SEDAN26", "SEDAN27", "SEDAN28", "SEDAN29"
    ],
    Polies: [],
  },
};

BABYLON.DefaultLoadingScreen.prototype.displayLoadingUI = function () {
  console.log("displayLoadingUI before loading screen div");
  document.getElementById("LoadingScreenDiv").style.display = "block";
};

BABYLON.DefaultLoadingScreen.prototype.hideLoadingUI = function () {
  console.log("From hide loading screen");
  document.getElementById("LoadingScreenDiv").style.display = "none";
};

function takePicture() {
  var desiredWidth = 3840 * 2;
  var aspectRatio = engine.getAspectRatio(camera);
  var desiredHeight = desiredWidth / aspectRatio;

  BABYLON.Tools.CreateScreenshotUsingRenderTarget(
    engine,
    camera,
    { width: desiredWidth, height: desiredHeight },
    function (data) {
      var a = document.createElement("a");
      a.href = data;
      const now = new Date();
      a.download =
        "View_" + now.toISOString().replace(/:/g, "").replace(/\..+/, "");
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
    }
  );
}

function saveScene() {
  console.log(GetSceneProps());
  downloadObjectAsJson(GetSceneProps(), "SceneProps.json");
}

function loadScene() {
  document.getElementById("fileInput").click();
}

function handleFile(files) {
  if (files.length === 0) {
    console.log("No file selected!");
    return;
  }
  const file = files[0];
  const reader = new FileReader();

  reader.onload = (e) => {
    const fileContents = e.target.result;
    try {
      savedSceneProps = JSON.parse(fileContents);
      SetSceneProps(savedSceneProps);
    } catch (error) {
      console.error("Error parsing JSON:", error);
    }
  };

  reader.onerror = (e) => {
    console.error("Error reading file:", e);
  };

  reader.readAsText(file); // Read the file as text
}

function getRandomElement(arr) {
  if (!arr.length) {
    return; // Return undefined if the array is empty
  }
  const randomIndex = Math.floor(Math.random() * arr.length);
  return arr[randomIndex];
}

function downloadObjectAsJson(objectData, fileName) {
  const jsonString = JSON.stringify(objectData, null, 2); // null and 2 are for formatting purposes
  const blob = new Blob([jsonString], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = fileName;
  document.body.appendChild(a); // Append the anchor to the document
  a.click(); // Simulate a click on the anchor
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

function readFile() {
  var input = document.getElementById("fileInput");

  if (!input.files.length) {
    alert("Please select a file.");
    return;
  }

  var file = input.files[0];
  var reader = new FileReader();

  reader.onload = function (e) {
    try {
      var obj = JSON.parse(e.target.result);
    } catch (error) {
      alert("Error parsing JSON: " + error);
    }
  };

  reader.onerror = function () {
    alert("Failed to read file!");
  };

  reader.readAsText(file);
}

function SortXZ(a, b) {
  try {
    var abi = a.getBoundingInfo();
    var bbi = b.getBoundingInfo();

    amin = abi.boundingBox.minimumWorld;
    bmin = bbi.boundingBox.minimumWorld;

    if (amin.y !== bmin.y) {
      return amin.y - bmin.y;
    } else {
      return amin.x - bmin.x;
    }
  } catch (e) {
    if (a.position.x !== b.position.x) {
      return a.position.x - b.position.x;
    } else {
      return a.position.y - b.position.y;
    }
  }
}
