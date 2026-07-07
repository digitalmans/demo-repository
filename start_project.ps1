# Nexus 3D AI System: 一键多终端启动脚本
# 用法: 在 PowerShell 中运行 `.\start_project.ps1`

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

# 定义端口
$PORTS = @{
    "Speech Provider (ASR)" = 8000
    "2Dto3D Backend" = 8002
    "Interactive WebSocket Server" = 8765
    "HTTP Asset Server" = 8080
    "GPT-SoVITS TTS" = 9880
    "Vite Frontend" = 5173
}

# 辅助函数：检查端口占用
function Check-Port($port) {
    return Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue
}

# 菜单选项
function Show-Menu {
    Clear-Host
    Write-Host "==========================================================" -ForegroundColor Cyan
    Write-Host "         🌟 Nexus 3D: AI 沙盒创世数字人系统 🌟" -ForegroundColor Cyan
    Write-Host "==========================================================" -ForegroundColor Cyan
    Write-Host "端口状态检测：" -ForegroundColor Yellow
    foreach ($name in $PORTS.Keys) {
        $port = $PORTS[$name]
        $busy = Check-Port $port
        if ($busy) {
            Write-Host "  [-] $name (Port $port): " -NoNewline
            Write-Host "已占用" -ForegroundColor Red
        } else {
            Write-Host "  [+] $name (Port $port): " -NoNewline
            Write-Host "空闲" -ForegroundColor Green
        }
    }
    Write-Host "----------------------------------------------------------"
    Write-Host "请选择要启动的服务类型：" -ForegroundColor Yellow
    Write-Host "  1. 启动完整的 [Nexus 3D 互动数字人系统] (WS + ASR + Frontend)"
    Write-Host "  2. 仅启动 [2Dto3D 文件转换与打印后台]"
    Write-Host "  3. 仅启动 [GPT-SoVITS 本地语音合成推理 (api.py)]"
    Write-Host "  4. 启动上述所有组件 (多终端并发)"
    Write-Host "  5. 退出"
    Write-Host "=========================================================="
}

while ($true) {
    Show-Menu
    $choice = Read-Host "请输入数字 (1-5)"
    
    switch ($choice) {
        "1" {
            Write-Host "正在启动 [Nexus 3D 互动系统]..." -ForegroundColor Green
            # 1. ASR
            Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location '$PSScriptRoot\backend2'; & '$PSScriptRoot\venv\Scripts\python.exe' speech_provider.py"
            # 2. WebSocket
            Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location '$PSScriptRoot\backend2'; & '$PSScriptRoot\venv\Scripts\python.exe' interactive_server.py"
            # 3. Frontend
            Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location '$PSScriptRoot\frontend2'; npm run dev"
            Write-Host "启动指令已下发到各独立终端，请注意检查弹出窗口。" -ForegroundColor Cyan
            Read-Host "按任意键返回菜单"
        }
        "2" {
            Write-Host "正在启动 [2Dto3D 转换后台]..." -ForegroundColor Green
            Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location '$PSScriptRoot\2Dto3D'; & '$PSScriptRoot\venv\Scripts\python.exe' backend/run.py"
            Write-Host "启动指令已下发到独立终端，2Dto3D 默认运行在 http://127.0.0.1:8002" -ForegroundColor Cyan
            Read-Host "按任意键返回菜单"
        }
        "3" {
            Write-Host "正在启动 [GPT-SoVITS 推理服务]..." -ForegroundColor Green
            Write-Host "注意：如果指定了参考音频，建议手动启动或在 GPT-SoVITS 目录下运行命令行。" -ForegroundColor Yellow
            $ref_audio = Read-Host "（可选）输入参考音频路径 (留空使用默认)"
            $ref_text = Read-Host "（可选）输入参考音频的文本内容"
            
            $cmd = "& '$PSScriptRoot\venv\Scripts\python.exe' api.py"
            if ($ref_audio) {
                $cmd += " -dr `"$ref_audio`""
            }
            if ($ref_text) {
                $cmd += " -dt `"$ref_text`""
                $cmd += " -dl zh"
            }
            
            Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location '$PSScriptRoot\GPT-SoVITS'; $cmd"
            Write-Host "GPT-SoVITS 推理 API 启动指令已发送，默认端口 9880。" -ForegroundColor Cyan
            Read-Host "按任意键返回菜单"
        }
        "4" {
            Write-Host "正在启动系统所有服务..." -ForegroundColor Green
            # ASR
            Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location '$PSScriptRoot\backend2'; & '$PSScriptRoot\venv\Scripts\python.exe' speech_provider.py"
            # WebSocket
            Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location '$PSScriptRoot\backend2'; & '$PSScriptRoot\venv\Scripts\python.exe' interactive_server.py"
            # Frontend
            Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location '$PSScriptRoot\frontend2'; npm run dev"
            # 2Dto3D
            Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location '$PSScriptRoot\2Dto3D'; & '$PSScriptRoot\venv\Scripts\python.exe' backend/run.py"
            # GPT-SoVITS
            Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location '$PSScriptRoot\GPT-SoVITS'; & '$PSScriptRoot\venv\Scripts\python.exe' api.py"
            
            Write-Host "已在五个独立终端中启动所有关联服务！" -ForegroundColor Cyan
            Read-Host "按任意键返回菜单"
        }
        "5" {
            break
        }
        default {
            Write-Host "无效的输入，请重新选择。" -ForegroundColor Red
            Start-Sleep -Seconds 1
        }
    }
}
