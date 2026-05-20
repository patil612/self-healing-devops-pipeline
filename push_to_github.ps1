# This script configures your remote and pushes the repository to your GitHub account.
# Replace 'self-healing-devops-pipeline' with your repository name if needed.
$REPO_NAME = "self-healing-devops-pipeline"
$GITHUB_USERNAME = "patil612"

# Check if origin already exists
$remoteExists = git remote | Where-Object { $_ -eq "origin" }

if ($remoteExists) {
    Write-Host "Updating git remote URL to point to https://github.com/$GITHUB_USERNAME/$REPO_NAME.git"
    git remote set-url origin "https://github.com/$GITHUB_USERNAME/$REPO_NAME.git"
} else {
    Write-Host "Adding git remote origin pointing to https://github.com/$GITHUB_USERNAME/$REPO_NAME.git"
    git remote add origin "https://github.com/$GITHUB_USERNAME/$REPO_NAME.git"
}

Write-Host "Staging any unstaged changes..."
git add .

# Try to commit, ignore if there's nothing to commit
Write-Host "Committing changes..."
git commit -m "Configure self-healing devops pipeline repository" 2>$null

Write-Host "Setting default branch to main..."
git branch -M main

Write-Host "Pushing to GitHub..."
git push -u origin main
