# Questrade Custom API Wrapper - Automated Git Commit Tool
# PowerShell Script for Windows Users

# Colors for output
$GREEN = [ConsoleColor]::Green
$YELLOW = [ConsoleColor]::Yellow
$RED = [ConsoleColor]::Red
$BLUE = [ConsoleColor]::Cyan

# Default commit message if none provided
$DEFAULT_MSG = "Update Questrade Custom API Wrapper"

# Display script header
Write-Host "=========================================" -ForegroundColor $BLUE
Write-Host "  Questrade Custom API Wrapper          " -ForegroundColor $BLUE
Write-Host "  Automated Git Commit Tool             " -ForegroundColor $BLUE
Write-Host "=========================================" -ForegroundColor $BLUE
Write-Host ""

# Check if Git is installed
try {
    git --version | Out-Null
} catch {
    Write-Host "Error: Git is not installed or not in PATH." -ForegroundColor $RED
    exit 1
}

# Check if current directory is a git repository
if (-not (Test-Path .git)) {
    Write-Host "Error: Not a git repository." -ForegroundColor $RED
    Write-Host "Please run this script from the root of your git repository." -ForegroundColor $YELLOW
    exit 1
}

# Function to show status
function Show-GitStatus {
    Write-Host "Current Status:" -ForegroundColor $BLUE
    git status -s
    Write-Host ""
}

# Display initial status
Show-GitStatus

# Check if there are changes to commit
$gitStatus = git status --porcelain
if ([string]::IsNullOrEmpty($gitStatus)) {
    Write-Host "No changes to commit. Working directory is clean." -ForegroundColor $YELLOW
    exit 0
}

# Ask if user wants to see diff
$showDiff = Read-Host "Do you want to see the diff? (y/n)"
if ($showDiff -eq "y" -or $showDiff -eq "Y") {
    git diff
}

# Ask for commit message
Write-Host "Enter commit message (leave empty for default message: '$DEFAULT_MSG'):" -ForegroundColor $YELLOW
$commitMsg = Read-Host

# If empty, use default message
if ([string]::IsNullOrEmpty($commitMsg)) {
    $commitMsg = $DEFAULT_MSG
}

# Ask if user wants to add all changes
$addAll = Read-Host "Add all changes? (y/n)"
if ($addAll -eq "y" -or $addAll -eq "Y") {
    git add .
    Write-Host "All changes staged for commit." -ForegroundColor $GREEN
} else {
    Write-Host "Please specify files to add (space-separated):" -ForegroundColor $YELLOW
    $filesToAdd = Read-Host
    if (-not [string]::IsNullOrEmpty($filesToAdd)) {
        # Split input by spaces and add each file
        $filesToAdd -split ' ' | ForEach-Object {
            git add $_
        }
        Write-Host "Selected files staged for commit." -ForegroundColor $GREEN
    } else {
        Write-Host "No files specified. Nothing staged." -ForegroundColor $RED
        exit 1
    }
}

# Display status after staging
Show-GitStatus

# Confirm before commit
$confirm = Read-Host "Ready to commit with message: '$commitMsg'. Proceed? (y/n)"
if ($confirm -ne "y" -and $confirm -ne "Y") {
    Write-Host "Commit aborted." -ForegroundColor $RED
    exit 0
}

# Commit
git commit -m $commitMsg

if ($LASTEXITCODE -eq 0) {
    Write-Host "Changes committed successfully!" -ForegroundColor $GREEN
    
    # Ask if user wants to push changes
    $pushChanges = Read-Host "Push changes to remote repository? (y/n)"
    if ($pushChanges -eq "y" -or $pushChanges -eq "Y") {
        $currentBranch = git symbolic-ref --short HEAD
        Write-Host "Pushing to branch: $currentBranch" -ForegroundColor $BLUE
        git push origin $currentBranch
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "Changes pushed successfully!" -ForegroundColor $GREEN
        } else {
            Write-Host "Failed to push changes." -ForegroundColor $RED
        }
    } else {
        Write-Host "Changes were committed locally but not pushed." -ForegroundColor $BLUE
    }
} else {
    Write-Host "Failed to commit changes." -ForegroundColor $RED
}

# Final status
Write-Host "Final Status:" -ForegroundColor $BLUE
git status 