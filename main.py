import datetime
import mimetypes
from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.parse
import pathlib
import websockets
import asyncio
from threading import Thread
from db import db
import json
from datetime import datetime

HOST = 'localhost'
SERVER_PORT = 3000
WEBSOCKET_PORT = 5000


class MainHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        url = urllib.parse.urlparse(self.path)

        if url.path == '/':
            self.serve_html('index.html')
        elif url.path == '/message':
            self.serve_html('message.html')
        else:
            if pathlib.Path().joinpath('html', url.path[1:]).exists():
                self.serve_static()
            else:
                self.serve_html('error.html', 404)

    def do_POST(self):
        url = urllib.parse.urlparse(self.path)
        if url.path == '/message':
            content_len = int(self.headers.get('Content-Length'))

            post_body = self.rfile.read(content_len)

            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self.send_to_websocket(post_body.decode()))
            loop.close()

            self.serve_html('message.html')

    def prepare_data(self, data):
        data = urllib.parse.parse_qs(data)

        output = {}

        for key in data:
            if len(data[key]) > 0:
                output[key] = data[key][0]

        return json.dumps(output)

    async def send_to_websocket(self, message):
        uri = f"ws://{HOST}:{WEBSOCKET_PORT}"
        data = self.prepare_data(message)
        async with websockets.connect(uri) as websocket:
            await websocket.send(data)
            await websocket.recv()

    def serve_html(self, filename, status=200):
        self.send_response(status)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        with open(f'html/{filename}', 'rb') as f:
            self.wfile.write(f.read())

    def serve_static(self):
        self.send_response(200)
        mt = mimetypes.guess_type(self.path)

        if mt:
            self.send_header('Content-type', mt[0])
        else:
            self.send_header('Content-type', 'text/plain')

        self.end_headers()
        with open(f'html/{self.path}', 'rb') as f:
            self.wfile.write(f.read())


def run_server(server_class=HTTPServer, handler_class=MainHandler):
    server_address = ('', SERVER_PORT)
    http = server_class(server_address, handler_class)
    try:
        http.serve_forever()
    except KeyboardInterrupt:
        http.server_close()


async def socket_handler(websocket):
    data = await websocket.recv()
    data = json.loads(data)
    print('Data received', data)

    data['date'] = datetime.now()

    client = db()
    try:
        client.insert_one(data)
    except Exception as e:
        print('Error saving data:', e)

    reply = f"Data recieved as:  {data}!"
    print(reply)
    await websocket.send(reply)


async def websocket_server():
    async with websockets.serve(socket_handler, 'localhost', WEBSOCKET_PORT) as ws:
        try:
            await asyncio.Future()
        except KeyboardInterrupt:
            ws.close()


def run_websocket():
    asyncio.run(websocket_server())


if __name__ == '__main__':
    t1 = Thread(target=run_server)
    t2 = Thread(target=run_websocket)

    t1.start()
    t2.start()

    t1.join()
    t2.join()
