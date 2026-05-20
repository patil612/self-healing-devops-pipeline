import sys
import re

def analyze_log(log_path):
    """
    Analyzes the log file for known error patterns and returns a recommended playbook.
    """
    recommended_playbook = None
    
    try:
        with open(log_path, 'r') as f:
            content = f.read()
            
            # Pattern 1: Missing Dependency
            if "ModuleNotFoundError" in content or "ImportError" in content:
                print("Detected: Missing Dependency")
                recommended_playbook = "heal_dependency.yml"
                
            # Pattern 2: Service Crash / Critical Error
            elif "CRITICAL: Application crasing" in content or "sys.exit(1)" in content or "exited with code 1" in content:
                print("Detected: Service Crash")
                recommended_playbook = "heal_service.yml"
                
            # Pattern 3: High Latency / Timeout (Simulated)
            elif "WARNING: endpoint experiencing high latency" in content or "Response delayed" in content:
                print("Detected: Performance Issue")
                recommended_playbook = "heal_service.yml" # Restart might fix it
            
            # Default
            else:
                print("No specific failure pattern detected.")
                
    except FileNotFoundError:
        print(f"Error: Log file not found at {log_path}")
        sys.exit(1)
        
    return recommended_playbook

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python log_analyzer.py <path_to_log_file>")
        sys.exit(1)
        
    log_file = sys.argv[1]
    playbook = analyze_log(log_file)
    
    if playbook:
        print(f"RECOMMENDATION: {playbook}")
        # In a real scenario, this script might trigger Ansible directly or output a machine-readable format
        # For Jenkins, we can capture this output.
    else:
        print("RECOMMENDATION: None")
