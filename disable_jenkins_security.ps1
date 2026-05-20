Write-Host "Disabling security in Jenkins container..."
docker exec jenkins sed -i "s/<useSecurity>true<\/useSecurity>/<useSecurity>false<\/useSecurity>/g" /var/jenkins_home/config.xml

Write-Host "Restarting Jenkins container..."
docker restart jenkins

Write-Host "Jenkins is restarting. You can refresh http://localhost:8080 in a few seconds and you will be logged in automatically without a password!"
