@echo off
REM ============================================================
REM  Innovation Hub - build a single, sendable HTML file.
REM  Double-click this file. It reads the modular site and writes
REM  dist\innovation-hub.html (nothing existing is changed).
REM ============================================================
cd /d "%~dp0"

where py >nul 2>nul
if %errorlevel%==0 (
  py build.py
  goto done
)

where python >nul 2>nul
if %errorlevel%==0 (
  python build.py
  goto done
)

echo.
echo  Python was not found on this PC.
echo  Install it from https://www.python.org/downloads/  (tick "Add to PATH"),
echo  then double-click build.bat again.
echo.

:done
echo.
pause
