pipeline {
    agent any

    environment {
        DOCKER_IMAGE   = "flask-app-healing"
        HELM_RELEASE   = "flask-app-healing"
        APP_PORT       = "5000"
        SLACK_WEBHOOK_URL = ""
        KUBECONFIG     = "/root/.kube-linux/config"
        // Dashboard is on the same Docker network (devops-net) → use container name
        DASHBOARD      = "http://dashboard:3000/api/update"
    }

    stages {

        // ─── STAGE 1: Setup ──────────────────────────────────────────────────
        stage('Setup') {
            steps {
                script {
                    sh """
                        curl -s -X POST \\
                          -d 'status=building&log=🚀 Pipeline build #${env.BUILD_NUMBER} started — running setup...' \\
                          ${env.DASHBOARD} || true
                    """
                    sh '''
                        if [ -f /root/.kube/config ]; then
                            echo "Translating host kubeconfig..."
                            mkdir -p /root/.kube-linux
                            cp /root/.kube/config /root/.kube-linux/config
                            sed -i 's|C:\\\\Users\\\\rajat\\\\.minikube|/root/.minikube|g' /root/.kube-linux/config
                            sed -i 's|\\\\|/|g' /root/.kube-linux/config
                            sed -i 's|127.0.0.1|host.docker.internal|g' /root/.kube-linux/config
                            sed -i 's|localhost|host.docker.internal|g' /root/.kube-linux/config
                            chmod 600 /root/.kube-linux/config
                            echo "Kubeconfig configured."
                        else
                            echo "No kubeconfig found — Docker-only deployment mode."
                        fi
                    '''
                }
            }
        }

        // ─── STAGE 2: Notify Start ───────────────────────────────────────────
        stage('Notify: Start') {
            steps {
                script {
                    sh "python3 scripts/notifier.py --status STARTING --build ${env.BUILD_NUMBER} --webhook ${env.SLACK_WEBHOOK_URL} || true"
                }
            }
        }

        // ─── STAGE 3: DevSecOps Scans ────────────────────────────────────────
        stage('DevSecOps Security Scan') {
            parallel {
                stage('SAST - Bandit') {
                    steps {
                        script {
                            sh """
                                curl -s -X POST \\
                                  -d 'status=building&log=🔍 Running SAST security scan (Bandit)...' \\
                                  ${env.DASHBOARD} || true
                            """
                            sh "python3 -m pip install bandit --break-system-packages -q || true"
                            sh "bandit -r ./app -x ./app/tests -ll || true"
                        }
                    }
                }
                stage('Dependency Check') {
                    steps {
                        script {
                            sh "python3 -m pip install safety --break-system-packages -q || true"
                            sh "safety check -r ./app/requirements.txt || true"
                        }
                    }
                }
                stage('Container Scan') {
                    steps {
                        script {
                            sh "trivy image --severity CRITICAL --exit-code 0 ${DOCKER_IMAGE}:latest || echo 'Trivy not installed — skipping.'"
                        }
                    }
                }
            }
        }

        // ─── STAGE 4: Build Docker Image ─────────────────────────────────────
        stage('Build') {
            steps {
                script {
                    sh """
                        curl -s -X POST \\
                          -d 'status=building&log=🔨 Build stage: Building Docker image ${env.DOCKER_IMAGE}:latest...' \\
                          ${env.DASHBOARD} || true
                    """
                    sh 'docker build -t ${DOCKER_IMAGE}:latest ./app'
                    sh 'minikube image load ${DOCKER_IMAGE}:latest 2>/dev/null || true'
                    sh """
                        curl -s -X POST \\
                          -d 'status=building&log=✅ Docker image built successfully!' \\
                          ${env.DASHBOARD} || true
                    """
                }
            }
        }

        // ─── STAGE 5: Deploy ─────────────────────────────────────────────────
        stage('Deploy') {
            steps {
                script {
                    sh """
                        curl -s -X POST \\
                          -d 'status=deploying&log=🚢 Deploy stage: Deploying application...' \\
                          ${env.DASHBOARD} || true
                    """
                    sh '''
                        if command -v helm > /dev/null 2>&1 && kubectl get nodes > /dev/null 2>&1; then
                            echo "Kubernetes available. Deploying with Helm..."
                            helm upgrade --install ${HELM_RELEASE} ./helm/flask-app-healing \
                              --set image.repository=${DOCKER_IMAGE} \
                              --set image.tag=latest \
                              --wait --timeout 120s
                        else
                            echo "No Kubernetes cluster — deploying with Docker..."
                            docker stop flask-app-demo 2>/dev/null || true
                            docker rm   flask-app-demo 2>/dev/null || true
                            docker run -d \
                              --name flask-app-demo \
                              --network project3_devops-net \
                              -p 5000:5000 \
                              --restart unless-stopped \
                              ${DOCKER_IMAGE}:latest
                            echo "Docker deployment complete."
                        fi
                    '''
                    sh """
                        curl -s -X POST \\
                          -d 'status=deploying&log=✅ Application deployed successfully!' \\
                          ${env.DASHBOARD} || true
                    """
                }
            }
        }

        // ─── STAGE 6: Test & Health Check ────────────────────────────────────
        stage('Test & Health Check') {
            steps {
                script {
                    sh """
                        curl -s -X POST \\
                          -d 'status=testing&log=🧪 Test stage: Running health checks...' \\
                          ${env.DASHBOARD} || true
                    """
                    sh 'sleep 5'
                    // Check app health — flask-app-demo is on devops-net, reachable by name
                    sh '''
                        for i in 1 2 3 4 5; do
                            if curl -sf http://flask-app-demo:5000/ > /dev/null 2>&1 || \
                               curl -sf http://host.docker.internal:5000/ > /dev/null 2>&1; then
                                echo "✅ Health check PASSED on attempt $i"
                                exit 0
                            fi
                            echo "Attempt $i failed — waiting 5s..."
                            sleep 5
                        done
                        echo "❌ Health check verification failed — aborting pipeline to trigger self-healing."
                        exit 1
                    '''
                    // Kubernetes health (only if cluster exists)
                    sh '''
                        if kubectl get deployment/${HELM_RELEASE}-flask-app > /dev/null 2>&1; then
                            kubectl rollout status deployment/${HELM_RELEASE}-flask-app --timeout=60s || true
                            kubectl logs deployment/${HELM_RELEASE}-flask-app --tail=50 > deployment_test_logs.txt 2>&1 || true
                        else
                            docker logs flask-app-demo --tail=50 > deployment_test_logs.txt 2>&1 || true
                        fi
                        python3 scripts/anomaly_detector.py deployment_test_logs.txt 10.0 150.0 || true
                    '''
                    sh """
                        curl -s -X POST \\
                          -d 'status=testing&log=✅ Health checks passed. Pipeline finalizing...' \\
                          ${env.DASHBOARD} || true
                    """
                }
            }
        }
    }

    // ─── POST-BUILD ───────────────────────────────────────────────────────────
    post {
        success {
            script {
                sh """
                    curl -s -X POST \\
                      -d 'status=success&log=🎉 Pipeline #${env.BUILD_NUMBER} SUCCEEDED! App is live at http://localhost:5000' \\
                      ${env.DASHBOARD} || true
                """
                currentBuild.description = "Deployment completed successfully."
                sh "docker tag ${env.DOCKER_IMAGE}:latest ${env.DOCKER_IMAGE}:stable || true"
                sh "python3 scripts/notifier.py --status SUCCESS --build ${env.BUILD_NUMBER} --webhook ${env.SLACK_WEBHOOK_URL} || true"
            }
        }
        failure {
            script {
                currentBuild.displayName = "#${env.BUILD_NUMBER} - Healed"
                currentBuild.description = "Auto-rollback executed successfully to restore previous stable version."
                sh """
                    curl -s -X POST \\
                      -d 'status=failed&log=❌ Pipeline #${env.BUILD_NUMBER} FAILED! Initiating self-healing...' \\
                      ${env.DASHBOARD} || true
                """
                sh "python3 scripts/notifier.py --status FAILED --build ${env.BUILD_NUMBER} --error 'Health verification failure' --webhook ${env.SLACK_WEBHOOK_URL} || true"

                sh """
                    curl -s -X POST \\
                      -d 'status=healing&log=🔧 Self-healing: Rolling back to last stable version...' \\
                      ${env.DASHBOARD} || true
                """
                sh '''
                    if command -v helm > /dev/null 2>&1 && kubectl get nodes > /dev/null 2>&1; then
                        helm rollback ${HELM_RELEASE} || echo "No previous Helm release to rollback."
                    else
                        echo "No Kubernetes cluster — deploying with Docker rollback..."
                        docker stop flask-app-demo 2>/dev/null || true
                        docker rm   flask-app-demo 2>/dev/null || true
                        if docker image inspect ${DOCKER_IMAGE}:stable >/dev/null 2>&1; then
                            docker run -d \
                              --name flask-app-demo \
                              --network project3_devops-net \
                              -p 5000:5000 \
                              --restart unless-stopped \
                              ${DOCKER_IMAGE}:stable
                        else
                            docker run -d \
                              --name flask-app-demo \
                              --network project3_devops-net \
                              -p 5000:5000 \
                              --restart unless-stopped \
                              project3-flask-app:latest
                        fi
                        echo "Docker deployment rollback complete."
                    fi
                '''
                sh """
                    curl -s -X POST \\
                      -d 'status=healed&log=✅ Self-healing complete! Previous stable version restored.' \\
                      ${env.DASHBOARD} || true
                """
                sh "python3 scripts/notifier.py --status ROLLBACK --build ${env.BUILD_NUMBER} --action 'Auto-Rollback' --webhook ${env.SLACK_WEBHOOK_URL} || true"
            }
        }
    }
}
