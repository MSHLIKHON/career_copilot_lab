import socket
import subprocess
import sys
import time
import unittest
import urllib.request
from pathlib import Path


class ServerTests(unittest.TestCase):
    def test_local_server_health(self):
        root = Path(__file__).resolve().parents[1]
        with socket.socket() as sock:
            sock.bind(('127.0.0.1', 0))
            port = sock.getsockname()[1]
        process = subprocess.Popen([sys.executable, '-m', 'streamlit', 'run', 'app.py',
                                    '--server.headless', 'true', '--server.address', '127.0.0.1',
                                    '--server.port', str(port)], cwd=root,
                                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        try:
            response = None
            for _ in range(40):
                if process.poll() is not None:
                    self.fail('Streamlit exited before becoming healthy.')
                try:
                    with opener.open(f'http://127.0.0.1:{port}/_stcore/health', timeout=1) as result:
                        response = result.read().decode()
                    break
                except OSError:
                    time.sleep(0.25)
            self.assertEqual(response, 'ok')
        finally:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)
