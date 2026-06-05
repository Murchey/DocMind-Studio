@echo off
REM =====================================================
REM 使用阿里云镜像安装 Python requirements.txt
REM =====================================================

REM 获取当前脚本所在目录
SET "SCRIPT_DIR=%~dp0"

REM 默认使用同级目录下的 requirements.txt
SET "REQ_FILE=%SCRIPT_DIR%requirements.txt"

REM 默认 Python 可执行路径
SET "PYTHON_PATH=python"

REM 检查 requirements.txt 是否存在
IF NOT EXIST "%REQ_FILE%" (
    echo ERROR: requirements.txt 文件不存在: %REQ_FILE%
    pause
    exit /b 1
)

REM 检查 Python 是否可用
%PYTHON_PATH% --version >nul 2>&1
IF ERRORLEVEL 1 (
    echo ERROR: Python 未找到，请确保已安装 Python 或修改 PYTHON_PATH
    pause
    exit /b 1
)

REM 安装 pip（如果未安装）
%PYTHON_PATH% -m pip --version >nul 2>&1
IF ERRORLEVEL 1 (
    echo pip 未安装，尝试使用 ensurepip 安装...
    %PYTHON_PATH% -m ensurepip
)

REM 升级 pip
echo 升级 pip...
%PYTHON_PATH% -m pip install --upgrade pip

REM 使用阿里云镜像安装 requirements.txt
echo 使用阿里云镜像安装依赖...
%PYTHON_PATH% -m pip install -r "%REQ_FILE%" -i https://mirrors.aliyun.com/pypi/simple/

echo 依赖安装完成！
pause