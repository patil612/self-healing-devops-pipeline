from flask import Flask, jsonify
import sys
import time
import os

app = Flask(__name__)

@app.route('/')
def health_check():
    return jsonify({"status": "healthy", "message": "App is running smoothly"}), 200

@app.route('/simulate/crash')
def simulate_crash():
    # Simulate a critical failure that crashes the application
    print("CRITICAL: Application crasing due to simulated unrecoverable error!", file=sys.stderr)
    os._exit(1)

@app.route('/simulate/latency')
def simulate_latency():
    # Simulate high latency or a hanging process
    print("WARNING: endpoint experiencing high latency...", file=sys.stderr)
    time.sleep(10)
    return jsonify({"status": "degraded", "message": "Response delayed by 10s"}), 200

@app.route('/simulate/missing_dep')
def simulate_missing_dep():
    # Simulate a missing dependency error
    try:
        import non_existent_module
    except ImportError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return jsonify({"error": str(e), "status": "failed"}), 500
    return jsonify({"status": "ok"}), 200

# SIMULATED FAILURE FOR DEMO
import sys
print('CRITICAL: Application crasing due to simulated unrecoverable error!', file=sys.stderr)
os._exit(1)
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
