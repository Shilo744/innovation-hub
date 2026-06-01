@echo off
title Innovation Hub - GitHub Update
cd /d "%~dp0"

echo ===================================================
echo             Innovation Hub - GitHub Update          
echo ===================================================
echo.

:: Check if git is installed
where git >nul 2>nul
if errorlevel 1 (
    echo [ERROR] Git is not installed or not in your PATH.
    goto error
)

:: Check if this is a git repository
git rev-parse --is-inside-work-tree >nul 2>nul
if errorlevel 1 (
    echo [ERROR] This directory is not a Git repository.
    goto error
)

:: Detect current branch
set current_branch=main
for /f "tokens=*" %%i in ('git branch --show-current') do set current_branch=%%i

echo [1/3] Adding changes...
git add -A
if errorlevel 1 (
    echo [ERROR] Failed to add changes.
    goto error
)

:: Check if there are changes to commit
git diff-index --quiet HEAD --
if not errorlevel 1 (
    echo No new changes to commit. Checking for unpushed commits...
    goto push
)

echo.
echo [2/3] Committing changes...
set commit_msg=Auto-update: %date% %time%
set /p commit_msg="Enter commit message (or press Enter for auto-commit): "

git commit -m "%commit_msg%"
if errorlevel 1 (
    echo [ERROR] Failed to commit changes.
    goto error
)

:push
echo.
echo [3/3] Pushing to GitHub...
git push origin %current_branch%
if errorlevel 1 (
    echo.
    echo [ERROR] Failed to push to GitHub.
    echo Please check your connection and credentials.
    goto error
)

echo.
echo ===================================================
echo    SUCCESS: Update Completed Successfully!
echo ===================================================
echo.

:: Extract username and repo name to construct GitHub Pages URL
for /f "tokens=*" %%a in ('git remote get-url origin') do set repoUrl=%%a
set tempUrl=%repoUrl:.git=%
set tempUrl=%tempUrl:https://github.com/=%
set tempUrl=%tempUrl:git@github.com:=%
for /f "tokens=1,2 delims=/" %%g in ("%tempUrl%") do (
    set username=%%g
    set repo=%%h
)

set pagesUrl=https://%username%.github.io/%repo%/

echo Opening website: %pagesUrl%
start %pagesUrl%
goto end

:error
echo.
echo ===================================================
echo    FAILED: Update Failed!
echo ===================================================
echo.

:end
echo Press any key to close...
pause >nul
