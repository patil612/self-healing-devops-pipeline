# 🎯 PPT Content — Enterprise Self-Healing Kubernetes Pipeline
### Project Review Presentation (Advanced DevOps Edition)

---

## 🖥️ SLIDE 1 — Title Slide

> **Title:** Advanced Self-Healing DevOps Pipeline
> **Subtitle:** Orchestrating Native Kubernetes Self-Healing, Helm Auto-Rollbacks, & Prometheus-Grafana Monitoring
> **Subject:** DevOps Lab | Graduation Project Review
> **Presented by:** Start-Automating DevOps Team

---

## 📌 SLIDE 2 — Problem Statement & Enterprise Objective

### 🔴 The Challenge in Production
Bare Docker setups lack automatic scaling, container health isolation, and robust deployment recovery.
*   **App Container Crashes**: Downtime occurs if external log tools fail to reboot the process.
*   **Failed Deployments**: Deploying broken updates immediately impacts 100% of incoming user traffic.
*   **Traffic Spikes**: No dynamic scaling causes CPU saturation and slow responses.
*   **Lack of Telemetry**: Troubleshooting relies on reading raw server logs instead of looking at visual metrics.

### 🟢 The Enterprise Solution
Establish a **Self-Healing Kubernetes CI/CD Pipeline** that:
1.  **Orchestrates** deployment using Helm charts.
2.  **Self-Heals Natively** via Kubernetes Liveness & Readiness probes.
3.  **Autoscales** dynamically using the Horizontal Pod Autoscaler (HPA) and Metrics Server.
4.  **Auto-Rolls Back** failed deployments to the last stable release.
5.  **Monitors Metrics** using Prometheus and Grafana dashboards.

---

## 📌 SLIDE 3 — Architecture & Tool Stack

### System Workflow Diagram
```
  [ GitHub Push ]
        │
  [ Jenkins Pipeline ]
        ├── Stage 1: Build & Load Docker Image
        ├── Stage 2: Helm Deploy (helm upgrade --install)
        └── Stage 3: Rollout Verification Check (kubectl rollout status)
                  │
                  ├── SUCCESS ──► Stable Running Pods (Port 5000)
                  │
                  └── FAILURE ──► [ Helm Rollback (helm rollback) ] ──► Restore Last Stable Release
```

### Advanced DevOps Tool Integration

| Tool | Enterprise Role |
| :--- | :--- |
| **Jenkins** | Pipelines build automation and rollback orchestration. |
| **Kubernetes (Minikube)** | Runs, isolates, and manages container state. |
| **Helm** | Declares and rolls back application packages. |
| **Liveness Probe** | Restarts crashed containers automatically. |
| **Readiness Probe** | Isolates latent pods from incoming traffic. |
| **HPA + Metrics Server** | Scales container pods horizontally based on CPU demand. |
| **Prometheus** | Scrapes and stores telemetry metrics. |
| **Grafana** | Visualizes system resource consumption and restarts. |

---

## 📌 SLIDE 4 — CI/CD Pipeline & Auto-Rollback

### Declarative Pipeline Stages (`Jenkinsfile`)
*   **BUILD**: Compiles the code, builds the container image `flask-app-failure:latest`, and imports it directly into the Minikube image cache.
*   **DEPLOY**: Executes `helm upgrade --install` to perform rolling updates with zero downtime.
*   **VERIFY**: Runs `kubectl rollout status` to check if the new pods start successfully.
*   **AUTO-ROLLBACK (Failure Post-Action)**: If verification tests fail, Jenkins captures diagnostic logs and triggers `helm rollback flask-app-healing` to immediately restore the last stable deployment.

---

## 📌 SLIDE 5 — Kubernetes Native Self-Healing

### 1. Liveness Probes (Crash Recovery)
*   **How it works**: Kubernetes periodically pings `/`. If the app fails (e.g. returns a 500 error or doesn't respond), Kubernetes kills the container and starts a new one.
*   **Outcome**: Solves process lockups and crashes without needing external scripts.

### 2. Readiness Probes (Traffic Isolation)
*   **How it works**: Evaluates container health before sending traffic. If the response is slow (e.g. latency spikes on `/simulate/latency`), Kubernetes marks the pod as `Not Ready`.
*   **Outcome**: Users never see error pages or time-out screens because traffic is routed only to active, healthy pods.

---

## 📌 SLIDE 6 — Dynamic Autoscaling (HPA)

### Metrics-Server & Autoscaling Workflow
1.  **Metrics Scraping**: Metrics Server queries CPU and Memory metrics from running pods.
2.  **Resource Limits**: Pods are configured with CPU/Memory request baselines and limits.
3.  **Horizontal Pod Autoscaler (HPA)**:
    *   Tracks CPU utilization against a defined target (e.g. 80%).
    *   If traffic triggers high load, HPA dynamically scales pods up (from 2 up to 5 replicas).
    *   Once load cools down, the cluster scales back down to save infrastructure resources.

---

## 📌 SLIDE 7 — Telemetry & Visual Monitoring

### Prometheus + Grafana Integration
*   **Prometheus**: Acts as the time-series database, scraping resource metrics and liveness checks.
*   **Grafana Dashboards**: 
    *   Visualize CPU and memory patterns.
    *   Track active replica counts and pod restart events.
    *   Show real-time alert firing status.
*   **Alertmanager**: Triggers Slack/Telegram/Email notifications to developers if pods enter a crash loop or hit sustained high CPU limits.

---

## 📌 SLIDE 8 — Presentation & Demo Checklist

Be ready to showcase the following live scenarios during your review:

1.  **Kubernetes Dashboard**: Run `minikube dashboard` to visually show the workload.
2.  **Trigger Crash**: Run `curl` against `/simulate/crash` and show `kubectl get pods -w` outputting the container restart event.
3.  **Trigger Latency**: Run `curl` against `/simulate/latency` and show the pod readiness changing from `1/1` to `0/1`.
4.  **Autoscaling Demo**: Run `stress-ng` inside a pod and watch the replica count scale up in real-time.
5.  **Helm Rollback Demo**: Deploy a broken image and show Jenkins automatically rolling back the release.
