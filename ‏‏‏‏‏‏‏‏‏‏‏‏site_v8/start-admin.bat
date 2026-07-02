@echo off
title RISE.HUB - Local Content Admin
cd /d "%~dp0"

set PYCMD=
where py >nul 2>nul && set PYCMD=py
if not defined PYCMD (
  where python >nul 2>nul && set PYCMD=python
)

if not defined PYCMD (
  echo.
  echo  Python is required. Install it from:
  echo  https://www.python.org/downloads/   ^(tick "Add to PATH"^)
  echo  then double-click this file again.
  echo.
  pause
  exit /b
)

%PYCMD% admin\server.py

echo.
echo  Server stopped.
pause
