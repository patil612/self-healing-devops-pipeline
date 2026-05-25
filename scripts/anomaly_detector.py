import sys
import os
import re

def analyze_telemetry(log_file, cpu_usage=0.0, mem_usage=0.0):
    """
    Parses application logs and resource metrics to check for anomalous behaviors using
    statistical anomaly scoring.
    """
    print(f"Analyzing system health - CPU: {cpu_usage}%, Memory: {mem_usage}MB")
    
    anomalies_detected = []
    
    # 1. Metric anomaly detection (Z-score heuristic baseline)
    # Define historical mean/std dev for resources under normal conditions
    CPU_MEAN, CPU_STD = 25.0, 15.0
    MEM_MEAN, MEM_STD = 200.0, 50.0
    
    cpu_z = (cpu_usage - CPU_MEAN) / CPU_STD
    mem_z = (mem_usage - MEM_MEAN) / MEM_STD
    
    if cpu_z > 3.0:
        anomalies_detected.append(f"High CPU Anomaly (Z-score: {cpu_z:.2f})")
    if mem_z > 3.0:
        anomalies_detected.append(f"High Memory Anomaly (Z-score: {mem_z:.2f})")
        
    # 2. Log density pattern analysis
    if os.path.exists(log_file):
        with open(log_file, 'r') as f:
            content = f.read()
            
        # Count warning and critical lines
        warnings = len(re.findall(r'WARNING|DEGRADED', content, re.IGNORECASE))
        criticals = len(re.findall(r'CRITICAL|ERROR|FATAL', content, re.IGNORECASE))
        
        print(f"Log Scan Results - Warnings: {warnings}, Criticals: {criticals}")
        
        # Anomaly scoring: high occurrence of warning logs without a crash yet indicates prediction of failure
        if criticals > 0:
            anomalies_detected.append(f"Active Failures (Critical logs: {criticals})")
        elif warnings > 5:
            anomalies_detected.append(f"Log Warning Spikes (Anomaly Warning Density: {warnings})")
            
    # 3. Decision mapping
    if any("Active Failures" in a for a in anomalies_detected):
        print("Anomaly Status: CRITICAL")
        return "CRITICAL_ANOMALY", "heal_service.yml"
    elif len(anomalies_detected) > 0:
        print(f"Anomaly Status: WARNING - Detected: {', '.join(anomalies_detected)}")
        # Predictive self-healing: scale up or proactive restart
        return "PREDICTIVE_WARNING", "heal_service.yml"
    else:
        print("Anomaly Status: NORMAL")
        return "NORMAL", None

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python anomaly_detector.py <log_file> [cpu_usage] [memory_usage]")
        sys.exit(1)
        
    log_path = sys.argv[1]
    cpu = float(sys.argv[2]) if len(sys.argv) > 2 else 15.0
    mem = float(sys.argv[3]) if len(sys.argv) > 3 else 180.0
    
    status, recommendation = analyze_telemetry(log_path, cpu, mem)
    print(f"STATUS: {status}")
    print(f"RECOMMENDATION: {recommendation}")
