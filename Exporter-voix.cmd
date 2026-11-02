@echo off
chcp 65001 >nul
title Windose Benkyou - export des voix
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0installer\export-voices.ps1" %*
echo.
pause
