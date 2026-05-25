# ☸️ Kubernetes Self-Healing & Scaling Testing Guide

This guide describes how to verify and test the self-healing, scaling, and routing behaviors of the application deployed in Kubernetes.

---

## 1. Prerequisites & Addons Setup

Before testing HPA (Horizontal Pod Autoscaling) and Ingress, ensure that the corresponding Kubernetes addons are enabled on your local cluster (Minikube).

### Enable Metrics Server (Required for HPA)
```powershell
minikube addons enable metrics-server
```
*Wait 1–2 minutes for the metrics server to initialize. Verify it works with:*
```powershell
kubectl top pods
```

### Enable Ingress Controller
```powershell
minikube addons enable ingress
```
*Verify that the Ingress controller pods are running in the ingress-nginx namespace:*
```powershell
kubectl get pods -n ingress-nginx
```

### Enable Kubernetes Dashboard
```powershell
minikube dashboard
```
*This command will open a web browser tab displaying your cluster resources, events, and restart histories.*

---

## 2. Verify Auto-Healing (Liveness Probe)

Kubernetes automatically restarts containers if the application crashes or becomes completely unresponsive.

1.  **Watch the pods list in real-time**:
    ```powershell
    kubectl get pods -l app=flask-app-healing -w
    ```
2.  **Trigger a container crash**:
    You can trigger this by calling the `/simulate/crash` endpoint:
    ```powershell
    # Get the service IP or port-forward the pod:
    kubectl port-forward service/flask-app-healing 5000:5000
    
    # In another terminal, run:
    curl http://localhost:5000/simulate/crash
    ```
    *Alternatively, kill the container process inside the pod directly:*
    ```powershell
    kubectl exec -it deployment/flask-app-healing -- kill 1
    ```
3.  **Observe the result**:
    *   The pod status will change from `Running` $\rightarrow$ `Error` $\rightarrow$ `CrashLoopBackOff` $\rightarrow$ `Running`.
    *   The `RESTARTS` count of the pod will increment by 1.
    *   Kubernetes-native self-healing recovers the pod without manual intervention.

---

## 3. Verify Traffic Routing (Readiness Probe)

Readiness probes determine whether the pod is ready to accept traffic. If a pod is slow or degraded, Kubernetes temporarily removes it from the service endpoint pool so users do not experience errors.

1.  **Trigger high latency**:
    Call the `/simulate/latency` endpoint:
    ```powershell
    curl http://localhost:5000/simulate/latency
    ```
2.  **Check pod readiness**:
    ```powershell
    kubectl get pods -l app=flask-app-healing
    ```
    *   The pod's `READY` status changes from `1/1` to `0/1`.
    *   The service stops routing incoming requests to this pod until the latency period completes (10 seconds) and the readiness probe returns healthy.

---

## 4. Test Auto-Scaling (HPA)

The Horizontal Pod Autoscaler scales pod replicas up or down based on CPU metrics gathered by the metrics server.

1.  **Monitor the HPA state**:
    ```powershell
    kubectl get hpa -w
    ```
2.  **Generate artificial CPU stress**:
    Exec into one of the running pods:
    ```powershell
    kubectl exec -it deployment/flask-app-healing -- /bin/sh
    ```
    *Inside the pod's shell, run:*
    ```sh
    # Install stress tool
    apt-get update && apt-get install -y stress-ng
    
    # Run CPU intensive tasks for 2 minutes
    stress-ng --cpu 2 --timeout 120s
    ```
3.  **Observe scaling behavior**:
    *   The HPA CPU percentage will rise.
    *   Once utilization exceeds the threshold (80%), the deployment will scale replicas from `2` up to `3`, `4`, or `5` dynamically.
    *   Once stress-ng stops, cooldown policies will slowly scale down replicas back to the baseline count of `2`.

---

## 5. Verify Ingress Routing

1.  **Get the IP address of your Minikube cluster**:
    ```powershell
    minikube ip
    ```
2.  **Configure hosts file** (optional, to use the domain name):
    Add the host record to your system host file (e.g. `C:\Windows\System32\drivers\etc\hosts` on Windows):
    ```
    <minikube-ip>  flask-app.local
    ```
3.  **Access the web app**:
    Open a web browser and navigate to `http://flask-app.local` or run:
    ```powershell
    curl http://<minikube-ip>/
    ```

---

## 6. Deploy and Test Prometheus & Grafana Monitoring

Use the lightweight monitoring manifests to deploy visual analytics dashboards.

### Deploy the Monitoring Manifests
Run the following command in the repository root directory:
```powershell
kubectl apply -f kubernetes/monitoring/
```
Verify that the prometheus and grafana pods are running:
```powershell
kubectl get pods -w
```

### Access Prometheus UI
To open the Prometheus expression browser interface locally:
```powershell
kubectl port-forward svc/prometheus 9090:9090
```
Open `http://localhost:9090` in your web browser. You can query target metrics such as:
*   `up`
*   `container_cpu_usage_seconds_total`

### Access Grafana Dashboards
To open the Grafana monitoring dashboard interface:
```powershell
kubectl port-forward svc/grafana 3000:3000
```
1.  Open `http://localhost:3000` in your web browser.
2.  Log in using credentials `admin` / `admin` (or click skip since anonymous admin access is configured as default).
3.  Prometheus is already provisioned as the default datasource.
4.  Create a new Dashboard $\rightarrow$ Add an empty panel:
    *   **CPU Monitor Query**: `sum(rate(container_cpu_usage_seconds_total{container="flask-app"}[1m])) by (pod)`
    *   **Memory Monitor Query**: `sum(container_memory_working_set_bytes{container="flask-app"}) by (pod)`
    *   **Restart Tracker Query**: `kube_pod_container_status_restarts_total{container="flask-app"}` (Scraped if using kube-state-metrics) or track container state restarts from cAdvisor container metrics: `changes(container_last_seen{container="flask-app"}[1h])`
