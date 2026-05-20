# This script removes the crash code from app.py, restores it to a healthy state,
# commits the change, and pushes it to your GitHub repository.
$AppPath = "app/app.py"
$Content = Get-Content $AppPath

# Filter out the simulated failure lines
$NewContent = @()
$skip = $false
foreach ($line in $Content) {
    if ($line -match "# SIMULATED FAILURE FOR DEMO") {
        $skip = $true
        continue
    }
    if ($skip -and ($line -match "import sys" -or $line -match "print\('CRITICAL: Application crasing" -or $line -match "os._exit\(1\)")) {
        # Check if we should stop skipping
        if ($line -match "os._exit\(1\)") {
            $skip = $false
        }
        continue
    }
    $NewContent += $line
}
Set-Content $AppPath $NewContent

Write-Host "Restoring the application code locally..." -ForegroundColor Green
git add app/app.py
git commit -m "Restore app code to healthy state"

Write-Host "Pushing the clean code to GitHub..." -ForegroundColor Yellow
git push origin main

Write-Host "`nClean code is now live on GitHub!" -ForegroundColor Green
Write-Host "Go to Jenkins (http://localhost:8080) and click 'Build Now'." -ForegroundColor Green
Write-Host "The pipeline should build and deploy successfully!" -ForegroundColor Green
