"""
A simple proxy server, based on original by gear11:
https://gist.github.com/gear11/8006132
Modified from original to support both GET and POST, status code passthrough, header and form data passthrough.
Usage: http://hostname:port/p/(URL to be proxied, minus protocol)
For example: http://localhost:5000/p/www.google.com
"""
from flask import Flask, render_template, request, abort, Response, redirect, url_for, send_file, flash
import requests
from datetime import datetime
import os

from scripts.utils import *
from scripts.config import Config

base_path=Config.BASE_PATH
app = Flask(__name__,template_folder=Config.TEMPLATES_PATH,static_url_path=base_path+Config.STATIC_URL,instance_path=Config.INSTANCE_PATH)
app.config.from_object(Config)
app.running_streamlits={}

@app.route(base_path+'/file/upload',methods=['POST'])
def upload():
    if request.method == 'POST':
        # check if the post request has the file part
        if 'file' not in request.files or request.files['file'].filename == '':
            return 'No file part'

        file = request.files['file']
        if file:
            if not file.filename.endswith(".py"):
                return 'File must be a Python (.py) file','error'

            path=os.path.join(app.instance_path, file.filename)
            file.save(path)
            flash('File uploaded successfully','success')
            return "ok"

@app.route(base_path+'/delete/<name>')
def delete(name):
    path=os.path.join(app.instance_path, "%s.py"%name)
    if os.path.isfile(path):
        os.remove(path)
        img_path=os.path.join(app.instance_path, 'img', '%s.png'%name)
        if os.path.isfile(img_path):
            os.remove(img_path)
        flash('Deleted application: %s'%name,'success')
    else:
        flash('Application "%s" was not found'%name,'danger')
    return redirect(url_for('home'))

@app.route(base_path+'/serve_img/<name>')
def serve_img(name):
    path=os.path.join(app.instance_path, 'img', '%s.png'%name)
    print(path)
    return send_file(path)

@app.route(base_path+'/create_img/<name>',methods=['POST'])
def create_img(name):
    path=os.path.join(app.instance_path, "%s.py"%name)
    if os.path.isfile(path):
        try:
            #clean_streamlit_processes(app.running_streamlits)
            img_path=get_screenshot(app.instance_path,name)
            flash('Image for application "%s" created successfully'%name,'success')
            return "ok"
        except Exception as e:
            return "Failed to create image: "+str(e)
    return 'App "%s" not found'%name
    #return '<h1>Image saved!</h1><p><a href="%s">Return home</a></p><img src="%s" alt="%s" height="500">'%(url_for('home'),url_for('serve_img',name=name),name)

@app.route(base_path+'/url_exists',methods=['POST'])
def url_exists():
    jsondata=request.json
    if jsondata is not None and 'url' in jsondata:
        url=jsondata['url']
        res = requests.get(url)
        if res.status_code == 200:
            return "ok"
    return "ko"

@app.route(base_path+'/<name>')
def streamlit_show(name=None):
    if name is None:
        return 'Please navigate to the name of the streamlit'
    path=os.path.join(app.instance_path, '%s.py'%name)
    if not os.path.isfile(path):
        return "Streamlit file %s.py doesn't exist"%name

    modified_date=str(os.path.getmtime(path))

    if name in app.running_streamlits and proc_running(app.running_streamlits[name]["proc"]) and modified_date==app.running_streamlits[name]["modified"]:
        app.running_streamlits[name]["last_accessed"]=datetime.now()
        port=app.running_streamlits[name]["port"]
    else:
        proc,port=streamlit_service(path,name,modified_date,app.running_streamlits) #passing name and modified_date to attach to process
        if proc is None:
            return "No ports are available."
        app.running_streamlits[name]={"last_accessed":datetime.now(),
                                    "proc":proc,
                                    "port":port,
                                    "modified":modified_date}

    server_url = "http://"+get_ip()+":"+str(port)
    return render_template('app_view.html',server_url=server_url,name=name)

@app.route(base_path+'/')
def home():
    clean_streamlit_processes(app.running_streamlits)
    #All Streamlits
    streamlits={}
    for file in os.listdir(app.instance_path):
        name=os.path.splitext(file)[0]
        if file.endswith(".py"):
            img_path=path=os.path.join(app.instance_path, 'img', '%s.png'%name)
            img_url=url_for('serve_img',name=name) if os.path.isfile(img_path) else "#"
            streamlits[name]={"img_url":img_url,
                            "create_img_url":url_for('create_img',name=name),
                            "delete_url":url_for('delete',name=name),
                            "file_path":os.path.join(app.instance_path, '%s.py'%name),
                            "running": name in list(app.running_streamlits),
                            "url": url_for('streamlit_show',name=name)}
    return render_template('index.html',apps=streamlits)

if __name__ == "__main__":
    app.run(host=Config.HOST,port=Config.PORT,debug=Config.DEBUG)
