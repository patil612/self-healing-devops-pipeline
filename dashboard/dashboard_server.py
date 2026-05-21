import http.server
import socketserver
import json
import urllib.parse
import urllib.request
import threading
import time
import os
import sys
import re
import subprocess

PORT = 3000

# Global state
state = {
    "pipeline_status": "idle", # idle, building, deploying, testing, failed, healing, healed, success
    "app_status": "checking",   # healthy, crashed, checking
    "repo_url": "https://github.com/patil612/self-healing-devops-pipeline.git",
    "last_update": "",
    "logs": [],
    "build_history": [],        # list of completed build records
    "build_number": 0,          # current build number counter
    "current_journey": []       # phases seen in current build
}

def load_current_repo_url():
    global state
    try:
        cmd = 'docker exec jenkins cat /var/jenkins_home/jobs/self-healing-demo/config.xml'
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            match = re.search(r'<url>(.*?)</url>', result.stdout)
            if match:
                state["repo_url"] = match.group(1)
                print(f"Loaded current repository URL from Jenkins: {state['repo_url']}")
    except Exception as e:
        print(f"Error loading initial repo URL from Jenkins: {e}")

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

def parse_github_url(url):
    url = url.strip()
    # Matches:
    # https://github.com/username/repo.git
    # https://github.com/username/repo
    # github.com/username/repo
    # username/repo
    match = re.search(r'(?:github\.com/|git@github\.com[:/])?([^/]+)/([^/.]+)(?:\.git)?$', url)
    if match:
        username = match.group(1)
        repo = match.group(2)
        return username, repo
    return None, None

def update_push_script(username, repo):
    try:
        script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'push_to_github.ps1')
        if os.path.exists(script_path):
            with open(script_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Replace $REPO_NAME = "..." and $GITHUB_USERNAME = "..."
            content = re.sub(r'\$REPO_NAME\s*=\s*"[^"]*"', f'$REPO_NAME = "{repo}"', content)
            content = re.sub(r'\$GITHUB_USERNAME\s*=\s*"[^"]*"', f'$GITHUB_USERNAME = "{username}"', content)
            
            with open(script_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"Updated push_to_github.ps1 with username={username}, repo={repo}")
    except Exception as e:
        print(f"Error updating push_to_github.ps1: {e}")

def update_jenkins_config(new_url):
    try:
        # Run sed inside the docker container
        cmd = f'docker exec jenkins sed -i "s|<url>.*</url>|<url>{new_url}</url>|g" /var/jenkins_home/jobs/self-healing-demo/config.xml'
        subprocess.run(cmd, shell=True, check=True)
        print(f"Updated Jenkins job config with URL: {new_url}")
        
        # Restart Jenkins container in background thread
        def restart_jenkins():
            print("Restarting Jenkins container to apply new configuration...")
            subprocess.run("docker restart jenkins", shell=True)
            print("Jenkins container restarted.")
            
        threading.Thread(target=restart_jenkins, daemon=True).start()
        return True
    except Exception as e:
        print(f"Error updating Jenkins config: {e}")
        return False

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
            script_dir = os.path.dirname(os.path.abspath(__file__))
            os.chdir(script_dir)
            super().do_GET()

    def do_POST(self):
        global state
        parsed_path = urllib.parse.urlparse(self.path)
        
        if parsed_path.path == '/api/update':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length).decode('utf-8')
            
            new_status = ""
            log_msg = ""
            
            try:
                data = json.loads(post_data)
                new_status = data.get("status", "")
                log_msg = data.get("log", "")
            except json.JSONDecodeError:
                params = urllib.parse.parse_qs(post_data)
                if "status" in params:
                    new_status = params["status"][0]
                if "log" in params:
                    log_msg = params["log"][0]

            if new_status:
                state["pipeline_status"] = new_status
                state["last_update"] = time.strftime("%Y-%m-%d %H:%M:%S")

                # ---- Build history tracking ----
                if new_status == "building":
                    # Start a new build record
                    state["build_number"] += 1
                    state["current_journey"] = ["Building"]

                elif new_status == "deploying":
                    if "Deploying" not in state["current_journey"]:
                        state["current_journey"].append("Deploying")

                elif new_status == "testing":
                    if "Testing" not in state["current_journey"]:
                        state["current_journey"].append("Testing")

                elif new_status == "failed":
                    if "Failed" not in state["current_journey"]:
                        state["current_journey"].append("Failed")

                elif new_status == "healing":
                    if "Healing" not in state["current_journey"]:
                        state["current_journey"].append("Healing")

                elif new_status == "healed":
                    if "Healed" not in state["current_journey"]:
                        state["current_journey"].append("Healed")
                    # Finalise build record
                    state["build_history"].insert(0, {
                        "build_num": state["build_number"],
                        "time": state["last_update"],
                        "result": "healed",
                        "journey": list(state["current_journey"])
                    })
                    state["build_history"] = state["build_history"][:20]

                elif new_status == "success":
                    if "Success" not in state["current_journey"]:
                        state["current_journey"].append("Success")
                    # Finalise build record
                    state["build_history"].insert(0, {
                        "build_num": state["build_number"],
                        "time": state["last_update"],
                        "result": "success",
                        "journey": list(state["current_journey"])
                    })
                    state["build_history"] = state["build_history"][:20]
                # --------------------------------

                if new_status == "success" or new_status == "healed":
                    state["app_status"] = "healthy"
                elif new_status == "failed":
                    state["app_status"] = "crashed"

                if log_msg:
                    state["logs"].append(f"[{state['last_update']}] {log_msg}")
                    state["logs"] = state["logs"][-30:]

                print(f"[{state['last_update']}] Status updated: {new_status} | Logs: {log_msg}")

            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"result": "success", "state": state}).encode('utf-8'))
            
        elif parsed_path.path == '/api/set-repo':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length).decode('utf-8')
            
            new_url = ""
            try:
                data = json.loads(post_data)
                new_url = data.get("url", "").strip()
            except json.JSONDecodeError:
                params = urllib.parse.parse_qs(post_data)
                if "url" in params:
                    new_url = params["url"][0].strip()

            if not new_url:
                self.send_response(400)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"error": "Missing URL parameter"}).encode('utf-8'))
                return

            # Append .git extension if not present for clean GitHub formatting
            if not new_url.endswith('.git') and 'github.com' in new_url:
                new_url = new_url + '.git'

            username, repo = parse_github_url(new_url)
            if not username or not repo:
                self.send_response(400)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"error": "Invalid GitHub repository format"}).encode('utf-8'))
                return

            print(f"Updating repository configuration. Username: {username}, Repo: {repo}")
            
            # Apply configurations
            success = update_jenkins_config(new_url)
            if success:
                update_push_script(username, repo)
                state["repo_url"] = new_url
                state["logs"].append(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Repository changed to: {new_url} (Jenkins restarting)")
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"result": "success", "repo_url": new_url}).encode('utf-8'))
            else:
                self.send_response(500)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"error": "Failed to update Jenkins configuration"}).encode('utf-8'))
        else:
            self.send_response(404)
            self.end_headers()

def run():
    # Load current configuration from Jenkins container if running
    load_current_repo_url()
    
    # Start health check thread
    checker_thread = threading.Thread(target=flask_health_checker, daemon=True)
    checker_thread.start()

    # Serve files
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    
    # Enable socket re-use
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
