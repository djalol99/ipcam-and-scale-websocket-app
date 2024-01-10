from simple_websocket_server import WebSocketServer, WebSocket
from serial import Serial, SerialException
import sys


CLOSE = 0
CONNECT = 1


class ScaleWebSocket(WebSocket):
    com_port = None
    protocol = "A9"
    ws_server = None
    _reset = True

    def handle(self):
        msg = int(self.data)
        if msg == CLOSE:
            self.close_ws_server()
        elif msg == CONNECT:
            self.connect_to_scale()
        else:
            self.send_data()

    def connected(self):
        pass

    def handle_close(self):
        pass

    # custom methods
    def send_data(self):
        if self.ws_server.serial_conn.is_open:
            self.read_data_from_scale()
            self.send_message(self._weight)
        else:
            self.close()

    def connect_to_scale(self):
        try:
            if self.ws_server.serial_conn is None:
                self.ws_server.serial_conn = Serial('COM' + self.com_port)
                self.ws_server.not_connected = False
                self.read_data_from_scale()
            elif not self.ws_server.serial_conn.is_open:
                self.ws_server.serial_conn.open()
                self.read_data_from_scale()

            self.send_data()
        except SerialException as ex:
            self.close()

    def close_ws_server(self):
        self.ws_server.serial_conn and self.ws_server.serial_conn.is_open and self.ws_server.serial_conn.close()
        self.ws_server.stop_server()

    def read_data_from_scale(self):
        try:
            if self._reset:
                self.ws_server.serial_conn.reset_input_buffer()

            SOF = "02"
            EOF = "03"
            # FIND START OF FRAME
            while self.ws_server.serial_conn.read().hex() != SOF:
                continue
            # RECORD UNTIL END OF FRAME
            data = bytes()
            while True:
                temp = self.ws_server.serial_conn.read()
                if temp.hex() == EOF:
                    break
                else:
                    data += temp
            self._weight = self.get_weight(data.decode("utf-8"))
        except SerialException:
            self.ws_server.serial_conn.is_open = False
            self.close()

    def get_weight(self, data):
        try:
            if self.protocol == "A9":
                decimal = int(data[7])
                return str(round(int(data[:7]) * 10**(-decimal), decimal))
            else:
                return data
        except:
            return "0"


if __name__ == "__main__":
    host = '127.0.0.1'
    port = None
    com_port = None
    timeout = 1000
    for param in sys.argv:
        key_val = param.split("=")
        if key_val[0] == "host":
            host = key_val[1]
        elif key_val[0] == "port":
            port = key_val[1]
        elif key_val[0] == "comport":
            com_port = key_val[1]
        elif key_val[0] == "protocol":
            ScaleWebSocket.protocol = key_val[1]
        elif key_val[0] == "timeout":
            timeout = int(key_val[1])

    if host and port and com_port:
        ScaleWebSocket.com_port = com_port
        try:
            WebSocketServer.serial_conn = None
            server = WebSocketServer(host, port, ScaleWebSocket)
            ScaleWebSocket.ws_server = server
            server.serve_forever(timeout=timeout)
        except OSError:
            pass
