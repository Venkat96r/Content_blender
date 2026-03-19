import subprocess
import sys
import os
import signal
import threading
import webbrowser
import time

ROOT = os.path.dirname(os.path.realpath(__file__))
BACKEND = os.path.join(ROOT, "backend")
FRONTEND = os.path.join(ROOT, "frontend")
SERVE_PY_FULL_PATH = os.path.join(FRONTEND, "serve.py")

if not os.path.isdir(BACKEND):
    print("ERROR: backend/ directory not found at: " + BACKEND)
    sys.exit(1)
if not os.path.isdir(FRONTEND):
    print("ERROR: frontend/ directory not found at: " + FRONTEND)
    sys.exit(1)

print("+------------------------------------------------+")
print("|        Content Blender Studio v3.0            |")
print("+------------------------------------------------+")
print("| Backend  -> http://localhost:8000              |")
print("| Frontend -> http://localhost:3000              |")
print("| API Docs -> http://localhost:8000/docs         |")
print("+------------------------------------------------+")
print("")
print("Starting servers... Press Ctrl+C to stop.")
print("")

backend_proc = subprocess.Popen(
    [sys.executable, "-m", "uvicorn", "main:app", "--reload", "--port", "8000"],
    cwd=BACKEND
)

frontend_proc = subprocess.Popen(
    [sys.executable, SERVE_PY_FULL_PATH],
    cwd=FRONTEND
)

def open_browser():
    time.sleep(2.5)
    webbrowser.open("http://localhost:3000")

browser_thread = threading.Thread(target=open_browser, daemon=True)
browser_thread.start()

def shutdown(sig, frame):
    print("\nShutting down servers...")
    backend_proc.terminate()
    frontend_proc.terminate()
    sys.exit(0)

signal.signal(signal.SIGINT, shutdown)
signal.signal(signal.SIGTERM, shutdown)

backend_proc.wait()
frontend_proc.wait()
