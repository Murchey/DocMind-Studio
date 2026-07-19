@echo off
chcp 65001 >nul 2>&1
echo ========================================
echo   PPT Deep Summary - 安装依赖
echo ========================================
echo.

python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未检测到 Python，请先安装 Python 3.10+
    pause
    exit /b 1
)

echo [安装] python-pptx（阿里云镜像源）
pip install python-pptx -i https://mirrors.aliyun.com/pypi/simple/ --trusted-host mirrors.aliyun.com
if errorlevel 1 (
    echo [失败] 安装失败，请检查网络连接
    pause
    exit /b 1
)

echo.
echo ========================================
echo   安装完成！
echo ========================================
pause
