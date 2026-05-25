import urllib.request
import urllib.parse
import time
import sys

DASHBOARD_URL = "http://localhost:3000/api/update"

def send_update(status, log):
    data = urllib.parse.urlencode({"status": status, "log": log}).encode("utf-8")
    req = urllib.request.Request(DASHBOARD_URL, data=data, method="POST")
    try:
        with urllib.request.urlopen(req) as response:
            response.read()
        print(f"Sent Status Update: [{status}] -> {log}")
    except Exception as e:
        print(f"Failed to send status [{status}]: {e}")

def run_simulation():
    print("====================================================")
    print(" STARTING PIPELINE MONITOR FLOW SIMULATION         ")
    print("====================================================\n")
    
    # --- PHASE 1: Failed Build & Auto-Healing ---
    print(">>> Phase 1: Simulating Build FAILURE & Auto-Healing...")
    send_update("building", "Starting Build phase: Building Docker image...")
    time.sleep(3)
    
    send_update("deploying", "Starting Deploy phase: Upgrading Helm chart on Kubernetes...")
    time.sleep(3)
    
    send_update("testing", "Starting Health Test phase: Verifying rollout status...")
    time.sleep(3)
    
    send_update("failed", "Health check failed! App container crashed or unresponsive.")
    time.sleep(4)
    
    send_update("healing", "Deploy failed. Running Helm rollback to last stable release...")
    time.sleep(4)
    
    send_update("healed", "Helm auto-rollback executed successfully. Restored previous stable deployment version.")
    time.sleep(5)
    
    # --- PHASE 2: Successful Build ---
    print("\n>>> Phase 2: Simulating SUCCESSFUL Pipeline Build...")
    send_update("building", "Starting Build phase: Building Docker image...")
    time.sleep(3)
    
    send_update("deploying", "Deploying stable code to Kubernetes...")
    time.sleep(3)
    
    send_update("testing", "Verifying rollout status of stable release...")
    time.sleep(3)
    
    send_update("success", "Pipeline built, deployed, and verified successfully on Kubernetes!")
    
    print("\n====================================================")
    print(" SIMULATION SUCCESSFULLY COMPLETED!                 ")
    print("====================================================")

if __name__ == "__main__":
    run_simulation()
