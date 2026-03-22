from __future__ import annotations

import subprocess
import sys
import unittest


class CliEntrypointTests(unittest.TestCase):
    def test_python_module_entrypoint_help(self) -> None:
        proc = subprocess.run(
            [sys.executable, "-m", "futureos", "--help"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="ignore",
            check=False,
        )
        self.assertEqual(proc.returncode, 0)
        output = (proc.stdout or "") + (proc.stderr or "")
        self.assertIn("Usage", output)
        self.assertIn("login", output)


if __name__ == "__main__":
    unittest.main()
