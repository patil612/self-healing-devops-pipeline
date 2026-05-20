# Self-Healing DevOps Pipeline

This project demonstrates a self-healing pipeline using **Jenkins**, **Docker**, **Ansible**, and **Python**. When the application fails (crash, missing dependency, etc.), the pipeline detects the error pattern and automatically triggers an Ansible playbook to fix it.

## Architecture

1.  **Application (Flask)**: Simulates failures via endpoints.
2.  **Jenkins**: Orchestrates the Build -> Deploy -> Test pipeline.
3.  **Log Analyzer (Python)**: Parses failure logs to identify the root cause.
4.  **Ansible**: Executes remediation playbooks based on the analyzer's recommendation.

## Quick Start

1.  **Start Infrastructure**:
    ```bash
    docker-compose up -d --build
    ```
2.  **Access Jenkins**:
    - URL: [http://localhost:8080](http://localhost:8080)
    - Unlock Jenkins using the initial admin password found in logs:
      ```bash
      docker logs jenkins
      ```
    - Install recommended plugins.
3.  **Create Pipeline Job**:
    - New Item -> Pipeline -> Name: `self-healing-demo`.
    - Definition: `Pipeline script from SCM`.
    - SCM: `Git`.
    - Repository URL: `https://github.com/Start-Automating/Self-Healing-DevOps-Pipeline-Three-Tier-Architecture.git` (or local path).
    - Script Path: `Jenkinsfile`.
4.  **Trigger Failure**:
    - Modify the `Jenkinsfile` or app code to hit a failure endpoint.
    - Watch the "Post Actions" stage automatically heal the app!

## Simulated Failures

- **Crash**: Application exits with code 1. -> Fix: Restart Container.
- **Missing Dependency**: Import error. -> Fix: Install requirements and restart.
- **Latency**: Timeout. -> Fix: Restart Container (simulated fix).
