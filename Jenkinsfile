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
                    sh 'docker build -t ${DOCKER_IMAGE} ./app'
                }
            }
        }

        stage('Deploy') {
            steps {
                script {
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
                    // Give it a moment to start
                    sleep 5
                    // Simple health check
                    sh "curl -f http://host.docker.internal:5000/ || curl -f http://172.17.0.1:5000/"
                }
            }
        }
    }

    post {
        failure {
            script {
                echo "Pipeline failed! Initiating Self-Healing process..."
                
                // 1. Capture Logs
                def logFile = "failure_log.txt"
                sh "docker logs ${CONTAINER_NAME} > ${logFile} 2>&1"
                
                // 2. Analyze Logs
                def analyzerOutput = sh(script: "python3 scripts/log_analyzer.py ${logFile}", returnStdout: true).trim()
                echo "Analyzer Output: ${analyzerOutput}"
                
                // Extract recommendation
                def recommendation = analyzerOutput.split("RECOMMENDATION: ")[1]
                
                if (recommendation && recommendation != "None") {
                    echo "Applying fix: ${recommendation}"
                    
                    // 3. Run Ansible Playbook
                    // We point to the local inventory and the specific playbook
                    sh "ansible-playbook -i ansible/inventory ansible/playbooks/${recommendation}"
                    
                    // 4. Retry the build (Optional: triggering a new build)
                    // In a real pipeline, we might retry the failed stage. 
                    // For this demo, we'll just output that we healed it.
                    echo "Heal attempt complete. Please re-run the job to verify fix."
                } else {
                    echo "No automated fix found."
                }
            }
        }
    }
}
