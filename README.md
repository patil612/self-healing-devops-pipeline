# ☸️ Enterprise-Grade Self-Healing DevSecOps Pipeline

An industry-level, resilient, and secure DevOps pipeline featuring **Kubernetes Native Self-Healing**, **Helm Auto-Rollbacks**, **Prometheus & Grafana Monitoring**, **Loki Centralized Logging**, **Slack Notifications**, **DevSecOps Scans**, and **AI Anomaly Detection**.

---

## 🏗️ System Architecture

```
                                [ GitHub Code Push ]
                                         │
                                [ Jenkins CI/CD ]
                                         ├── DevSecOps Scans (Bandit, Safety, Trivy)
                                         ├── Build Container Image
                                         └── Deploy via Helm (Rolling Updates)
                                                 │
                                                 ├── Rollout Failed ──► [ Helm Auto-Rollback ]
                                                 │
                                                 └── Rollout Passed ──► [ Kubernetes Cluster ]
                                                                                ├── Pods & Ingress Routing
                                                                                ├── Liveness/Readiness Probes (Self-Healing)
                                                                                ├── HPA (Autoscaling)
                                                                                └── telemetry (Prometheus, Grafana, Loki)
```

---

## 🚀 Key Features

*   **Kubernetes Orchestration & Helm**: Declarative deployments using Helm templates with zero-downtime rolling updates.
*   **Auto-Healing**: Kubernetes Liveness Probes monitor pod health and automatically restart crashed containers.
*   **Autoscaling (HPA)**: Pod replica scaling from 2 up to 5 instances based on real-time CPU metric load.
*   **Helm Auto-Rollback**: Jenkins automatically rolls back deployment to the last stable release upon verification failures.
*   **Centralized Telemetry Stack**:
    *   **Prometheus**: Scrapes resource usage metrics and container data.
    *   **Grafana**: Renders real-time graphs showing CPU usage, memory, and restart tracks.
    *   **Grafana Loki & Promtail**: Collects, processes, and streams pod logs centrally.
*   **DevSecOps Shift-Left Security**: Automates static security checks (`Bandit`), dependency audits (`Safety`), and container scanning (`Trivy`) inside the build stages.
*   **AI/ML Anomaly Check**: Runs statistical anomaly evaluation (`scripts/anomaly_detector.py`) post-deployment to flag anomalies.
*   **Real-time Alerts**: Sends rich notification cards to Slack hooks on starts, successes, failures, and rollbacks.

---

## 📂 Project Directory Structure

```
project-root/
├── app/                        # Flask application source code & Dockerfile
├── helm/                       # Helm chart deployment templates
│   └── flask-app-healing/
│       ├── Chart.yaml
│       ├── values.yaml
│       └── templates/          # Deployment, Service, HPA, Ingress
├── kubernetes/
│   └── monitoring/             # Prometheus, Grafana, Loki, & Promtail manifests
├── scripts/                    # Python log analyzers, notifier, & anomaly detector
├── Jenkinsfile                 # Declarative CI/CD pipeline definition
├── PPT_Self_Healing_DevOps.md   # Project presentation slides
└── kubernetes_testing_guide.md # Diagnostic testing manual
```

---

## 🛠️ Setup Instructions

### 1. Start Jenkins Infrastructure
Run the following script to build and launch Jenkins with the Docker socket mounted:
```powershell
./START_EVERYTHING.ps1
```
*   **Jenkins URL**: `http://localhost:8080` (Run `./disable_jenkins_security.ps1` to bypass passwords locally).
*   **Dashboard URL**: `http://localhost:3000`

### 2. Deploy Telemetry Stack
To spin up Prometheus, Grafana, Loki, and Promtail inside your cluster:
```powershell
kubectl apply -f kubernetes/monitoring/
```
Verify the pods are running:
```powershell
kubectl get pods
```

### 3. Setup Port Forwards
Access the visual dashboards locally:
```powershell
# Prometheus
kubectl port-forward svc/prometheus 9090:9090

# Grafana (Credentials: admin / admin)
kubectl port-forward svc/grafana 3000:3000
```

---

## 🧪 Testing Failures & Probes

Refer to the [kubernetes_testing_guide.md](file:///c:/Users/rajat/OneDrive/Desktop/pro/project3/kubernetes_testing_guide.md) for step-by-step commands to test:
1.  **Liveness Probes**: Crashing the pod via `/simulate/crash` and watching restarts.
2.  **Readiness Probes**: Degrading performance via `/simulate/latency` and watching traffic isolation.
3.  **Dynamic Scaling**: Sticking CPU load with `stress-ng` and monitoring replica scaling.
4.  **Auto-Rollback**: Pushing bad code to trigger automatic Helm rollback.
