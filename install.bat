@echo off
title SillyTavern Immersive Task Assistant - Installer
color 0a

echo ===============================================
echo   SillyTavern Immersive Task Assistant 安装程序
echo ===============================================
echo.

REM Step 1: 检查 Python 是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo [×] 未检测到 Python，请先安装 Python 3.10+ 并添加到 PATH
    pause
    exit /b
)

REM Step 2: 安装依赖
echo [→] 正在安装依赖库...
pip install -r requirements.txt
if errorlevel 1 (
    echo [×] 依赖安装失败，请检查网络或手动执行 pip install -r requirements.txt
    pause
    exit /b
)

REM Step 3: 配置开机自启
echo [→] 正在配置开机自启...
python setup_autostart.py
if errorlevel 1 (
    echo [×] 配置开机自启失败，请尝试手动运行 setup_autostart.py
    pause
    exit /b
)

echo.
echo [√] 安装完成！请重启电脑以启用提醒功能。
echo.
pause
