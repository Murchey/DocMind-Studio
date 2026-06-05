param (
    [Parameter(Mandatory=$true)]
    [string]$ProjectName,           # 用户项目名

    [string]$BasePath = ".\workspace"  # 可选，工作区根路径
)

# 拼接完整工作区路径
$WorkspacePath = Join-Path $BasePath $ProjectName

# 定义子目录
$SubDirs = @("temp", "generated_scripts", "excel_output")

# 创建工作区主目录
if (-Not (Test-Path $WorkspacePath)) {
    New-Item -ItemType Directory -Path $WorkspacePath | Out-Null
    Write-Host "工作区创建完成：" $WorkspacePath
} else {
    Write-Host "工作区已存在：" $WorkspacePath
}

# 创建子目录
foreach ($dir in $SubDirs) {
    $fullPath = Join-Path $WorkspacePath $dir
    if (-Not (Test-Path $fullPath)) {
        New-Item -ItemType Directory -Path $fullPath | Out-Null
        Write-Host "创建子目录：" $fullPath
    } else {
        Write-Host "子目录已存在：" $fullPath
    }
}