@echo off
title Job Portal Web Application - Flask Server
cd /d "%~dp0"
echo ===================================================
echo Starting Job Portal Web Application...
echo Default Admin: admin@jobportal.com / admin123
echo URL: http://127.0.0.1:5000
echo ===================================================
env\Scripts\python.exe app.py
pause
