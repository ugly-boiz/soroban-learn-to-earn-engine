"""Launch backend and frontend as independent daemon processes."""

import os
import subprocess
import sys
import time

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def launch_backend():
    log_path = os.path.join(PROJECT_ROOT, "backend.log")
    env = os.environ.copy()
    env["SKIP_MODEL_LOAD"] = "1"
    with open(log_path, "w") as log:
        return subprocess.Popen(
            [sys.executable, "-m", "uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"],
            cwd=PROJECT_ROOT,
            stdout=log,
            stderr=log,
            stdin=subprocess.DEVNULL,
            env=env,
            start_new_session=True,
        )


def launch_frontend():
    log_path = os.path.join(PROJECT_ROOT, "frontend.log")
    with open(log_path, "w") as log:
        return subprocess.Popen(
            ["npx", "vite", "--host", "0.0.0.0"],
            cwd=os.path.join(PROJECT_ROOT, "frontend"),
            stdout=log,
            stderr=log,
            stdin=subprocess.DEVNULL,
            start_new_session=True,
        )


if __name__ == "__main__":
    print("Starting backend...")
    be = launch_backend()
    print("  Backend PID:", be.pid)

    print("Starting frontend...")
    fe = launch_frontend()
    print("  Frontend PID:", fe.pid)

    time.sleep(3)

    # Verify they're alive
    if be.poll() is not None:
        print(f"ERROR: Backend exited with code {be.returncode}")
    else:
        print("Backend: running")

    if fe.poll() is not None:
        print(f"ERROR: Frontend exited with code {fe.returncode}")
    else:
        print("Frontend: running")

    print("\nBackend:  http://localhost:8000")
    print("Frontend: http://localhost:5173")
