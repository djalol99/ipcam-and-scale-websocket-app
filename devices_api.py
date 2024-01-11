import os, tempfile, time, psutil
from django.conf import settings


BASE_DIR = settings.BASE_DIR
MIN_PORT = 7001
MAX_PORT = 7050
next_port = MIN_PORT


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
                       ip_address: str = None, 
                       username: str = None, 
                       password: str = None, 
                       anpr: int = 0, # 0 = False and 1 = True
                       timeout: int = 100, 
                       image_queue_size: int = 5, 
                       time_interval_pictures: float = 0.05) -> int:
    port = get_available_port()
    path = os.path.join(BASE_DIR, "devices", "exe", "ipcam_ws_app.exe")
    command = f"start {path} host={host} port={port} ipcam={ip_address} \
        username={username} password={password} anpr={anpr} timeout={timeout} \
        image_queue_size={image_queue_size} time_interval_pictures={time_interval_pictures}"
    run_command(command)
    return port
    
def start_ws_scale_app(host: str = "127.0.0.1", comport: str = None, protocol:str = "A9", timeout: int = 100) -> int:
    '''Currently available protocols: [A9,]'''
    port = get_available_port()
    path = os.path.join(BASE_DIR, "devices", "exe", "scale_ws_app.exe")
    command = f"start {path} host={host} port={port} comport={comport} protocol={protocol} timeout={timeout}"
    run_command(command)
    return port