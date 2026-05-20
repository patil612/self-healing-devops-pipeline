Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "STARTING SELF-HEALING DEVOPS PIPELINE DEMO" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan

# 1. Start Docker Backend
Write-Host "[1/4] Starting Docker Desktop Backend..." -ForegroundColor Yellow
$DockerProcess = Start-Process -FilePath "C:\Program Files\Docker\Docker\resources\com.docker.backend.exe" -WorkingDirectory "C:\Program Files\Docker\Docker\resources" -PassThru -WindowStyle Hidden

# 2. Wait for Docker to become active
Write-Host "[2/4] Waiting for Docker API to become responsive..." -ForegroundColor Yellow
$Timeout = 90
$Started = $false
for ($i = 1; $i -le $Timeout; $i++) {
    docker ps >$null 2>&1
    if ($LASTEXITCODE -eq 0) {
        $Started = $true
        Write-Host "`nDocker is up and running! (Initialized in $i seconds)" -ForegroundColor Green
        break
    }
    Write-Host -NoNewline "."
    Start-Sleep -Seconds 1
}

if (-not $Started) {
    Write-Error "Docker failed to start within $Timeout seconds."
    exit 1
}

# 3. Check and Start Jenkins via Docker Compose
Write-Host "`n[3/4] Running docker-compose to ensure Jenkins is up..." -ForegroundColor Yellow
docker-compose up -d --build

Write-Host "`nChecking running containers:" -ForegroundColor Green
docker ps

# 4. Verify Jenkins Job Config
Write-Host "`n[4/4] Verifying Jenkins job config inside container..." -ForegroundColor Yellow
docker exec jenkins ls -l /var/jenkins_home/jobs/self-healing-demo

Write-Host "`nLocal Git Repository Status:" -ForegroundColor Green
git status

Write-Host "`n=========================================" -ForegroundColor Cyan
Write-Host "DEMO SETUP COMPLETED SUCCESSFULLY!" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan
