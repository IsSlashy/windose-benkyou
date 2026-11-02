@echo off
chcp 65001 >nul
title Windose Benkyou - installation
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0installer\install.ps1" %*
echo.
pause
