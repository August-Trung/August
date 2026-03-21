from __future__ import annotations

import subprocess
import sys


def main() -> int:
    steps = [
        [sys.executable, "scripts/execute_testcases.py"],
        [sys.executable, "scripts/check_testcases.py"],
        [sys.executable, "-m", "unittest", "discover", "-s", "tests"],
        [sys.executable, "-m", "compileall", "."],
    ]
    for cmd in steps:
        print(f"$ {' '.join(cmd)}")
        proc = subprocess.run(cmd)
        if proc.returncode != 0:
            print(f"FAILED: {' '.join(cmd)}")
            return proc.returncode
    print("Gate passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
