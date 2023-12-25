from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import base64, os, tempfile, time, psutil
import uvicorn


MIN_PORT = 7001
MAX_PORT = 7050
next_port = MIN_PORT

app = FastAPI()
origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def port_is_available(port: int) -> int:
    for sconn in psutil.net_connections():
        if sconn.laddr.port == port:
            return False
    return True    

def get_available_port():
    global next_port
    counter = MAX_PORT -  MIN_PORT
    while not port_is_available(next_port):
        if counter:
            counter -= 1
        else:
            return 0
        if next_port < MAX_PORT:
            next_port += 1
        else:
            next_port = MIN_PORT
    return next_port

def atob(value: str) -> str:
    return base64.b64decode(value).decode()

def run_command(command: str) -> None:
    fd, path = tempfile.mkstemp(suffix=".bat")
    try:
        with os.fdopen(fd, 'w') as temp:
            temp.write(command)
    finally:
        os.startfile(path)
        time.sleep(1)
        os.remove(path)

def start_ws_ipcam_app(host: str = "127.0.0.1", 
                       port: int  = None, 
                       ip_address: str = None, 
                       username: str = None, 
                       password: str = None, 
                       anpr: int = 0, # 0 = False and 1 = True
                       timeout: int = 100, 
                       image_queue_size: int = 5, 
                       time_interval_pictures: float = 0.05) -> None:
    path = ".\dist\ipcam_ws_app.exe"
    command = f"start {path} host={host} port={port} ipcam={ip_address} \
        username={username} password={password} anpr={anpr} timeout={timeout} \
        image_queue_size={image_queue_size} time_interval_pictures={time_interval_pictures}"
    run_command(command)
    
def start_ws_scale_app(host: str = "127.0.0.1", port: int = None, comport: str = None, timeout: int = 100) -> None:
    path = ".\dist\scale_ws_app.exe"
    command = f"start {path} host={host} port={port} comport={comport} timeout={timeout}"
    run_command(command)

@app.get("/ipcam")
async def connect_ipcam(ip_address: str, username: str, password: str, anpr: int = 0):
    ip_address = atob(ip_address)
    username = atob(username)
    password = atob(password)
    port = get_available_port()
    if port:
        start_ws_ipcam_app(port=port, ip_address=ip_address, username=username, password=password)
    return port

@app.get("/scale")
async def connect_scale(comport: str):
    port = get_available_port()
    if port:
        start_ws_scale_app(port=port, comport=comport)
    return port

def run_server(host="127.0.0.1", port=7000):
    uvicorn.run(app=app, host=host, port=port, log_config=None)

def stop_server(host="127.0.0.1", port=7000):
    for process in psutil.process_iter():
        connections =  process.connections()
        if len(connections) > 0:
            for conn in connections:
                if conn.laddr.ip == host and conn.laddr.port == port:
                    process.kill()
                    break

if __name__ == "__main__":
    import sys
    port = 7000
    for param in sys.argv:
        key_val = param.split("=")
        if key_val[0] == "port":
            port = int(key_val[1])
    uvicorn.run(app, port=port, log_config=None)