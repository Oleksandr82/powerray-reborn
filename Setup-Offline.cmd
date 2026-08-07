@echo off
REM Double-click this ONCE, at home, while you have internet.
REM It creates a local Python virtual environment (venv) and installs
REM everything the cockpit needs. After this, Start-Cockpit.cmd works
REM with no internet connection at all.
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\setup-offline.ps1"
