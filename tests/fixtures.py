import base64
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import threading
import time
import struct
import zlib

def png_chunk(tag, data):
    return struct.pack('>I',len(data))+tag+data+struct.pack('>I',zlib.crc32(tag+data)&0xffffffff)


# A complete 1x1 RGB PNG with independently constructed chunks and valid CRCs.
PNG = (b'\x89PNG\r\n\x1a\n' + png_chunk(b'IHDR',struct.pack('>IIBBBBB',1,1,8,2,0,0,0))
       + png_chunk(b'IDAT',zlib.compress(b'\x00\xff\x80\x20')) + png_chunk(b'IEND',b''))


@contextmanager
def api_server(mode='b64'):
    state = {'posts': [], 'gets': [], 'mode': mode}
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def reply(self, status, body, content_type='application/json'):
            if not isinstance(body, bytes):
                body = json.dumps(body).encode()
            self.send_response(status)
            self.send_header('Content-Type', content_type)
            self.send_header('Content-Length', str(len(body)))
            self.end_headers()
            try:
                self.wfile.write(body)
            except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
                pass

        def do_GET(self):
            state['gets'].append((self.path, self.headers.get('Authorization')))
            if self.path == '/v1/models':
                self.reply(200, {'data':[{'id':'gpt-image-2'}, {'id':'other-model'}]})
            elif self.path.split('?')[0] == '/picture.png':
                self.reply(200, PNG, 'image/png')
            elif self.path == '/redirect':
                self.send_response(302)
                self.send_header('Location', 'http://evil.example/image.png')
                self.end_headers()
            else:
                self.reply(404, {})

        def do_POST(self):
            payload = json.loads(self.rfile.read(int(self.headers.get('Content-Length', '0'))))
            state['posts'].append((self.path, self.headers.get('Authorization'), payload))
            mode = state['mode']
            if mode == '401':
                self.reply(401, {'error':'DO-NOT-LEAK local-test-key'})
            elif mode == 'disconnect':
                self.close_connection = True
            elif mode == 'slow':
                time.sleep(1.3)
                self.reply(200, {'data':[{'b64_json':base64.b64encode(PNG).decode()}]})
            elif mode in ('url', 'signed', 'redirect'):
                tail = '/picture.png' if mode == 'url' else '/redirect'
                if mode == 'signed':
                    tail = '/picture.png?signature=test-only&expires=123'
                self.reply(200, {'data':[{'url':state['base'].removesuffix('/v1') + tail}]})
            elif mode == 'bad':
                self.reply(200, {'data':[{'b64_json':base64.b64encode(b'not-an-image').decode()}]})
            elif mode == 'forged':
                forged = b'\x89PNG\r\n\x1a\n' + struct.pack('>I',13)+b'IHDR'+struct.pack('>II',1,1)+b'junkIENDjunk'
                self.reply(200, {'data':[{'b64_json':base64.b64encode(forged).decode()}]})
            elif mode == 'missing_url':
                self.reply(200, {'data':[{'url':state['base'].removesuffix('/v1') + '/missing.png'}]})
            elif mode == 'empty':
                self.reply(200, {'data':[]})
            elif mode == 'invalid_json':
                self.reply(200, b'not-json')
            else:
                self.reply(200, {'created':123, 'data':[{'b64_json':base64.b64encode(PNG).decode()}]})
    server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
    state['base'] = 'http://127.0.0.1:%d/v1' % server.server_address[1]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield state
    finally:
        server.shutdown()
        server.server_close()
        thread.join()
