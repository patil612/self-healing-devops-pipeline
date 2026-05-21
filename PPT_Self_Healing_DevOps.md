# 🎯 PPT Content — Self-Healing DevOps Pipeline
### Project Review Presentation

---

## 🖥️ SLIDE 1 — Title Slide

> **Title:** Self-Healing DevOps Pipeline
> **Subtitle:** Automated Failure Detection & Remediation using Jenkins, Docker, Ansible & Python
> **Subject:** DevOps Lab | Project Review

---

## 📌 SLIDE 2 — Problem Statement & Objective

### 🔴 Problem Statement
In modern software systems, applications face failures like **crashes, missing dependencies, and high latency**. These require **manual intervention** — which is slow, error-prone, and costly.

**Pain Points:**
- App containers crash → system goes down
- Dependency errors go unnoticed until users report them
- Manual log reading & fixing takes hours
- No automatic recovery in traditional pipelines

### 🟢 Objective
Build a **Self-Healing CI/CD Pipeline** that:
1. **Detects** failures automatically via log analysis
2. **Diagnoses** root cause using a Python Log Analyzer
3. **Remediates** automatically using Ansible Playbooks
4. **Notifies** the dashboard with real-time status

> **Goal:** Zero manual intervention — the system **heals itself**

---

## 📌 SLIDE 3 — Architecture & Workflow

### Architecture Diagram

```
[ GitHub Code Push ]
        ↓
[ Jenkins Pipeline ]
  Stage 1: BUILD   → docker build ./app
  Stage 2: DEPLOY  → docker run flask-app (port 5000)
  Stage 3: TEST    → curl http://app:5000/ (health check)
        ↓ FAILURE
[ Python Log Analyzer ]
  → Reads docker logs
  → Detects error pattern
  → Outputs: RECOMMENDATION
        ↓
[ Ansible Playbook ]
  → heal_service.yml    (crash/latency → restart container)
  → heal_dependency.yml (missing dep → pip install + restart)
        ↓
[ Dashboard (port 3000) ]
  building → deploying → testing → healed ✅
```

### Tool Integration Table

| Tool | Role |
|------|------|
| **GitHub** | Source code repository |
| **Jenkins** | Orchestrates Build → Deploy → Test → Heal |
| **Docker** | Containerizes Flask app; manages lifecycle |
| **Python** | `log_analyzer.py` detects errors & recommends fix |
| **Ansible** | Executes automated healing playbooks |
| **Flask** | Sample app with simulated failure endpoints |
| **Dashboard** | Real-time monitoring UI (Node.js, port 3000) |

---

## 📌 SLIDE 4 — DevOps Tool Installation & Setup

### GitHub
- Repo: `patil612/self-healing-devops-pipeline`
- Jenkins pulls from GitHub via `Pipeline script from SCM`
- Script path: `Jenkinsfile`

### Jenkins (runs as Docker container)
```yaml
# docker-compose.yml
jenkins:
  build: ./jenkins
  ports: ["8080:8080", "50000:50000"]
  volumes:
    - jenkins_home:/var/jenkins_home
    - /var/run/docker.sock:/var/run/docker.sock  # allows Docker control
  user: root
```
- Accessible at `http://localhost:8080`
- Docker socket mounted → Jenkins can build & run containers

### Docker
- Start everything: `docker-compose up -d --build`
- App container: `flask-app-failure` on **port 5000**
- Jenkins container: on **port 8080**

### Ansible
- Installed inside Jenkins container
- Inventory: `ansible/inventory` (localhost)
- Playbooks in: `ansible/playbooks/`
  - `heal_service.yml` → restarts crashed container
  - `heal_dependency.yml` → pip install + restart

---

## 📌 SLIDE 5 — Pipeline Creation (Jenkinsfile)

**Type:** Declarative Pipeline | **File:** `Jenkinsfile`

### Stage 1 — BUILD
```groovy
sh 'docker build -t flask-app-failure ./app'
```
Builds Docker image from `./app/Dockerfile`

### Stage 2 — DEPLOY
```groovy
sh "docker rm -f flask-app-failure || true"
sh "docker run -d -p 5000:5000 --name flask-app-failure flask-app-failure"
```
Removes old container → starts fresh one on port 5000

### Stage 3 — TEST
```groovy
sleep 5
sh "curl -f http://172.17.0.1:5000/"   // Health check
```
Waits 5s, then pings app. Expected: `{"status": "healthy"}`

### POST — Self-Healing (on Failure)
```
1. Capture logs  →  docker logs flask-app-failure > failure_log.txt
2. Analyze logs  →  python3 scripts/log_analyzer.py failure_log.txt
3. Get fix       →  RECOMMENDATION: heal_service.yml
4. Run Ansible   →  ansible-playbook ansible/playbooks/heal_service.yml
5. App recovers  →  Dashboard: "Healed ✅"
```

---

## 📌 SLIDE 6 — Containerization

### Dockerfile (`app/Dockerfile`)
```dockerfile
FROM python:3.9-slim          # Lightweight Python base image
WORKDIR /app                  # Set working directory
COPY requirements.txt .       # Copy dependency list
RUN pip install --no-cache-dir -r requirements.txt
COPY . .                      # Copy source code
CMD ["python", "app.py"]      # Start Flask app
```

### Flask App — Simulated Endpoints

| Endpoint | Behavior |
|----------|----------|
| `/` | Returns `{"status": "healthy"}` — normal health check |
| `/simulate/crash` | Calls `os._exit(1)` → kills container |
| `/simulate/latency` | Sleeps 10s → simulates slow response |
| `/simulate/missing_dep` | Imports non-existent module → `ModuleNotFoundError` |

### Key Docker Commands
```bash
docker build -t flask-app-failure ./app                                   # Build image
docker run -d -p 5000:5000 --name flask-app-failure flask-app-failure     # Run
docker ps                                                                  # Check running containers
docker logs flask-app-failure                                              # View logs
docker rm -f flask-app-failure                                             # Stop & remove
docker-compose up -d --build                                               # Start full infrastructure
```

---

## 📌 SLIDE 7 — Summary

### Failures Handled Automatically

| Failure | Detection | Auto Fix |
|---------|-----------|----------|
| App Crash | `CRITICAL` in logs | Restart container |
| Missing Dependency | `ModuleNotFoundError` | pip install + restart |
| High Latency | `WARNING: high latency` | Restart container |

### Key Takeaways
- **Jenkins** = Pipeline brain 🧠
- **Docker** = Isolated, reproducible containers 📦
- **Ansible** = Automated fixer 🔧
- **Python** = Smart log detective 🔍
- **GitHub** = Single source of truth 📁

> This pattern is used at **Netflix, Google, Amazon** — systems that self-recover without waking engineers at 3AM! 🚀

### Tips for Presentation
- Be ready to show the **live `docker ps`** command to prove containers are running
- Open `http://localhost:8080` to show Jenkins is configured
- Show the `Jenkinsfile` when explaining the pipeline stages

---

*Presentation prepared for DevOps Lab Project Review — May 2026*
