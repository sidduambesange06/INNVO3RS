"""
Start the API with automatic port selection (avoids WinError 10048).

From the skyguard-v2 folder:
  .\\venv\\Scripts\\python.exe -m app

Do not use `uvicorn app.main:app --port 8000` if something may already be on 8000 —
that runs full startup then exits when bind fails.
"""

from __future__ import annotations

import os
import sys


def main() -> None:
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    os.chdir(root)
    if root not in sys.path:
        sys.path.insert(0, root)
    import run_server

    run_server.main()


if __name__ == "__main__":
    main()
