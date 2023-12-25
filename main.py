# https://oxylabs.io/blog/python-script-service-guide docs
import servicemanager
import socket
import sys
import win32event
import win32service
import win32serviceutil

import ipcam_and_scale_app


# <<< Windows Service
class GBSScale(win32serviceutil.ServiceFramework):
    _svc_name_ = "GBSScale" #Service Name (exe)
    _svc_display_name_ = "GBS Scale" #Service Name which will display in the Winfows Services Window 
    _svc_description_ = "Reading data throug serial ports" #Service Name which will display in the Winfows Services Window

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
        ipcam_and_scale_app.stop_server()
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        win32event.SetEvent(self.hWaitStop)

    def SvcDoRun(self):
        '''
        Used to execute all the piece of code that you want service to perform.
        '''
        ipcam_and_scale_app.run_server()
        
# >>> Windows Service


if __name__ == '__main__':
    if len(sys.argv) == 1:
        servicemanager.Initialize()
        servicemanager.PrepareToHostSingle(GBSScale)
        servicemanager.StartServiceCtrlDispatcher()
    else:
        win32serviceutil.HandleCommandLine(GBSScale)
