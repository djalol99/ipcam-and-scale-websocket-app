# import os
# import tempfile
# import time

# command = "start .\ipcam_ws_app.py port=9000 ipcam=192.168.100.45 username=admin password=@1392781"

# fd, path = tempfile.mkstemp(suffix=".bat")
# try:
#     with os.fdopen(fd, 'w') as temp:
#         temp.write(command)
# finally:
#     os.startfile(path)
#     time.sleep(1)
#     os.remove(path)


import psutil

port = 33686
for sconn in psutil.net_connections():
    if sconn.laddr.port == port:
        print(sconn)
