@echo off
chcp 65001 >nul 2>&1
title Ledom照片视频整理 - Streamlit

:START
cls
echo ========================================
echo     Ledom照片视频整理 v1.94 (Streamlit版)
echo ========================================
echo.
echo [1] 启动应用
echo [2] 安装/更新依赖
echo [3] 退出
echo.
set /p choice=请选择 (1-3): 

if "%choice%"=="1" goto RUN
if "%choice%"=="2" goto INSTALL
if "%choice%"=="3" exit
goto START

:INSTALL
cls
echo ========================================
echo 正在安装/更新依赖...
echo ========================================
echo.
echo [基础依赖] streamlit
pip install --upgrade streamlit
echo.
echo [可选依赖] exifread
pip install exifread
echo.
echo [可选依赖] pillow-heif
pip install pillow-heif
echo.
echo ========================================
echo 依赖安装完成！
echo ========================================
pause
goto START

:RUN
cls
echo ========================================
echo 正在启动，请稍候...
echo 浏览器将自动打开 http://localhost:8501
echo 关闭此窗口即可停止服务
echo ========================================
echo.

python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未检测到 Python，请先安装 Python 3.6+
    echo 下载地址: https://www.python.org/downloads/
    pause
    exit /b 1
)

python -c "import streamlit" >nul 2>&1
if errorlevel 1 (
    echo [错误] streamlit 未安装，请先选择 [2] 安装依赖
    pause
    goto START
)

streamlit run photo_organizer_streamlit.py
pause