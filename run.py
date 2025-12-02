#!/usr/bin/env python3
"""
Unified Launcher for Financial Charting Tool.

- Runs the backend server (which also serves the frontend).
- Opens the browser automatically.
- Accepts a file path to load data immediately.

Usage:
    python run.py [file.csv]
"""

import sys
import os
import time
import webbrowser
import argparse
import subprocess
import signal
from pathlib import Path

def main():
    parser = argparse.ArgumentParser(description="Financial Charting Tool")
    parser.add_argument("file", nargs="?", help="Path to CSV file to load")
    parser.add_argument("--port", type=int, default=8000, help="Port to run the server on")
    parser.add_argument("--no-browser", action="store_true", help="Do not open browser automatically")
    args = parser.parse_args()

    port = args.port
    csv_file = args.file
    
    # Resolve absolute path for CSV if provided
    if csv_file:
        csv_path = Path(csv_file).resolve()
        if not csv_path.exists():
            print(f"❌ Error: File not found: {csv_file}")
            sys.exit(1)
        csv_arg = str(csv_path)
    else:
        csv_arg = None

    print(f"🚀 Starting Financial Charting Tool on port {port}...")

    # Start backend server (which serves frontend at /)
    # We use sys.executable to ensure we use the same python environment
    # We assume 'poetry run' is handled by the user invoking this script via poetry, 
    # or that the dependencies are installed in the current env.
    # But looking at original run.py, it used "poetry run uvicorn". 
    # If the user runs "python run.py", they might not be in poetry env.
    # We'll try to use 'uvicorn' directly if available, or assume user is in env.
    
    cmd = [sys.executable, "-m", "uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", str(port)]
    
    try:
        # Start process
        process = subprocess.Popen(
            cmd,
            cwd=os.getcwd(),
            # Create new process group on Windows to handle Ctrl+C cleanly
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if sys.platform == 'win32' else 0
        )
        
        # Wait for server to start (naive wait)
        time.sleep(2)
        
        if process.poll() is not None:
            print("❌ Server failed to start.")
            sys.exit(1)

        base_url = f"http://localhost:{port}"
        
        if csv_arg:
            # Pass filename parameter. 
            # Note: The frontend expects 'filename' param.
            # We use absolute path so backend can find it.
            url = f"{base_url}/?filename={csv_arg}"
            print(f"📂 Loading file: {csv_arg}")
        else:
            url = base_url

        print("\n" + "="*60)
        print(f"✅ Server running at: {base_url}")
        print(f"📊 Chart URL:       {url}")
        print("="*60)
        print("\n💡 Press Ctrl+C to stop the server\n")

        if not args.no_browser:
            print("🌐 Opening browser...")
            webbrowser.open(url)

        # Keep running
        while True:
            if process.poll() is not None:
                print("❌ Server process ended unexpected.")
                break
            time.sleep(1)

    except KeyboardInterrupt:
        print("\n\n🛑 Shutting down...")
    finally:
        if 'process' in locals():
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()

if __name__ == "__main__":
    main()
