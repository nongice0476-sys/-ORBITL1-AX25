"""Run test suite, collect detailed execution data, and emit test_results.json."""

from __future__ import annotations

import hashlib
import json
import os
import platform
import sys
import time
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


class DetailedTestResult(unittest.TextTestResult):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.records: list[dict] = []
        self._test_start_time = 0.0

    def startTest(self, test):
        super().startTest(test)
        self._test_start_time = time.perf_counter()

    def addSuccess(self, test):
        super().addSuccess(test)
        elapsed = time.perf_counter() - self._test_start_time
        self.records.append({
            "id": test.id(),
            "name": test._testMethodName,
            "suite": test.__class__.__name__,
            "module": test.__class__.__module__,
            "status": "PASS",
            "duration_sec": round(elapsed, 4),
            "doc": (test._testMethodDoc or "").strip(),
        })

    def addFailure(self, test, err):
        super().addFailure(test, err)
        elapsed = time.perf_counter() - self._test_start_time
        self.records.append({
            "id": test.id(),
            "name": test._testMethodName,
            "suite": test.__class__.__name__,
            "module": test.__class__.__module__,
            "status": "FAIL",
            "duration_sec": round(elapsed, 4),
            "error": self._exc_info_to_string(err, test),
            "doc": (test._testMethodDoc or "").strip(),
        })

    def addError(self, test, err):
        super().addError(test, err)
        elapsed = time.perf_counter() - self._test_start_time
        self.records.append({
            "id": test.id(),
            "name": test._testMethodName,
            "suite": test.__class__.__name__,
            "module": test.__class__.__module__,
            "status": "ERROR",
            "duration_sec": round(elapsed, 4),
            "error": self._exc_info_to_string(err, test),
            "doc": (test._testMethodDoc or "").strip(),
        })


def compute_file_hashes() -> dict[str, str]:
    files = [
        "src/ax25.py",
        "src/ax25_hdlc.py",
        "src/ax25_receiver.py",
        "src/ax25_transmitter.py",
        "src/vendor/mobilinkd/CRC.py",
        "src/vendor/mobilinkd/HDLC.py",
        "src/vendor/mobilinkd/LICENSE",
        "tests/test_ax25_core.py",
        "tests/test_hdlc.py",
        "tests/test_receiver.py",
        "tests/test_reliability.py",
        "tests/test_integration.py",
        "tests/test_acceptance.py",
    ]
    hashes = {}
    for rel in files:
        full = ROOT / rel
        if full.is_file():
            with open(full, "rb") as fp:
                hashes[rel] = hashlib.sha256(fp.read()).hexdigest()
    return hashes


def main() -> int:
    os.chdir(ROOT)
    loader = unittest.TestLoader()
    suite = loader.discover("tests")

    runner = unittest.TextTestRunner(resultclass=DetailedTestResult, verbosity=2)
    start = time.perf_counter()
    result = runner.run(suite)
    duration = time.perf_counter() - start

    # Retrieve benchmark metrics if available
    benchmark = {}
    mod = sys.modules.get("test_acceptance") or sys.modules.get("tests.test_acceptance")
    if mod:
        cls = getattr(mod, "TestPerformanceAndMemoryBehavior", None)
        if cls and hasattr(cls, "last_benchmark"):
            benchmark = cls.last_benchmark

    summary = {
        "timestamp_iso": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "python_version": sys.version,
        "platform": platform.platform(),
        "total_tests": result.testsRun,
        "passed": result.testsRun - len(result.failures) - len(result.errors),
        "failures": len(result.failures),
        "errors": len(result.errors),
        "skipped": len(result.skipped),
        "total_duration_sec": round(duration, 3),
        "success": result.wasSuccessful(),
        "file_hashes": compute_file_hashes(),
        "throughput_benchmark": benchmark,
        "tests": result.records,
    }

    out_path = ROOT / "docs" / "project" / "test_results.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as fp:
        json.dump(summary, fp, indent=2)

    print(f"\nSaved machine-readable test summary to: {out_path}")
    print(f"Total tests: {result.testsRun} | Passed: {summary['passed']} | Failures: {len(result.failures)} | Errors: {len(result.errors)}")
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    sys.exit(main())
