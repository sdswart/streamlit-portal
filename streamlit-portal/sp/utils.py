from flask import Flask,request,Response
import socket
from datetime import datetime, timedelta
import psutil
import subprocess
import signal
import os
import requests
import urllib.parse
from selenium import webdriver
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By

from .config import Config

def run_in_terminal(command,new_env=None,return_output=False):
    env = os.environ.copy()
    if new_env is not None:
        env = {**env,**new_env}
    print(command)
    proc=subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,env=env)
    if return_output:
        msg,err=proc.communicate()
        return "MSG: "+str(msg)+"ERR: "+str(err)
        #print("MSG: "+str(msg)+"ERR: "+str(err))
    return proc

def proc_running(proc):
    if hasattr(proc,"poll"):
        return proc.poll() is None
    else:
        return proc.is_running()

def kill_pid(pid):
    print("killing %d..."%pid)
    res = run_in_terminal("taskkill /F /T /PID %s"%str(pid),return_output=True)
    print(res)

def get_screenshot(instance_path,file_name,host):
    path=os.path.join(instance_path, '%s.py'%file_name)
    proc,final_port=streamlit_service(path,host)
    server_url = "http://%s:%d"%(host,final_port)
    pic_path=os.path.join(instance_path, 'img', '%s.png'%file_name)

    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--window-size=1420,1080')
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--disable-gpu')
    with webdriver.Remote(command_executor="http://%s:4444/wd/hub"%host, desired_capabilities=DesiredCapabilities.CHROME, options=chrome_options) as browser:
        browser.get(server_url)
        try:
            element = WebDriverWait(browser, 30).until(
                EC.title_contains(file_name)
            )
        except:
            print("TIMEOUT: first wait")

        finally:
            browser.get_screenshot_as_file(pic_path)
    kill_pid(proc.pid)
    return pic_path

def streamlit_service(path,host_ip,file_name=None,modified=None,running_streamlits=None):
    final_port=None

    if running_streamlits is not None and file_name is not None:
        #Check if process exists in running_streamlits
        if file_name in running_streamlits and "proc" in running_streamlits[file_name]: #process may have stopped or file modified
            if proc_running(running_streamlits[file_name]["proc"]):
                curproc=running_streamlits[file_name]["proc"]
                kill_pid(curproc.pid)
            running_streamlits.pop(file_name, None)

        #Clean streamlit processes to make it easier to find a new port
        clean_streamlit_processes(running_streamlits)
    else:
        running_streamlits={}

    #Look for available ports
    streamlit_ports=[props["port"] for _,props in running_streamlits.items() if "port" in props]
    for port in list(set(Config.PORTS)-set(streamlit_ports)):
        if not port_in_use(port):
            final_port=port
            break

    if final_port is None: #No ports are available
        return None,None

    #command='streamlit run "%s" --server.port %s --server.headless 1 --server.baseUrlPath %s'%(path,str(final_port),Config.BASE_PATH+"/"+file_name+"/")
    command='streamlit run "%s" --server.port %s --server.headless 1  --server.enableCORS false --browser.serverAddress %s'%(path,str(final_port),host_ip)
    my_env = {}
    if modified is not None:
        my_env["MODIFIED"] = modified
    if file_name is not None:
        my_env["STREAMLIT_NAME"] = file_name
    my_env["STREAMLIT_PORT"] = str(final_port)
    proc=run_in_terminal(command,my_env)
    return proc,final_port

def clean_streamlit_processes(running_streamlits):
    #Make sure running_streamlits doesn't include processes that have stopped
    for name in list(running_streamlits):
        if "proc" in running_streamlits[name]:
            if not proc_running(running_streamlits[name]["proc"]):
                running_streamlits.pop(name, None)
            elif running_streamlits[name]["last_accessed"] < (datetime.now()-timedelta(days=5)):
                curproc=running_streamlits[name]["proc"]
                kill_pid(curproc.pid)
                running_streamlits.pop(name, None)

    #Check if there are any streamlits running in background that are not in running_streamlits
    for key,val in find_running_streamlits().items():
        running_streamlits[key]=val

def find_running_streamlits():
    res={}
    for proc in psutil.process_iter():
        try:
            pinfo = proc.as_dict(attrs=['name', 'cmdline'])
            pinfo["ports"]=[]
            for conns in proc.connections(kind='inet'):
                pinfo["ports"].append(conns.laddr.port)
        except psutil.NoSuchProcess:
            pass
        else:
            command=[] if pinfo["cmdline"] is None else pinfo["cmdline"]
            if "streamlit" in command:
                proc_env=proc.environ()
                if "STREAMLIT_NAME" in proc_env and "MODIFIED" in proc_env and "STREAMLIT_PORT" in proc_env:
                    name=proc_env["STREAMLIT_NAME"]
                    res[name]={"port":int(proc_env["STREAMLIT_PORT"]),
                                "proc":proc,
                                "last_accessed":datetime.now(),
                                "modified":proc_env["MODIFIED"]}
                else: #kill it with fire!
                    kill_pid(proc.pid)
    return res

def get_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # doesn't even have to be reachable
        s.connect(('10.255.255.255', 1))
        IP = s.getsockname()[0]
    except:
        IP = '127.0.0.1'
    finally:
        s.close()
    return IP

def port_in_use(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0

def dict_to_html(dictObj, indent=1):
    html= '<ul style="padding-left:%dem">'%(2*indent)
    for k,v in dictObj.items():
        k=str(k);v=str(v)
        if isinstance(v, dict):
            html+='<li>'+ k+ ': '+ '</li>'
            html+=dict_to_html(v, indent+1)
        else:
            html+='<li>'+ k+ ': '+ v+ '</li>'
    html+='</ul>'
    return html
