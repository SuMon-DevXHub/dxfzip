from flask import Flask, request, render_template, jsonify
from werkzeug.utils import secure_filename
import os, json
from datetime import datetime
import threading
from PolyExttract import parse_dxf_to_json
from ReadDXF import RestoreFromDXF, RestoreFromDB 
import DXFUtils 
# from DXFUtils import ws, CreateWs, SendMessage
import traceback
import sqlite3


app = Flask(__name__)

lastConnection=1
UPLOAD_FOLDER = 'Upload'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

DXFUtils.ws = DXFUtils.CreateWs()

# Ensure the upload folder exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route('/index2')
def index2():
    return render_template('index2.html')

@app.route('/')
def index():
    return render_template('index.html',base_url=request.url_root)

@app.route('/Projects/<ProjectName>/<Version>')
def Projects(ProjectName,Version):
    return render_template('index.html',PName=ProjectName,PVer=Version,base_url=request.url_root)


@app.route('/uploadCFG', methods=['POST'])
def CFG_upload():
    wsid = request.form.get('sessionToken')
    print("uid", wsid)
    wsclients=[cl for cl in DXFUtils.ws.clients if cl["id"]==int(wsid)]
    if wsclients:
        client=wsclients[0]
    else:
        return jsonify({'message': 'No Websocket client found'})    
    files={"CFG":None, "Pallets":None, "Struct":None}
    if 'cfgInput[]' not in request.files:
        return 'No file part'
    uploaded_files = request.files.getlist("cfgInput[]")
    datetime_stamp = datetime.now().strftime("%Y%m%d%H%M%S")
    for file in uploaded_files:
        filename = secure_filename(file.filename)
        name, ext = os.path.splitext(filename)
        new_filename = f"{name}_{datetime_stamp}{ext}"
        file_path = os.path.join(app.config['UPLOAD_FOLDER']+"//DB", new_filename)        
        if  filename.lower().endswith("cfg.sqlite"):
            file.save(file_path)
            files["CFG"]=file_path
        elif filename.lower().endswith("pallets.sqlite"):
            file.save(file_path)
            files["Pallets"]=file_path 
        elif filename.lower().endswith("struct.sqlite"):
            file.save(file_path)
            files["Struct"]=file_path

    if files["CFG"] or files["Struct"]:
        DXFUtils.SendMessage("Success",f"File Uploaded: {name+ext}",client)
        RestoreFromDB(files,client) 
      
        return jsonify({'message': 'File successfully uploaded'})
    else:
        return jsonify({'message': 'File not successfully uploaded'})

@app.route('/uploadObj', methods=['POST'])
def Obj_upload():
    wsid = request.form.get('sessionToken')
    print("uid", wsid)
    wsclients=[cl for cl in DXFUtils.ws.clients if cl["id"]==int(wsid)]
    if wsclients:
        client=wsclients[0]
    else:
        return jsonify({'message': 'No Websocket client found'})

    if 'ObjInput[]' not in request.files:
        return 'No file part'
    uploaded_files = request.files.getlist("ObjInput[]")
    datetime_stamp = datetime.now().strftime("%Y%m%d%H%M%S")
    for file in uploaded_files:
        filename = secure_filename(file.filename)
        name, ext = os.path.splitext(filename)
        new_filename = f"{name}_{datetime_stamp}{ext}"
        file_path =os.path.join(app.config['UPLOAD_FOLDER']+"//Objects", new_filename)
        file.save(file_path)
        file_path =os.path.join("static//3dobjs//CustomObjects", filename)
        file.seek(0)
        file.save(file_path)
        DXFUtils.SendMessage("Success",f"File Uploaded: {name+ext}",client)     
    return jsonify({'message': 'File not successfully uploaded'})


@app.route('/uploadpoly', methods=['POST'])
def poly_upload():
    wsid = request.form.get('sessionToken')
    print("uid", wsid)
    wsclients=[cl for cl in DXFUtils.ws.clients if cl["id"]==int(wsid)]
    if wsclients:
        client=wsclients[0]
    else:
        return jsonify({'message': 'No Websocket client found'})

    if 'file' not in request.files:
        return 'No file part'
    file = request.files['file']
    datetime_stamp = datetime.now().strftime("%Y%m%d%H%M%S")
    if file.filename == '':
        return 'No selected file'
    if file and file.filename.endswith('.dxf'):
        filename = secure_filename(file.filename)
        name, ext = os.path.splitext(filename)

        # Append datetime to the filename
        new_filename = f"{name}_{datetime_stamp}{ext}"
        file_path = os.path.join(app.config['UPLOAD_FOLDER']+"//Polylines", new_filename)

        file.save(file_path)
        jsonname=os.path.join(app.root_path+ '//static//3dobjs//Polies',name+'.json')
        parse_dxf_to_json(file_path,jsonname)
        DXFUtils.SendMessage("Success",f"File Uploaded: {name+ext}",client)
        return jsonify({'message': 'File successfully uploaded'})


