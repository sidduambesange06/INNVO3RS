"""
Start SkyGuard on API_PORT from .env, or the next free port if that one is busy.

From skyguard-v2:
  .\\venv\\Scripts\\python.exe run_server.py
  .\\venv\\Scripts\\python.exe -m app

Set SKYGUARD_FREE_LISTEN_PORT=1 in .env to stop whatever is LISTENING on API_PORT (Windows).
"""
from __future__ import annotations

import os
import socket
import subprocess
import sys
import time


def _free_listen_port_windows(port: int) -> None:
    """Stop processes listening on this port (typical stale uvicorn). Windows only."""
    if os.name != "nt":
        return
    ps = (
        f"$c = Get-NetTCPConnection -LocalPort {port} -State Listen -ErrorAction SilentlyContinue; "
        f"if ($c) {{ $c | Select-Object -ExpandProperty OwningProcess -Unique | "
        f"ForEach-Object {{ if ($_ -and $_ -ne 0) {{ Stop-Process -Id $_ -Force -ErrorAction SilentlyContinue }} }} }}"
    )
    try:
        subprocess.run(
            ["powershell", "-NoProfile", "-NonInteractive", "-Command", ps],
            capture_output=True,
            timeout=20,
            check=False,
        )
        time.sleep(0.4)
    except (OSError, subprocess.TimeoutExpired):
        pass


def _pick_port(preferred: int, listen_host: str, span: int = 40) -> tuple[int, bool]:
    """Try bind with the same host family uvicorn will use."""
    bind_addr = listen_host
    if listen_host in ("0.0.0.0", "::"):
        bind_addr = "0.0.0.0"
    for port in range(preferred, preferred + span):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.bind((bind_addr, port))
            return port, port == preferred
        except OSError:
            pass
        finally:
            s.close()
    return preferred, False


def main() -> None:
    root = os.path.dirname(os.path.abspath(__file__))
    os.chdir(root)

    from dotenv import load_dotenv

    load_dotenv(os.path.join(root, ".env"))

    preferred = int(os.environ.get("API_PORT", "8000"))
    listen_host = os.environ.get("API_HOST", "0.0.0.0").strip() or "0.0.0.0"

    free_flag = os.environ.get("SKYGUARD_FREE_LISTEN_PORT", "1").strip().lower()
    if free_flag in ("1", "true", "yes", "on"):
        _free_listen_port_windows(preferred)

    port, exact = _pick_port(preferred, listen_host)
    if not exact:
        print(
            f"[SkyGuard] Port {preferred} is already in use — binding to {port} instead.",
            file=sys.stderr,
        )
    os.environ["API_PORT"] = str(port)

    import uvicorn
    from app.config import settings

    host = settings.api_host
    browse = "127.0.0.1" if host in ("0.0.0.0", "::") else host
    print(
        f"[SkyGuard] Listening on http://{host}:{settings.api_port}  (browser: http://{browse}:{settings.api_port})",
        file=sys.stderr,
    )
    uvicorn.run(
        "app.main:app",
        host=host,
        port=settings.api_port,
        log_level="info",
        access_log=True,
    )


if __name__ == "__main__":
    main()
