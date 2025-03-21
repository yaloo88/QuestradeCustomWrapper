@echo off
setlocal enabledelayedexpansion

:: Colors for Windows console
set "GREEN=[92m"
set "YELLOW=[93m"
set "RED=[91m"
set "BLUE=[96m"
set "NC=[0m"

:: Default commit message
set "DEFAULT_MSG=Update Questrade Custom API Wrapper"

:: Display header
echo %BLUE%==========================================%NC%
echo %BLUE%  Questrade Custom API Wrapper          %NC%
echo %BLUE%  Automated Git Commit Tool             %NC%
echo %BLUE%==========================================%NC%
echo.

:: Check if Git is installed
where git >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo %RED%Error: Git is not installed or not in PATH.%NC%
    goto :end
)

:: Check if current directory is a git repository
if not exist ".git" (
    echo %RED%Error: Not a git repository.%NC%
    echo %YELLOW%Please run this script from the root of your git repository.%NC%
    goto :end
)

:: Display initial status
call :display_status

:: Check if there are changes to commit
git status --porcelain > temp_status.txt
set /p git_status=<temp_status.txt
del temp_status.txt

if "!git_status!" == "" (
    echo %YELLOW%No changes to commit. Working directory is clean.%NC%
    goto :end
)

:: Ask if user wants to see diff
set /p show_diff=%YELLOW%Do you want to see the diff? (y/n): %NC%
if /i "!show_diff!" == "y" (
    git diff
    echo.
)

:: Ask for commit message
echo %YELLOW%Enter commit message (leave empty for default message: '%DEFAULT_MSG%'):%NC%
set /p commit_msg=

:: If empty, use default message
if "!commit_msg!" == "" (
    set "commit_msg=%DEFAULT_MSG%"
)

:: Ask if user wants to add all changes
set /p add_all=%YELLOW%Add all changes? (y/n): %NC%
if /i "!add_all!" == "y" (
    git add .
    echo %GREEN%All changes staged for commit.%NC%
) else (
    echo %YELLOW%Please specify files to add (space-separated):%NC%
    set /p files_to_add=
    if not "!files_to_add!" == "" (
        git add !files_to_add!
        echo %GREEN%Selected files staged for commit.%NC%
    ) else (
        echo %RED%No files specified. Nothing staged.%NC%
        goto :end
    )
)

:: Display status after staging
call :display_status

:: Confirm before commit
set /p confirm=%YELLOW%Ready to commit with message: '!commit_msg!'. Proceed? (y/n): %NC%
if /i not "!confirm!" == "y" (
    echo %RED%Commit aborted.%NC%
    goto :end
)

:: Commit
git commit -m "!commit_msg!"

if %ERRORLEVEL% equ 0 (
    echo %GREEN%Changes committed successfully!%NC%
    
    :: Ask if user wants to push changes
    set /p push_changes=%YELLOW%Push changes to remote repository? (y/n): %NC%
    if /i "!push_changes!" == "y" (
        for /f "tokens=*" %%a in ('git symbolic-ref --short HEAD') do set current_branch=%%a
        echo %BLUE%Pushing to branch: !current_branch!%NC%
        git push origin !current_branch!
        
        if %ERRORLEVEL% equ 0 (
            echo %GREEN%Changes pushed successfully!%NC%
        ) else (
            echo %RED%Failed to push changes.%NC%
        )
    ) else (
        echo %BLUE%Changes were committed locally but not pushed.%NC%
    )
) else (
    echo %RED%Failed to commit changes.%NC%
)

:: Final status
echo %BLUE%Final Status:%NC%
git status

goto :end

:display_status
echo %BLUE%Current Status:%NC%
git status -s
echo.
goto :eof

:end
endlocal
echo.
echo %BLUE%Press any key to exit...%NC%
pause > nul 