@app.route('/upload', methods=['POST'])
def file_upload():
    wsid = request.form.get('sessionToken')
    print("uid", wsid)
    wsclients=[cl for cl in DXFUtils.ws.clients if cl["id"]==int(wsid)]
    if wsclients:
        client=wsclients[0]
    else:
        return jsonify({'message': 'No Websocket client found'})
    if 'file' not in request.files:
        return 'No file part'
    file = request.files['file']
    if file.filename == '':
        return 'No selected file'
    if file and file.filename.endswith('.dxf'):
        filename = secure_filename(file.filename)
        name, ext = os.path.splitext(filename)

        # Append datetime to the filename
        datetime_stamp = datetime.now().strftime("%Y%m%d%H%M%S")
        new_filename = f"{name}_{datetime_stamp}{ext}"
        file_path = os.path.join(app.config['UPLOAD_FOLDER']+"//Models", new_filename)

        file.save(file_path)
        DXFUtils.SendMessage("Success",f"File Uploaded: {name+ext}",client)
        dbpath=os.path.join(app.root_path+'//static//db') 
        try:       
            RestoreFromDXF(dbpath,file_path,client)
        except Exception as e:
            # Print exception information including line number
            print("An exception occurred: ", traceback.format_exc())            
            DXFUtils.SendMessage("Error","There was a problen at the uploaded file.",client)

        return jsonify({'message': 'File successfully uploaded'})

def NewClientws(client, server):
        DXFUtils.SendMessage("SetWSId",client['id'],client)
        print("New client connected and was given id %d" % client['id'], client['address'] )

def ClientLeftws(client, server):
        print("Client disconnected client[id]:{}  client['address'] ={}  ".format(client["id"], client['address'] ))

def MessageReceivedws(client, server, message):
        Message=json.loads(message)
        if Message["Command"]=="SendProject":
            files={"CFG":f"{app.root_path}//static//db//{Message['Data']['ProjectName']}_V{Message['Data']['Version']}_CFG.sqlite"}
            RestoreFromDB(files,client) 
        elif Message["Command"]=="SendProjectList":
            conn = sqlite3.connect("static//Projects.sqlite")
            crs = conn.cursor()
            crs.execute("SELECT * FROM Projects ORDER BY UpdateTime DESC")
            Projects = crs.fetchall()
            ProjectList=[]
            for p in Projects:
                ProjectList.append({"Code": p[0], "Version":p[1], "Name":p[2], "DB":p[3], "dxf":p[4], "FileTime":p[5]})

            DXFUtils.SendMessage("ProjectList",ProjectList,client)
            # dbpath = os.path.join(app.root_path, 'static', 'db')

            # # List all files and their last modified times in the specified directory
            # file_info = []
            # for filename in os.listdir(dbpath):
            #     if filename!="BaseCFG.sqlite" and filename!="_V_CFG.sqlite":
            #         filepath = os.path.join(dbpath, filename)
            #         modified_time = os.path.getmtime(filepath)
            #         human_readable_time = datetime.fromtimestamp(modified_time).strftime('%Y-%m-%d %H:%M:%S')
            #         file_info.append({"Project":filename.split("_")[0], "Version":filename.split("_")[1][1:], "FileTime":human_readable_time})

            # # dbpath=os.path.join(app.root_path+'//static//db') 

            # # # List all files in the specified directory
            # # file_list = os.listdir(dbpath)
            # # print(file_list)   
            # # obj=[{"Project":x.split("_")[0], "Version":x.split("_")[1][1:]} for x in file_list if x!="BaseCFG.sqlite" and x!="_V_CFG.sqlite"]
                    
            # file_info.sort(key=lambda x: x['FileTime'], reverse=True)
             
            # DXFUtils.SendMessage("DBFileList",file_info,client)

        print("Message Received:",message)


DXFUtils.ws.set_fn_new_client(NewClientws)
DXFUtils.ws.set_fn_client_left(ClientLeftws)
DXFUtils.ws.set_fn_message_received(MessageReceivedws)

if __name__ == '__main__':
    threading.Thread(name="WebSocket",  target=DXFUtils.ws.run_forever, daemon=True).start()
    app.run(host="0.0.0.0", port=8080)
