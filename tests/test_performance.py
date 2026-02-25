"""Performance tests for app load time and feature runtime."""

import importlib.util
import os
import socket
import subprocess
import sys
import time
import urllib.request
import unittest

from finance_app.logic import analyze_data, calculate_health_score, validate_file


COLD_LOAD_MAX_SECONDS = float(os.getenv("LOAD_TIME_COLD_MAX_SECONDS", "8.0"))
WARM_LOAD_MAX_SECONDS = float(os.getenv("LOAD_TIME_WARM_MAX_SECONDS", "3.0"))
FEATURE_RUNTIME_MAX_SECONDS = float(os.getenv("FEATURE_RUNTIME_MAX_SECONDS", "1.5"))


def _get_free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("", 0))
        return sock.getsockname()[1]


def _wait_for_server(url, timeout_seconds=30.0):
    start = time.perf_counter()
    while time.perf_counter() - start < timeout_seconds:
        try:
            with urllib.request.urlopen(url, timeout=2.0) as response:
                if response.status == 200:
                    return True
        except Exception:
            time.sleep(0.2)
    return False


def _streamlit_available():
    return importlib.util.find_spec("streamlit") is not None


class TestPerformance(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.test_file = "test_data.xlsx"
        cls.test_data = {
            "Date": ["1/1/2026", "2/1/2026"],
            "Name": ["Rent", "Groceries"],
            "Type": ["Needs", "Needs"],
            "Amount": [1000, 200],
            "Category": ["Rent", "Food"],
        }
        import pandas as pd

        pd.DataFrame(cls.test_data).to_excel(cls.test_file, index=False)

    @classmethod
    def tearDownClass(cls):
        import os

        if os.path.exists(cls.test_file):
            os.remove(cls.test_file)

    def test_feature_runtime_within_time_limit(self):
        valid, df = validate_file(self.test_file)
        self.assertTrue(valid)

        start_time = time.perf_counter()
        needs, wants, savings, _top_wants = analyze_data(df, 1200)
        score = calculate_health_score(1200, needs, wants, savings)
        elapsed = time.perf_counter() - start_time

        self.assertIsInstance(score, int)
        self.assertLess(
            elapsed,
            FEATURE_RUNTIME_MAX_SECONDS,
            f"Feature runtime exceeded time limit: {elapsed:.3f}s",
        )

    def test_webapp_load_time_cold_and_warm(self):
        if not _streamlit_available():
            self.skipTest("Streamlit not available in this environment")

        port = _get_free_port()
        url = f"http://localhost:{port}"

        process = subprocess.Popen(
            [
                sys.executable,
                "-m",
                "streamlit",
                "run",
                "web_app.py",
                "--server.headless",
                "true",
                "--server.address",
                "localhost",
                "--server.port",
                str(port),
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )

        try:
            server_ready = _wait_for_server(url, timeout_seconds=45.0)
            self.assertTrue(server_ready, "Streamlit server did not start in time")

            cold_start = time.perf_counter()
            with urllib.request.urlopen(url, timeout=5.0) as response:
                self.assertEqual(response.status, 200)
                response.read()
            cold_elapsed = time.perf_counter() - cold_start

            warm_start = time.perf_counter()
            with urllib.request.urlopen(url, timeout=5.0) as response:
                self.assertEqual(response.status, 200)
                response.read()
            warm_elapsed = time.perf_counter() - warm_start

            self.assertLess(
                cold_elapsed,
                COLD_LOAD_MAX_SECONDS,
                f"Cold load exceeded time limit: {cold_elapsed:.3f}s",
            )
            self.assertLess(
                warm_elapsed,
                WARM_LOAD_MAX_SECONDS,
                f"Warm load exceeded time limit: {warm_elapsed:.3f}s",
            )
        finally:
            process.terminate()
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()
