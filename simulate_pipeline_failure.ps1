# This script modifies the app code to crash immediately on startup,
# commits the change, and pushes it to your GitHub repository.
$AppPath = "app/app.py"
$Content = Get-Content $AppPath

# Inject the crash code right before app starts
$NewContent = @()
foreach ($line in $Content) {
    if ($line -match "if __name__ == '__main__':") {
        $NewContent += "# SIMULATED FAILURE FOR DEMO"
        $NewContent += "import sys"
        $NewContent += "print('CRITICAL: Application crasing due to simulated unrecoverable error!', file=sys.stderr)"
        $NewContent += "os._exit(1)"
    }
    $NewContent += $line
}
Set-Content $AppPath $NewContent

Write-Host "Breaking the application code locally..." -ForegroundColor Red
git add app/app.py
git commit -m "Simulate startup failure for self-healing demo"

Write-Host "Pushing the broken code to GitHub..." -ForegroundColor Yellow
git push origin main

Write-Host "`nBroken code is now live on GitHub!" -ForegroundColor Green
Write-Host "Go to Jenkins (http://localhost:8080) and click 'Build Now'." -ForegroundColor Green
Write-Host "The build will fail at the Test stage, capture the log, and trigger the Ansible self-healing playbook!" -ForegroundColor Green
