import http.server
import socketserver
import os
import threading
import webbrowser
import time

PORT = 3000
DIRECTORY = os.path.dirname(os.path.abspath(__file__))

class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)

    def log_message(self, format, *args):
        print("[Frontend] %s - %s" % (self.address_string(), format % args))

def open_browser():
    time.sleep(1.2)
    webbrowser.open("http://localhost:" + str(PORT))

if __name__ == "__main__":
    t = threading.Thread(target=open_browser, daemon=True)
    t.start()
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        print("Frontend serving at http://localhost:" + str(PORT))
        httpd.serve_forever()
