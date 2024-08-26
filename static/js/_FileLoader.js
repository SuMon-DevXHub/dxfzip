ws.onopen = function () {
  if (ProjectName && ProjectVersion)
    ws.send(
      JSON.stringify({
        Command: "SendProject",
        Data: { ProjectName: ProjectName, Version: ProjectVersion },
      })
    );
  else ws.send(JSON.stringify({ Command: "SendProjectList", Data: {} }));
};

ws.onmessage = function (e) {
  gelen = JSON.parse(e.data);
  switch (gelen.Command) {
    case "Project":
      InitNewProject(gelen.Data);
      break;
    case "SetWSId":
      WSID = gelen.Data;
      console.log(WSID);
      break;
    case "ProjectList":
      ExistingDB = gelen.Data;
      console.log(gelen.Data);
      let list = document.getElementById("MessageList");

      ExistingDB.forEach((project) => {
        let listItem = document.createElement("li");
        listItem.className =
          "list-group-item list-group-item-action d-flex justify-content-between align-items-center";
        listItem.textContent = `${project.Name} - Version ${project.Version}`;
        listItem.style.cursor = "pointer";

        // Change this to your actual hostname and port
        let hostname = document.location.hostname;
        let port = document.location.port;
        let url = `http://${hostname}:${port}/Projects/${project.Name}/${project.Version}`;

        listItem.onclick = () => {
          console.log(url, "from onclick");
          window.location.href = url;
        };

        // Creating the download link
        var downloadLink = document.createElement("a");
        downloadLink.href = "/" + project.dxf; // Assuming '/download' is the path to trigger the download
        downloadLink.textContent = "DXF";
        downloadLink.className = "btn btn-primary btn-sm"; // Bootstrap button classes for styling
        downloadLink.style.textAlign = "right"; // This pushes the link to the right side
        downloadLink.onclick = (e) => {
          e.stopPropagation(); // Prevent listItem's onclick from firing when the link is clicked
        };

        listItem.appendChild(downloadLink);

        list.appendChild(listItem);
      });

      break;
    default:
      DisplayMessage(gelen.Command, gelen.Data);
      break;
  }
};

window.onload = function () {
  console.log("loaded");
};

function DisplayMessage(Class, Message) {
  const li = document.createElement("li");

  li.classList.add("list-group-item", "p-1", "mb-1", "border-0");
  switch (Class) {
    case "Success":
      li.classList.add("list-group-item-success");
      break;
    case "Warning":
      li.classList.add("list-group-item-warning");
      break;
    case "Error":
      li.classList.add("list-group-item-danger");
      break;
    case "Info":
      li.classList.add("list-group-item-secondary");
      break;
    case "Primary":
      li.classList.add("list-group-item-primary");
      break;
  }
  const messageText = document.createTextNode(Message);
  li.appendChild(messageText);
  MessageList = document.getElementById("MessageList");
  MessageList.appendChild(li);
  MessageList.scrollTop = MessageList.scrollHeight;
}

function uploadDXF() {
  const formData = new FormData();
  document.getElementById("LoadingScreenDiv").style.display = "block";
  const dxfInput = document.getElementById("dxf-input");
  const file = dxfInput.files[0];
  console.log(WSID);
  formData.append("sessionToken", WSID);
  formData.append("file", file);

  fetch("/upload", {
    method: "POST",
    body: formData,
  })
    .then((response) => response.text())
    .catch((error) => {
      console.error("Error:", error);
    });
}

function uploadPoly() {
  const formData = new FormData();
  const polyInput = document.getElementById("Poly-input");
  const file = polyInput.files[0];
  formData.append("sessionToken", WSID);
  formData.append("file", file);

  fetch("/uploadpoly", {
    method: "POST",
    body: formData,
  })
    .then((response) => response.text())
    .catch((error) => {
      console.error("Error:", error);
    });
}

function uploadCFG() {
  const formData = new FormData();
  document.getElementById("LoadingScreenDiv").style.display = "block";
  const cfgInput = document.getElementById("CFG-input");
  console.log(cfgInput.files);
  formData.append("sessionToken", WSID);
  for (let file = 0; file < cfgInput.files.length; file++) {
    formData.append("cfgInput[]", cfgInput.files[file]);
  }
  fetch("/uploadCFG", {
    method: "POST",
    body: formData,
  })
    .then((response) => response.text())
    .catch((error) => {
      console.error("Error:", error);
    });
}

function uploadObject() {
  const formData = new FormData();
  document.getElementById("LoadingScreenDiv").style.display = "block";
  const ObjInput = document.getElementById("Obj-input");
  console.log(ObjInput.files);
  formData.append("sessionToken", WSID);
  for (let file = 0; file < ObjInput.files.length; file++) {
    formData.append("ObjInput[]", ObjInput.files[file]);
  }
  fetch("/uploadObj", {
    method: "POST",
    body: formData,
  })
    .then((response) => response.text())
    .catch((error) => {
      console.error("Error:", error);
    });
}

function updateStatus(message) {
  document.getElementById("status-panel").textContent = message;
}
