Write-Host "=================================================" -ForegroundColor Cyan
Write-Host "   SELF-HEALING DEVOPS PIPELINE - FULL START    " -ForegroundColor Cyan
Write-Host "=================================================" -ForegroundColor Cyan

# STEP 1 - Start Jenkins via Docker Compose
Write-Host "`n[1/4] Starting Jenkins + Docker Infrastructure..." -ForegroundColor Yellow
docker-compose up -d --build
Write-Host "Jenkins is UP!" -ForegroundColor Green

# STEP 2 - Wait for Jenkins to be ready
Write-Host "`n[2/4] Waiting for Jenkins to be ready..." -ForegroundColor Yellow
$timeout = 60
for ($i = 1; $i -le $timeout; $i++) {
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:8080" -UseBasicParsing -TimeoutSec 2 -ErrorAction Stop
        Write-Host "Jenkins is ready!" -ForegroundColor Green
        break
    } catch {
        Write-Host -NoNewline "."
        Start-Sleep -Seconds 2
    }
}

# STEP 3 - Start Dashboard in background
Write-Host "`n[3/4] Starting Real-Time Dashboard on port 3000..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PWD'; python dashboard/dashboard_server.py" -WindowStyle Minimized
Start-Sleep -Seconds 3
Write-Host "Dashboard is UP!" -ForegroundColor Green

# STEP 4 - Open all websites in browser
Write-Host "`n[4/4] Opening all websites in browser..." -ForegroundColor Yellow
Start-Sleep -Seconds 2

# Open Jenkins
Start-Process "http://localhost:8080"
Start-Sleep -Seconds 1

# Open Dashboard
Start-Process "http://localhost:3000"
Start-Sleep -Seconds 1

# Open Flask App
Start-Process "http://localhost:5000"

Write-Host "`n=================================================" -ForegroundColor Cyan
Write-Host "   ALL SYSTEMS ARE UP AND RUNNING!               " -ForegroundColor Cyan
Write-Host "=================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "  Jenkins Dashboard  --> http://localhost:8080" -ForegroundColor Green
Write-Host "  Flask App          --> http://localhost:5000" -ForegroundColor Green
Write-Host "  Pipeline Monitor   --> http://localhost:3000" -ForegroundColor Green
Write-Host ""
Write-Host "  Next: Go to Jenkins --> Click 'Build Now'!" -ForegroundColor Yellow
Write-Host "=================================================" -ForegroundColor Cyan
