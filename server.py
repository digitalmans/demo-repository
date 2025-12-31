import http.server
import socketserver
import os

PORT = 721
directory = os.path.dirname(os.path.abspath(__file__))

class MyHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=directory, **kwargs)

print(f"Starting server at http://localhost:{PORT}")
print(f"Serving files from: {directory}")

with socketserver.TCPServer(("", PORT), MyHTTPRequestHandler) as httpd:
    try:
        print("Server is running. Press Ctrl+C to stop.")
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped.")
        httpd.server_close()