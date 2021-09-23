import json
import socket
import re
from jsonconfig import JsonConfig

class Request:
    """
    HTTP Request from Client
    """

    def __init__(self, first_line, content_type, raw_content):
        self.method       = None
        self.path         = None
        self._raw_content = raw_content

        print("First-Line:", first_line)

        match = re.match('([^ ]+) +([^ ]+) ', first_line.decode())
        if match:
            self.method = match.group(1)
            self.path   = match.group(2)

    def match(self, method, path):
        return self.method == method and self.path == path

    @property
    def dict_data(self):
        return json.loads(self._raw_content)


class ConfigServer:
    """
    Small HTTP Server to update JsonConfig
    """

    def __init__(self, json_config):
        self._config = json_config
        self._addr   = socket.getaddrinfo('0.0.0.0', 80)[0][-1]
        self._sock   = socket.socket()

        self._sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._sock.bind(self._addr)
        self._sock.listen(1)
        print('listening on', self._addr)

    def serv(self):
        while True:
            client, addr = self._sock.accept()
            print('client connected from', addr)

            try:
                req = self.get_request_from_client(client)
                self.handle_request(client, req)
                client.close()
            except OSError as e:
                client.close()
                print('Connection closed with OSError')

    def close(self):
        self._sock.close()

    def handle_request(self, client, req):
        top = '/www/index.html'

        if req.match('GET', '/'):
            print("GET /")
            self.send_file(client, top)

        elif req.match('GET', '/config/settings.json'):
            print("GET /config/settings.json")
            self.send_file(client, '/config/settings.json')

        elif req.match('POST', '/config/settings'):
            print("POST /config/settings")
            print("DATA:", req.dict_data)

            config = JsonConfig(name = 'settings')
            config.dict.update(req.dict_data)
            config.save()
            self.send_file(client, top, code = '201 Created', append = 'Location: /')

        else:
            print("Not Found")
            self.send_file(client, '/www/404.html', code = '404 Not Found')

    def send_file(self, client, path, code = '200 OK', append = None):
        _HTTP_HEADER = 'HTTP/1.0 %s\r\nConnection: Close\r\nContent-Type: %s\r\n'

        if path.endswith('.json'):
            ct = 'application/json'
        else:
            ct = 'text/html'

        client.send(_HTTP_HEADER % (code, ct))

        if append:
            client.send(append + '\r\n')
        client.send('\r\n')

        try:
            with open(path, 'r') as file:
                while True:
                    s = file.read(512)
                    if len(s) <= 0:
                        break
                    client.send(s)
        except:
            pass

    def get_request_from_client(self, client):
        client.settimeout(4.0)
        fd = client.makefile('rwb', 0)

        content_length = 0
        content_type = None
        first_line = fd.readline()

        while True:
            line = fd.readline()

            if not line or line == b'\r\n':
                break

            match = re.match('Content-Length: *(\d+)', line.decode())
            if match:
                content_length = int(match.group(1))

            match = re.match('Content-Type: *([^ ]+)', line.decode())
            if match:
                content_type = match.group(1)

        data = client.read(content_length) if content_length > 0 else None
        client.settimeout(None)
        return Request(first_line, content_type, data)
