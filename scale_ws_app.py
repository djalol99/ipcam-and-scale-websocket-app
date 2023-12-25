from simple_websocket_server import WebSocketServer, WebSocket
from serial import Serial, SerialException
import time, sys


class ScaleWebSocket(WebSocket):
    com_port = None
    ws_server = None

    def handle(self):
        time.sleep(0.05)
        self.read_data_from_scale()
        if self._serial.is_open:
            self.send_message(self._weight)

    def connected(self):
        self._serial = None
        self.reset = True
        try:
            self._serial =  Serial('COM' + self.com_port)
            self.ws_server.not_connected = False
            for i in range(2):
                self.read_data_from_scale()
            if self._serial.is_open:
                self.send_message(self._weight)
        except SerialException as ex:
            self.close()
            self.ws_server.stop_server()

    def handle_close(self):
        self._serial and self._serial.close()
        self.ws_server.stop_server()

    def read_data_from_scale(self):
        reset = True
        try:
            if reset:
                self._serial.reset_input_buffer()
                
            SOF = "02"
            EOF = "03"
            # FIND START OF FRAME
            while self._serial.read().hex() != SOF:
                continue
            # RECORD UNTIL END OF FRAME
            data = bytes()
            while True:
                temp = self._serial.read()
                if temp.hex() == EOF:
                    break
                else:
                    data += temp
            self._weight = data.decode("utf-8")
        except:
            self._serial.close()
            self.close()
            self.ws_server.stop_server()


if __name__ == "__main__":
    host = '127.0.0.1'
    port = None
    com_port = None
    timeout = 100
    for param in sys.argv:
        key_val = param.split("=")
        if key_val[0] == "host":
            host = key_val[1]
        elif key_val[0] == "port":
            port = key_val[1]
        elif key_val[0] == "comport":
            com_port = key_val[1]
        elif key_val[0] == "timeout":
            timeout = int(key_val[1])


    if host and port and com_port:
        ScaleWebSocket.com_port = com_port
        try:
            server = WebSocketServer(host, port, ScaleWebSocket)
            ScaleWebSocket.ws_server = server
            server.serve_forever(timeout=timeout)
        except OSError:
            pass
