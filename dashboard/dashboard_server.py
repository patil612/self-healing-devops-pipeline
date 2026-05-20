import http.server
import socketserver
import json
import urllib.request
import threading
import time
import os
import sys

PORT = 3000

# Global state
state = {
    "pipeline_status": "idle", # idle, building, deploying, testing, failed, healing, healed, success
    "app_status": "checking",   # healthy, crashed, checking
    "last_update": "",
    "logs": []
}

# Thread to periodically check Flask app health
def flask_health_checker():
    global state
    while True:
        # Only check health if we are not in the middle of deploying/building
        if state["pipeline_status"] not in ["building", "deploying"]:
            try:
                # We request localhost:5000 (Flask app)
                req = urllib.request.Request("http://localhost:5000/", method="GET")
                with urllib.request.urlopen(req, timeout=1.5) as response:
                    if response.status == 200:
                        state["app_status"] = "healthy"
                    else:
                        state["app_status"] = "crashed"
            except Exception:
                state["app_status"] = "crashed"
        else:
            state["app_status"] = "checking"
        
        time.sleep(2)

class DashboardHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        # Allow CORS for easy debugging/local file access
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'X-Requested-With, Content-Type')
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

    def do_GET(self):
        global state
        if self.path == '/api/status':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(state).encode('utf-8'))
        else:
            # Serve index.html or other static files in the dashboard directory
            # Make sure we serve from the correct folder relative to the script location
            script_dir = os.path.dirname(os.path.abspath(__file__))
            os.chdir(script_dir)
            super().do_GET()

    def do_POST(self):
        global state
        if self.path == '/api/update':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length).decode('utf-8')
            
            # Parse form data or JSON
            new_status = ""
            log_msg = ""
            
            try:
                # Try parsing as JSON first
                data = json.loads(post_data)
                new_status = data.get("status", "")
                log_msg = data.get("log", "")
            except json.JSONDecodeError:
                # Fallback to query params parsing (e.g. status=building)
                params = urllib.parse.parse_qs(post_data)
                if "status" in params:
                    new_status = params["status"][0]
                if "log" in params:
                    log_msg = params["log"][0]

            if new_status:
                state["pipeline_status"] = new_status
                state["last_update"] = time.strftime("%Y-%m-%d %H:%M:%S")
                
                # Update app status based on pipeline status
                if new_status == "success" or new_status == "healed":
                    state["app_status"] = "healthy"
                elif new_status == "failed":
                    state["app_status"] = "crashed"

                if log_msg:
                    state["logs"].append(f"[{state['last_update']}] {log_msg}")
                    # Cap logs to last 30 messages
                    state["logs"] = state["logs"][-30:]

                print(f"[{state['last_update']}] Status updated: {new_status} | Logs: {log_msg}")

            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"result": "success", "state": state}).encode('utf-8'))
        else:
            self.send_response(404)
            self.end_headers()

def run():
    # Start health check thread
    checker_thread = threading.Thread(target=flask_health_checker, daemon=True)
    checker_thread.start()

    # Serve files
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    
    # Enable socket re-use to avoid port-in-use errors on restart
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("", PORT), DashboardHTTPRequestHandler) as httpd:
        print(f"Dashboard server started at http://localhost:{PORT}")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down server.")
            sys.exit(0)

if __name__ == '__main__':
    run()
