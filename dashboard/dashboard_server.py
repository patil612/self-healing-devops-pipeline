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

# Load environment credentials from .env file
def load_env():
    env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, val = line.split('=', 1)
                    os.environ[key.strip()] = val.strip()

load_env()
db_url = os.environ.get('DATABASE_URL')

# Fail-safe database connection fetcher
def get_db_connection():
    if not db_url or "aws_rds_endpoint" in db_url or "<aws_rds_endpoint>" in db_url:
        return None
    try:
        # Parse connection URL
        match = re.match(r'postgresql://([^:]+):([^@]+)@([^:]+):(\d+)/(.+)', db_url)
        if not match:
            match = re.match(r'postgresql://([^:]+):([^@]+)@([^/]+)/(.+)', db_url)
            if not match:
                return None
            username, password, host, dbname = match.groups()
            port = 5432
        else:
            username, password, host, port, dbname = match.groups()
            port = int(port)
            
        try:
            import psycopg2
            return psycopg2.connect(dbname=dbname, user=username, password=password, host=host, port=port)
        except ImportError:
            try:
                import pg8000
                return pg8000.dbapi.connect(database=dbname, user=username, password=password, host=host, port=port)
            except ImportError:
                return None
    except Exception:
        return None

# Database operation helper functions
def db_create_build(build_num, status):
    conn = get_db_connection()
    if not conn:
        return
    try:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO builds (build_number, status, started_at) VALUES (%s, %s, CURRENT_TIMESTAMP) "
            "ON CONFLICT (build_number) DO UPDATE SET status = EXCLUDED.status", 
            (build_num, status)
        )
        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"Database write error (create_build): {e}")

def db_update_build(build_num, status):
    conn = get_db_connection()
    if not conn:
        return
    try:
        cursor = conn.cursor()
        cursor.execute("UPDATE builds SET status = %s, ended_at = CURRENT_TIMESTAMP WHERE build_number = %s", (status, build_num))
        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"Database write error (update_build): {e}")

def db_add_log(build_num, severity, message):
    conn = get_db_connection()
    if not conn:
        return
    try:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO log_repository (build_number, severity, message, timestamp) "
            "VALUES (%s, %s, %s, CURRENT_TIMESTAMP)", 
            (build_num, severity, message)
        )
        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"Database write error (add_log): {e}")

def db_add_healing_audit(build_num, error_msg, playbook, status):
    conn = get_db_connection()
    if not conn:
        return
    try:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO healing_audits (build_number, detected_error, recommended_playbook, execution_status, executed_at) "
            "VALUES (%s, %s, %s, %s, CURRENT_TIMESTAMP)", 
            (build_num, error_msg, playbook, status)
        )
        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"Database write error (healing_audit): {e}")

def db_load_history():
    conn = get_db_connection()
    if not conn:
        return None
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT build_number, status, started_at FROM builds ORDER BY build_number DESC LIMIT 20")
        rows = cursor.fetchall()
        history = []
        for r in rows:
            history.append({
                "build_num": r[0],
                "time": str(r[2]),
                "result": r[1],
                "journey": [r[1].capitalize()]
            })
        cursor.close()
        conn.close()
        return history
    except Exception as e:
        print(f"Database read error (load_history): {e}")
        return None

# Global memory state (Fallback)
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
    match = re.search(r'(?:github\.com/|git@github\.com[:/])?([^/]+)/([^/.]+)(?:\.git)?$', url)
    if match:
        username = match.group(1)
        repo = match.group(2)
        return username, repo
    return None, None

def update_push_script(username, repo):
    try:
        script_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'push_to_github.ps1')
        if os.path.exists(script_path):
            with open(script_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            content = re.sub(r'\$REPO_NAME\s*=\s*"[^"]*"', f'$REPO_NAME = "{repo}"', content)
            content = re.sub(r'\$GITHUB_USERNAME\s*=\s*"[^"]*"', f'$GITHUB_USERNAME = "{username}"', content)
            
            with open(script_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"Updated push_to_github.ps1 with username={username}, repo={repo}")
    except Exception as e:
        print(f"Error updating push_to_github.ps1: {e}")

def update_jenkins_config(new_url):
    try:
        cmd = f'docker exec jenkins sed -i "s|<url>.*</url>|<url>{new_url}</url>|g" /var/jenkins_home/jobs/self-healing-demo/config.xml'
        subprocess.run(cmd, shell=True, check=True)
        print(f"Updated Jenkins job config with URL: {new_url}")
        
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
            
            # Sync local dashboard state history from AWS RDS database if connected
            db_history = db_load_history()
            if db_history is not None:
                state["build_history"] = db_history
                if db_history:
                    state["build_number"] = max(state["build_number"], max(h["build_num"] for h in db_history))
            
            self.wfile.write(json.dumps(state).encode('utf-8'))
        else:
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

                # Parse logging severity
                severity = "INFO"
                if new_status in ["failed"]:
                    severity = "ERROR"
                elif new_status in ["healing", "healed", "rollback"]:
                    severity = "WARNING"

                # ---- Build history tracking ----
                if new_status == "building":
                    state["build_number"] += 1
                    state["current_journey"] = ["Building"]
                    db_create_build(state["build_number"], new_status)

                elif new_status == "deploying":
                    if "Deploying" not in state["current_journey"]:
                        state["current_journey"].append("Deploying")
                    db_create_build(state["build_number"], new_status)

                elif new_status == "testing":
                    if "Testing" not in state["current_journey"]:
                        state["current_journey"].append("Testing")
                    db_create_build(state["build_number"], new_status)

                elif new_status == "failed":
                    if "Failed" not in state["current_journey"]:
                        state["current_journey"].append("Failed")
                    db_create_build(state["build_number"], new_status)

                elif new_status == "healing":
                    if "Healing" not in state["current_journey"]:
                        state["current_journey"].append("Healing")
                    db_create_build(state["build_number"], new_status)
                    
                    # Log recovery incident start
                    playbook = "heal_service.yml"
                    if "heal_dependency.yml" in log_msg:
                        playbook = "heal_dependency.yml"
                    db_add_healing_audit(state["build_number"], log_msg, playbook, "IN_PROGRESS")

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
                    db_update_build(state["build_number"], new_status)
                    
                    # Update recovery audit as success
                    playbook = "heal_service.yml"
                    if "heal_dependency.yml" in log_msg:
                        playbook = "heal_dependency.yml"
                    db_add_healing_audit(state["build_number"], log_msg, playbook, "SUCCESS")

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
                    db_update_build(state["build_number"], new_status)
                # --------------------------------

                if new_status == "success" or new_status == "healed":
                    state["app_status"] = "healthy"
                elif new_status == "failed":
                    state["app_status"] = "crashed"

                if log_msg:
                    state["logs"].append(f"[{state['last_update']}] {log_msg}")
                    state["logs"] = state["logs"][-30:]
                    db_add_log(state["build_number"], severity, log_msg)

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
    load_current_repo_url()
    
    checker_thread = threading.Thread(target=flask_health_checker, daemon=True)
    checker_thread.start()

    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    
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
