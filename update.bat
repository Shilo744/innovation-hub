@echo off
chcp 65001 >nul
cd /d "%~dp0"
title Innovation Hub - עדכון GitHub

echo.
echo ========================================
echo   עדכון אתר Innovation Hub ל-GitHub
echo ========================================
echo.

REM בדיקה שיש שינויים
git status --porcelain >nul 2>&1
if errorlevel 1 (
    echo [שגיאה] התיקייה הזו אינה ריפו Git.
    pause
    exit /b 1
)

echo [1/4] בודק שינויים...
git status --short
echo.

REM אם אין שום שינוי - יוצאים
for /f %%i in ('git status --porcelain ^| find /c /v ""') do set CHANGES=%%i
if "%CHANGES%"=="0" (
    echo אין שינויים לעדכון. הכל מסונכרן עם GitHub.
    echo.
    pause
    exit /b 0
)

echo [2/4] מוסיף את כל הקבצים (כולל חדשים)...
git add -A
if errorlevel 1 goto :error

REM יצירת הודעת commit עם תאריך ושעה
for /f "tokens=2 delims==" %%I in ('"wmic os get localdatetime /value"') do set DT=%%I
set STAMP=%DT:~0,4%-%DT:~4,2%-%DT:~6,2% %DT:~8,2%:%DT:~10,2%

echo [3/4] שומר commit...
git commit -m "Auto-update: %STAMP%"
if errorlevel 1 goto :error

echo [4/4] מעלה ל-GitHub...
git push origin main
if errorlevel 1 goto :error

echo.
echo ========================================
echo   ✅ העדכון הושלם בהצלחה!
echo ========================================
echo.

REM פתיחת ה-GitHub בדפדפן
echo פותח את GitHub בדפדפן...
for /f "tokens=*" %%U in ('git remote get-url origin') do set REPO_URL=%%U
REM הסרת .git מסוף ה-URL אם קיים
set REPO_URL=%REPO_URL:.git=%
start "" "%REPO_URL%"

timeout /t 3 >nul
exit /b 0

:error
echo.
echo ========================================
echo   ❌ אירעה שגיאה - ראה הודעה למעלה
echo ========================================
echo.
pause
exit /b 1
