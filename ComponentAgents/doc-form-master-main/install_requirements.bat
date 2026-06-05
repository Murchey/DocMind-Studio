@echo off
chcp 65001 >nul

echo ========================================
echo DOCX Master - Requirements Installer
echo ========================================
echo.

:: 检测 Python
python --version >nul 2>&1

if %errorlevel% neq 0 (
    echo [ERROR] 未检测到 Python
    echo 请先安装 Python 3.10+
    pause
    exit /b
)

echo [INFO] 检测到 Python
echo.

:: 升级 pip
echo [INFO] 正在升级 pip...
python -m pip install --upgrade pip -i https://mirrors.aliyun.com/pypi/simple/

echo.
echo [INFO] 正在使用阿里云镜像安装依赖...
echo.

:: 安装 requirements.txt
pip install -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple/

if %errorlevel% neq 0 (
    echo.
    echo [ERROR] 依赖安装失败
    pause
    exit /b
)

echo.
echo ========================================
echo 所有依赖安装完成
echo ========================================
echo.

pause