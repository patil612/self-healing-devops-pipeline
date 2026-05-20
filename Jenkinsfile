pipeline {
    agent any

    environment {
        DOCKER_IMAGE = "flask-app-failure"
        CONTAINER_NAME = "flask-app-failure"
    }

    stages {
        stage('Build') {
            steps {
                script {
                    sh "curl -X POST -d 'status=building&log=Starting Build phase: Building Docker image...' http://host.docker.internal:3000/api/update || curl -X POST -d 'status=building&log=Starting Build phase: Building Docker image...' http://172.17.0.1:3000/api/update || true"
                    sh 'docker build -t ${DOCKER_IMAGE} ./app'
                }
            }
        }

        stage('Deploy') {
            steps {
                script {
                    sh "curl -X POST -d 'status=deploying&log=Starting Deploy phase: Stopping old container and starting new one...' http://host.docker.internal:3000/api/update || curl -X POST -d 'status=deploying&log=Starting Deploy phase: Stopping old container and starting new one...' http://172.17.0.1:3000/api/update || true"
                    // Check if container exists and remove it (forcefully)
                    sh "docker rm -f ${CONTAINER_NAME} || true"
                    // Run the container
                    sh "docker run -d -p 5000:5000 --name ${CONTAINER_NAME} ${DOCKER_IMAGE}"
                }
            }
        }

        stage('Test') {
            steps {
                script {
                    sh "curl -X POST -d 'status=testing&log=Starting Health Test phase: Pinging Flask app container...' http://host.docker.internal:3000/api/update || curl -X POST -d 'status=testing&log=Starting Health Test phase: Pinging Flask app container...' http://172.17.0.1:3000/api/update || true"
                    // Give it a moment to start
                    sleep 5
                    // Simple health check
                    sh "curl -f http://host.docker.internal:5000/ || curl -f http://172.17.0.1:5000/"
                }
            }
        }
    }

    post {
        success {
            script {
                sh "curl -X POST -d 'status=success&log=Pipeline built, deployed, and tested successfully! App is healthy.' http://host.docker.internal:3000/api/update || curl -X POST -d 'status=success&log=Pipeline built, deployed, and tested successfully! App is healthy.' http://172.17.0.1:3000/api/update || true"
            }
        }
        failure {
            script {
                sh "curl -X POST -d 'status=failed&log=Health check failed! App container crashed or unresponsive.' http://host.docker.internal:3000/api/update || curl -X POST -d 'status=failed&log=Health check failed! App container crashed or unresponsive.' http://172.17.0.1:3000/api/update || true"
                echo "Pipeline failed! Initiating Self-Healing process..."
                
                // 1. Capture Logs
                def logFile = "failure_log.txt"
                sh "docker logs ${CONTAINER_NAME} > ${logFile} 2>&1"
                
                // 2. Analyze Logs
                def analyzerOutput = sh(script: "python3 scripts/log_analyzer.py ${logFile}", returnStdout: true).trim()
                echo "Analyzer Output: ${analyzerOutput}"
                
                // Extract recommendation
                def recommendation = ""
                try {
                    recommendation = analyzerOutput.split("RECOMMENDATION: ")[1]
                } catch(Exception e) {
                    echo "Could not parse recommendation: ${e.message}"
                }
                
                if (recommendation && recommendation != "None") {
                    sh "curl -X POST -d 'status=healing&log=Analyzing logs... Recommendation: ${recommendation}. Running Ansible playbook...' http://host.docker.internal:3000/api/update || curl -X POST -d 'status=healing&log=Analyzing logs... Recommendation: ${recommendation}. Running Ansible playbook...' http://172.17.0.1:3000/api/update || true"
                    echo "Applying fix: ${recommendation}"
                    
                    // 3. Run Ansible Playbook
                    sh "ansible-playbook -i ansible/inventory ansible/playbooks/${recommendation}"
                    
                    sh "curl -X POST -d 'status=healed&log=Ansible healing playbook executed successfully. Container restarted!' http://host.docker.internal:3000/api/update || curl -X POST -d 'status=healed&log=Ansible healing playbook executed successfully. Container restarted!' http://172.17.0.1:3000/api/update || true"
                    echo "Heal attempt complete. Please re-run the job to verify fix."
                } else {
                    sh "curl -X POST -d 'status=failed&log=Logs analyzed but no automated healing playbook was found.' http://host.docker.internal:3000/api/update || curl -X POST -d 'status=failed&log=Logs analyzed but no automated healing playbook was found.' http://172.17.0.1:3000/api/update || true"
                    echo "No automated fix found."
                }
            }
        }
    }
}

