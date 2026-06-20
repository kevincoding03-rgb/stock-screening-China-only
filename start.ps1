# ============================================================
#  DZH - A-Share Stock Screener Launcher (PowerShell)
#  Handles language selection, dependency check, and launch
# ============================================================

# Set UTF-8 console output so Chinese displays correctly
try {
    [Console]::OutputEncoding = [System.Text.Encoding]::UTF8
    $OutputEncoding = [System.Text.Encoding]::UTF8
    chcp 65001 > $null
} catch {}

function Get-Choice {
    param([string]$Prompt, [string[]]$Valid)
    while ($true) {
        $c = Read-Host $Prompt
        $c = $c.Trim()
        if ($Valid -contains $c) { return $c }
        if ($c -eq "") { return $Valid[0] }
        Write-Host "  Invalid input, please try again." -ForegroundColor Yellow
    }
}

# ==================== Language Selection ====================
Write-Host "============================================================"
Write-Host "  DZH - A-Share Stock Screener"
Write-Host "  DZH - A股实时筛选工具"
Write-Host "============================================================"
Write-Host ""
Write-Host "  [1] English"
Write-Host "  [2] 中文 (Chinese)"
Write-Host ""
$lang = Get-Choice "Select language / 选择语言 [1/2]" @("1", "2")

# ==================== Localization strings ====================
if ($lang -eq "1") {
    $T = @{
        title        = "DZH - A-Share Stock Screener Launcher"
        err_py       = "Python not detected. Please install Python 3.8 or higher."
        download     = "Download"
        ok_py        = "installed"
        check        = "Checking dependencies..."
        miss         = "not installed, installing..."
        ok_inst      = "installed successfully"
        ok           = "installed"
        err_inst     = "installation failed"
        ready        = "All dependencies ready. Launching dzh.py ..."
        err_exit     = "Program exited abnormally, error code"
        lang_set     = "Using English"
        separator    = "============================================================"
    }
} else {
    $T = @{
        title        = "DZH - A股实时筛选工具 启动器"
        err_py       = "未检测到 Python，请先安装 Python 3.8 及以上版本"
        download     = "下载地址"
        ok_py        = "已安装"
        check        = "正在检查依赖..."
        miss         = "未安装，正在安装..."
        ok_inst      = "安装成功"
        ok           = "已安装"
        err_inst     = "安装失败"
        ready        = "所有依赖就绪，正在启动 dzh.py ..."
        err_exit     = "程序异常退出，错误码"
        lang_set     = "使用中文"
        separator    = "============================================================"
    }
}

Write-Host ""
Write-Host $T.separator
Write-Host "  $($T.title)"
Write-Host $T.separator
Write-Host ""

# ==================== Check Python ====================
$pythonOk = $true
try {
    $pyVer = (python --version 2>&1) -replace "Python ", ""
    if ($LASTEXITCODE -ne 0) { $pythonOk = $false }
} catch {
    $pythonOk = $false
}

if (-not $pythonOk) {
    Write-Host "[ERROR] $($T.err_py)" -ForegroundColor Red
    Write-Host "        $($T.download): https://www.python.org/downloads/"
    exit 1
}

Write-Host "[OK] Python $pyVer $($T.ok_py)"
Write-Host ""

# ==================== Check & install dependencies ====================
Write-Host "[..] $($T.check)"
Write-Host ""

$deps = @("akshare", "pandas", "curl_cffi")
$failed = $false

foreach ($dep in $deps) {
    $installed = $false
    try {
        pip show $dep *> $null
        if ($LASTEXITCODE -eq 0) { $installed = $true }
    } catch {}

    if ($installed) {
        Write-Host "[OK] $dep $($T.ok)"
    } else {
        Write-Host "[MISS] $dep $($T.miss)"
        pip install $dep
        if ($LASTEXITCODE -ne 0) {
            Write-Host "[ERROR] $dep $($T.err_inst)" -ForegroundColor Red
            $failed = $true
            break
        }
        Write-Host "[OK] $dep $($T.ok_inst)"
    }
}

if ($failed) { exit 1 }

Write-Host ""
Write-Host $T.separator
Write-Host "  $($T.ready)"
Write-Host $T.separator
Write-Host ""

# ==================== Launch dzh.py ====================
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$target = Join-Path $scriptDir "dzh.py"

python $target
$exitCode = $LASTEXITCODE
if ($exitCode -ne 0) {
    Write-Host ""
    Write-Host "[ERROR] $($T.err_exit): $exitCode" -ForegroundColor Red
}

exit $exitCode
