# SkyGuard V2 — prefer run_server.py (auto free port). Optional: free port 8000 first.
$ErrorActionPreference = "SilentlyContinue"
Set-Location $PSScriptRoot
$env:PYTHONIOENCODING = "utf-8"

if ($args.Count -ge 1 -and $args[0] -eq "kill") {
    $port = if ($args.Count -ge 2) { [int]$args[1] } else { 8000 }
    Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue |
        Select-Object -ExpandProperty OwningProcess -Unique |
        ForEach-Object { if ($_ -and $_ -ne 0) { Stop-Process -Id $_ -Force -ErrorAction SilentlyContinue } }
    Start-Sleep -Seconds 1
}

& ".\venv\Scripts\python.exe" ".\run_server.py"
