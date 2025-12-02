#!/usr/bin/env python3
"""
Launcher script for the Financial Charting Tool.
Runs both backend API and frontend server simultaneously.
"""

import subprocess
import sys
import os
import signal
import time
from pathlib import Path

def main():
    """Start backend API and frontend server."""
    
    # Store process references
    processes = []
    
    def signal_handler(sig, frame):
        """Handle Ctrl+C gracefully."""
        print("\n\n🛑 Shutting down servers...")
        for proc in processes:
            proc.terminate()
        sys.exit(0)
    
    # Register signal handler
    signal.signal(signal.SIGINT, signal_handler)
    
    try:
        # Start backend API
        print("🚀 Starting Backend API on http://localhost:8000...")
        backend = subprocess.Popen(
            ["poetry", "run", "uvicorn", "src.api.main:app", "--reload", "--host", "0.0.0.0", "--port", "8000"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            bufsize=1
        )
        processes.append(backend)
        
        # Wait a bit for backend to start
        time.sleep(2)
        
        # Start frontend server
        print("🌐 Starting Frontend Server on http://localhost:3000...")
        frontend_dir = Path("src/frontend")
        frontend = subprocess.Popen(
            [sys.executable, "-m", "http.server", "3000"],
            cwd=frontend_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            bufsize=1
        )
        processes.append(frontend)
        
        print("\n" + "="*60)
        print("✅ Servers are running!")
        print("="*60)
        print(f"📊 Frontend:  http://localhost:3000")
        print(f"🔧 Backend:   http://localhost:8000")
        print(f"📚 API Docs:  http://localhost:8000/docs")
        print("="*60)
        print("\n💡 Press Ctrl+C to stop both servers\n")
        
        # Keep script running and show output
        while True:
            # Check if processes are still running
            backend_status = backend.poll()
            frontend_status = frontend.poll()
            
            if backend_status is not None:
                print(f"❌ Backend exited with code {backend_status}")
                break
            
            if frontend_status is not None:
                print(f"❌ Frontend exited with code {frontend_status}")
                break
            
            time.sleep(1)
    
    except KeyboardInterrupt:
        print("\n\n🛑 Shutting down servers...")
    except Exception as e:
        print(f"\n❌ Error: {e}")
    finally:
        # Clean up processes
        for proc in processes:
            try:
                proc.terminate()
                proc.wait(timeout=5)
            except:
                proc.kill()

if __name__ == "__main__":
    main()

