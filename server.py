import http.server
import json
import threading
import os
from urllib.parse import urlparse, parse_qs

COUNT_FILE = 'count.txt'
TEAMS = ['red', 'blue', 'green', 'yellow']
lock = threading.Lock()

def read_counts():
    if not os.path.exists(COUNT_FILE):
        return {team: 0 for team in TEAMS}
    with open(COUNT_FILE, 'r') as f:
        lines = f.readlines()
    counts = {}
    for line in lines:
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        if '=' in line:
            team, count = line.split('=', 1)
            try:
                counts[team] = int(count)
            except ValueError:
                counts[team] = 0
    for team in TEAMS:
        counts.setdefault(team, 0)
    return counts

def write_counts(counts):
    with open(COUNT_FILE, 'w') as f:
        for team in TEAMS:
            f.write(f'{team}={counts[team]}\n')

class ClickWarHandler(http.server.SimpleHTTPRequestHandler):
    def do_POST(self):
        if self.path == '/api/click':
            try:
                length = int(self.headers.get('Content-Length', 0))
                if length == 0:
                    raise ValueError('No data')
                data = self.rfile.read(length)
                payload = json.loads(data.decode('utf-8'))
                team = payload.get('team')
                if team in TEAMS:
                    with lock:
                        counts = read_counts()
                        counts[team] += 1
                        write_counts(counts)
                    self.send_response(200)
                    self.send_header('Content-Type', 'text/plain')
                    self.end_headers()
                    self.wfile.write(b'OK')
                    return
                else:
                    self.send_response(400)
                    self.send_header('Content-Type', 'text/plain')
                    self.end_headers()
                    self.wfile.write(b'Invalid team')
                    return
            except Exception as e:
                self.send_response(400)
                self.send_header('Content-Type', 'text/plain')
                self.end_headers()
                self.wfile.write(f'Bad Request: {str(e)}'.encode())
        else:
            self.send_response(404)
            self.end_headers()

    def do_GET(self):
        if self.path == '/api/counts':
            with lock:
                counts = read_counts()
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(counts).encode())
        else:
            super().do_GET()

if __name__ == '__main__':
    import socketserver
    PORT = 8000
    Handler = ClickWarHandler
    with socketserver.ThreadingTCPServer(('', PORT), Handler) as httpd:
        print(f'Serving at http://localhost:{PORT}')
        httpd.serve_forever()
