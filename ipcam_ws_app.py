from simple_websocket_server import WebSocketServer, WebSocket
import time, sys

from threading import Thread
from urllib.parse import urljoin
import requests
from requests.auth import HTTPBasicAuth, HTTPDigestAuth
from requests.exceptions import ConnectionError, HTTPError, ReadTimeout
import xmltodict, json


class Client:
    image_queue_size = 5
    time_interval_pictures = 0.05
    _spend_time_for_picture = 1 # updated on each request to image

    def __init__(self, host: str, username: str = None, password: str = None):
        """
        :param host: Host for device ('http://192.168.0.2')
        :param username: (optional) username for device
        :param password: (optional) Password for device
        :param timeout: (optional) Timeout for request
        """
        self.host = host
        self.username = username
        self.password = password
        self.session = self._check_session()
        self.stream = False
        self.pictures = []
        self.events = []

    def _check_session(self):
        """Check the connection with device

         :return request.session() object
        """
        full_url = urljoin(self.host, '/ISAPI/System/status')
        session = requests.session()
        session.auth = HTTPBasicAuth(self.username, self.password)
        response = session.get(full_url)
        if response.status_code == 401:
            session.auth = HTTPDigestAuth(self.username, self.password)
            response = session.get(full_url)
        response.raise_for_status()
        return session

    def get_events(self, timeout=30):
        url = urljoin(self.host, "/ISAPI/Event/notification/alertStream")
        try:
            while self.stream:
                response = self.session.request("get", url, timeout=timeout, stream=True)
                for chunk in response.iter_lines(chunk_size=1024, delimiter=b'--boundary'):
                    if not self.stream:
                        break
                    if chunk:
                        chunks = chunk.split(b'\r\n\r\n')
                        if len(chunks) < 2:
                            continue
                        try:
                            data = xmltodict.parse(chunks[1].decode("utf-8"))
                            if data['EventNotificationAlert']['eventType'] == "ANPR":
                                self.events.append(json.dumps(data))
                                break
                        except AttributeError:
                            pass
        except ConnectionError:
            self.stream = False

    def get_pictures(self, width=640, height=360, timeout=3):
        url = urljoin(self.host, f"/ISAPI/Streaming/channels/101/picture?videoResolutionWidth={width}&videoResolutionHeight={height}")
        try:
            while self.stream:
                start_request = time.time()
                response = self.session.request("get", url, timeout=timeout, stream=True)
                end_request = time.time()
                self._spend_time_for_picture = end_request - start_request
                if len(self.pictures) >= self.image_queue_size:
                    time.sleep(self.time_interval_pictures)
                    continue
                self.pictures.append(response.content)
                time.sleep(self.time_interval_pictures)
        except ConnectionError:
            self.stream = False

    def get_spend_time_to_img(self):
        return self._spend_time_for_picture + self.time_interval_pictures

class ScaleWebSocket(WebSocket):
    ws_server = None
    ipcam = None
    username = None
    password = None
    anpr = False

    def handle(self):
        time.sleep(self._client.get_spend_time_to_img())
        self._send()

    def connected(self):
        self._client = None    
        tries = 3
        while tries:
            try:
                self._client = Client(host="http://" + self.ipcam, username=self.username, password=self.password)
                self._client.stream = True
                self.ws_server.not_connected = False
                break
            except ReadTimeout:
                tries -= 1
                continue
            except (ConnectionError, HTTPError):
                break

        if self._client is None or not self._client.stream:
            self.ws_server.stop_server()
            return

        thread_pictures = Thread(target=self._client.get_pictures, args=())
        thread_pictures.daemon = True
        thread_pictures.start()

        if self.anpr:
            thread_events = Thread(target=self._client.get_events, args=())
            thread_events.daemon = True
            thread_events.start()

        while self._client.stream:
            if len(self._client.pictures) or (self.anpr and len(self._client.events)):
                self._send()
                break
            time.sleep(0.2)    

    def handle_close(self):
        if self._client:
            self._client.stream = False
        self.ws_server.stop_server()

    def _send(self):
        if self._client.stream:
            if len(self._client.pictures):
                self._img_bytes = self._client.pictures.pop(0)
            self.send_message(self._img_bytes)
            if self.anpr and len(self._client.events):
                self.send_message(self._client.events.pop(0))
        else:
            self.close()
            self.ws_server.stop_server()


if __name__ == "__main__":
    host = '127.0.0.1'
    port = None
    ipcam = None
    username = None
    password = None
    anpr = False
    timeout = 100

    for param in sys.argv:
        key_val = param.split("=")
        if key_val[0] == "host":
            host = key_val[1]
        elif key_val[0] == "port":
            port = key_val[1]
        elif key_val[0] == "ipcam":
            ipcam = key_val[1]
        elif key_val[0] == "username":
            username = key_val[1]
        elif key_val[0] == "password":
            password = key_val[1]
        elif key_val[0] == "anpr":
            anpr = bool(int(key_val[1]))
        elif key_val[0] == "timeout":
            timeout = int(key_val[1])
        elif key_val[0] == "image_queue_size":
            Client.image_queue_size = int(key_val[1])
        elif key_val[0] == "time_interval_pictures":
            Client.time_interval_pictures = float(key_val[1])

    if host and port and ipcam and username and password:
        ScaleWebSocket.ipcam = ipcam
        ScaleWebSocket.username = username
        ScaleWebSocket.password = password
        ScaleWebSocket.anpr = anpr
        try:
            server = WebSocketServer(host, port, ScaleWebSocket)
            ScaleWebSocket.ws_server = server
            server.serve_forever(timeout=timeout)
        except OSError:
            pass
