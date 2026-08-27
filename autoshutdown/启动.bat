@echo off
rem 用 pythonw 启动，不弹黑色控制台窗口。
cd /d "%~dp0"
start "" pythonw app.py
