In this project python 3.8.10 is used
# pipenv shell
or if you want another python version
# pipenv shell --python 3.8   

# pyinstaller ipcam_ws_app.py --onefile -w
# pyinstaller scale_ws_app.py --onefile -w


# pyinstaller ipcam_and_scale_app.py --onefile -w --add-binary dist\ipcam_ws_app.exe:. --add-binary dist\scale_ws_app.exe:.

to create service application
# pyinstaller --onefile --hidden-import win32timezone main.py --name ipcam_and_scale_service_tool --add-binary dist\ipcam_ws_app.exe:. --add-binary dist\scale_ws_app.exe:.