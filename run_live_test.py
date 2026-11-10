"""Launches HalluGuard backend and runs live E2E tests against it."""

import subprocess
import sys
import time
import httpx


def run() -> int:
    python_exe = r"F:\final project\LettuceDetect\.venv\Scripts\python.exe"
    backend_dir = r"F:\final project\HalluGuard\backend"

    print("Launching HalluGuard FastAPI server...")
    server_process = subprocess.Popen(
        [python_exe, "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "8000"],
        cwd=backend_dir,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )

    try:
        # Wait for server to be responsive
        print("Waiting for server startup & LettuceDetect model loading...")
        start_time = time.time()
        ready = False
        client = httpx.Client(base_url="http://127.0.0.1:8000", timeout=5.0)

        for attempt in range(40):
            try:
                res = client.get("/health")
                if res.status_code == 200 and res.json().get("detector_loaded"):
                    print(f"Server is ready after {time.time() - start_time:.2f}s!")
                    ready = True
                    break
            except Exception:
                pass
            time.sleep(1.0)

        if not ready:
            print("ERROR: Server failed to start within 40 seconds.")
            return 1

        # Run test_e2e.py
        import test_e2e
        result = test_e2e.test_live_server()
        return result
    finally:
        print("Terminating test server...")
        server_process.terminate()
        try:
            server_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            server_process.kill()
        print("Server stopped.")


if __name__ == "__main__":
    sys.exit(run())

