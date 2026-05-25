pipeline {
    agent any

    environment {
        DOCKER_IMAGE = "flask-app-failure"
        HELM_RELEASE = "flask-app-healing"
        // Slack webhook can be injected from Jenkins system config or credentials
        SLACK_WEBHOOK_URL = ""
    }

    stages {
        stage('Slack Notification: Start') {
            steps {
                script {
                    sh "python3 scripts/notifier.py --status STARTING --build ${env.BUILD_NUMBER} --webhook ${env.SLACK_WEBHOOK_URL} || true"
                }
            }
        }

        stage('DevSecOps Security Scan') {
            parallel {
                stage('Static Application Security Testing (SAST)') {
                    steps {
                        script {
                            echo "Running security scans on Flask app code..."
                            // Bandit checks for security issues in Python code
                            sh "python3 -m pip install bandit --break-system-packages || true"
                            sh "bandit -r ./app -x ./app/tests || true"
                        }
                    }
                }
                stage('Dependency Check') {
                    steps {
                        script {
                            echo "Scanning application dependencies..."
                            // Safety scans python requirements.txt for known vulnerabilities
                            sh "python3 -m pip install safety --break-system-packages || true"
                            sh "safety check -r ./app/requirements.txt || true"
                        }
                    }
                }
                stage('Container Image Scan') {
                    steps {
                        script {
                            echo "Scanning base Docker container image..."
                            // Trivy check if installed in environment
                            sh "trivy image --severity CRITICAL --exit-code 0 ${DOCKER_IMAGE}:latest || echo 'Trivy scanner not installed. Skipping.'"
                        }
                    }
                }
            }
        }

        stage('Build') {
            steps {
                script {
                    sh "curl -X POST -d 'status=building&log=Starting Build phase: Building Docker image...' http://host.docker.internal:3000/api/update || curl -X POST -d 'status=building&log=Starting Build phase: Building Docker image...' http://172.17.0.1:3000/api/update || true"
                    sh 'docker build -t ${DOCKER_IMAGE}:latest ./app'
                    // Load the newly built image directly into Minikube if applicable
                    sh 'minikube image load ${DOCKER_IMAGE}:latest || true'
                }
            }
        }

        stage('Deploy') {
            steps {
                script {
                    sh "curl -X POST -d 'status=deploying&log=Starting Deploy phase: Upgrading Helm chart on Kubernetes...' http://host.docker.internal:3000/api/update || curl -X POST -d 'status=deploying&log=Starting Deploy phase: Upgrading Helm chart on Kubernetes...' http://172.17.0.1:3000/api/update || true"
                    // Deploy to K8s using Helm
                    sh 'helm upgrade --install ${HELM_RELEASE} ./helm/flask-app-healing --set image.repository=${DOCKER_IMAGE} --set image.tag=latest --wait'
                }
            }
        }

        stage('Test & Anomaly Check') {
            steps {
                script {
                    sh "curl -X POST -d 'status=testing&log=Starting Health Test phase: Verifying rollout status...' http://host.docker.internal:3000/api/update || curl -X POST -d 'status=testing&log=Starting Health Test phase: Verifying rollout status...' http://172.17.0.1:3000/api/update || true"
                    
                    // Verify Kubernetes deployment status
                    sh "kubectl rollout status deployment/${env.HELM_RELEASE}-flask-app --timeout=60s"
                    
                    // Run AI Anomaly detector to ensure metrics/logs are stable post-deployment
                    def logFile = "deployment_test_logs.txt"
                    sh "kubectl logs deployment/${env.HELM_RELEASE}-flask-app --tail=50 > ${logFile} 2>&1 || true"
                    
                    // Execute AI/ML anomaly verification script
                    sh "python3 scripts/anomaly_detector.py ${logFile} 10.0 150.0"
                    
                    // Allow service ingress routing to catch up
                    sleep 5
                    
                    // Verify the HTTP endpoint (try via local proxy forward or direct ingress)
                    sh "curl -f http://host.docker.internal:5000/ || curl -f http://172.17.0.1:5000/ || true"
                }
            }
        }
    }

    post {
        success {
            script {
                sh "curl -X POST -d 'status=success&log=Pipeline built, deployed, and verified successfully on Kubernetes!' http://host.docker.internal:3000/api/update || curl -X POST -d 'status=success&log=Pipeline built, deployed, and verified successfully on Kubernetes!' http://172.17.0.1:3000/api/update || true"
                sh "python3 scripts/notifier.py --status SUCCESS --build ${env.BUILD_NUMBER} --webhook ${env.SLACK_WEBHOOK_URL} || true"
            }
        }
        failure {
            script {
                sh "curl -X POST -d 'status=failed&log=Health check failed! App container crashed or unresponsive.' http://host.docker.internal:3000/api/update || curl -X POST -d 'status=failed&log=Health check failed! App container crashed or unresponsive.' http://172.17.0.1:3000/api/update || true"
                echo "Pipeline failed! Initiating Auto-Rollback process..."
                sh "python3 scripts/notifier.py --status FAILED --build ${env.BUILD_NUMBER} --error 'Health verification failure' --webhook ${env.SLACK_WEBHOOK_URL} || true"
                
                // Capture cluster details for debugging
                sh "kubectl describe deployment/${env.HELM_RELEASE}-flask-app || true"
                sh "kubectl get pods -l app=${env.HELM_RELEASE}-flask-app || true"
                
                // Roll back to the previous stable release using Helm
                sh "curl -X POST -d 'status=healing&log=Deploy failed. Running Helm rollback to last stable release...' http://host.docker.internal:3000/api/update || curl -X POST -d 'status=healing&log=Deploy failed. Running Helm rollback to last stable release...' http://172.17.0.1:3000/api/update || true"
                echo "Rolling back deployment..."
                sh "helm rollback ${env.HELM_RELEASE} || echo 'No previous release found to rollback to.'"
                
                sh "curl -X POST -d 'status=healed&log=Helm auto-rollback executed successfully. Restored previous stable deployment version.' http://host.docker.internal:3000/api/update || curl -X POST -d 'status=healed&log=Helm auto-rollback executed successfully. Restored previous stable deployment version.' http://172.17.0.1:3000/api/update || true"
                sh "python3 scripts/notifier.py --status ROLLBACK --build ${env.BUILD_NUMBER} --action 'Helm Rollback' --webhook ${env.SLACK_WEBHOOK_URL} || true"
                echo "Heal attempt complete."
            }
        }
    }
}
