# https://oxylabs.io/blog/python-script-service-guide docs
import servicemanager
import socket
import sys
import win32event
import win32service
import win32serviceutil

import ipcam_and_scale_app


# <<< Windows Service
class IPCamAndScale(win32serviceutil.ServiceFramework):
    _svc_name_ = "ipcam_scale_ws_app" #Service Name (exe)
    _svc_display_name_ = "IP Camera and Weight Scale data reader" #Service Name which will display in the Winfows Services Window 
    _svc_description_ = "IP Camera streaming with ANPR function and Weight Scale data reader through com port" #Service Name which will display in the Winfows Services Window
    #Custom properties
    host = "127.0.0.1"
    port = 7000

    def __init__(self, *args):
        '''
        Used to initialize the service utility. 
        '''
        super().__init__(*args)
        self.hWaitStop = win32event.CreateEvent(None, 0, 0, None)
        socket.setdefaulttimeout(60)

    def SvcStop(self):
        '''
        Used to stop the service utility (restart / timeout / shutdown)
        '''
        ipcam_and_scale_app.stop_server(self.host, self.port)
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        win32event.SetEvent(self.hWaitStop)

    def SvcDoRun(self):
        '''
        Used to execute all the piece of code that you want service to perform.
        '''
        ipcam_and_scale_app.run_server(self.host, self.port)
        
# >>> Windows Service


if __name__ == '__main__':

    for index, param in enumerate(sys.argv):
        key_val = param.split("=")
        if key_val[0] == "host":
            IPCamAndScale.host = key_val[1]
        elif key_val[0] == "port":
            IPCamAndScale.port = int(key_val[1])

    if len(sys.argv) == 1:
        servicemanager.Initialize()
        servicemanager.PrepareToHostSingle(IPCamAndScale)
        servicemanager.StartServiceCtrlDispatcher()
    else:
        win32serviceutil.HandleCommandLine(IPCamAndScale)
