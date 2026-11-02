"""Convenience launcher for Demo-to-Deck."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))


def run_gui(host: str = "localhost", port: int = 8501) -> int:
    """Launch the Streamlit web application."""
    app_file = ROOT_DIR / "app.py"
    # Find python / streamlit in .venv if available
    venv_streamlit = ROOT_DIR / ".venv" / "Scripts" / "streamlit.exe"
    if venv_streamlit.exists():
        cmd = [str(venv_streamlit), "run", str(app_file), "--server.port", str(port), "--server.address", host]
    else:
        cmd = [sys.executable, "-m", "streamlit", "run", str(app_file), "--server.port", str(port), "--server.address", host]

    print(f"[*] Starting Demo-to-Deck Streamlit UI on http://{host}:{port}...")
    try:
        return subprocess.call(cmd)
    except KeyboardInterrupt:
        print("\n[*] Application stopped.")
        return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Run Demo-to-Deck agent")
    parser.add_argument("--cli", action="store_true", help="Run in CLI mode instead of web UI")
    parser.add_argument("source", nargs="?", default="sample_demo_app", help="Path or repo to inspect (CLI mode)")
    parser.add_argument("--port", type=int, default=8501, help="Port for Streamlit app (default: 8501)")
    parser.add_argument("--host", default="localhost", help="Host address (default: localhost)")
    args, unknown = parser.parse_known_args()

    if args.cli:
        from demo_to_deck.__main__ import main as cli_main
        cli_args = [args.source] + unknown
        return cli_main(cli_args)

    return run_gui(host=args.host, port=args.port)


if __name__ == "__main__":
    sys.exit(main())

