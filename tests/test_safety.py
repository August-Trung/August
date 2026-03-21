from __future__ import annotations

import unittest
from pathlib import Path

from futureos.safety import (
    AUDIT_CHAIN_FILE,
    AUDIT_FILE,
    HISTORY_CHAIN_FILE,
    HISTORY_FILE,
    verify_chain,
    write_audit,
    write_history,
)


class SafetyTests(unittest.TestCase):
    def setUp(self) -> None:
        for p in [HISTORY_FILE, AUDIT_FILE, HISTORY_CHAIN_FILE, AUDIT_CHAIN_FILE]:
            Path(p).unlink(missing_ok=True)

    def test_history_chain_verify(self) -> None:
        write_history({"event": "a"})
        write_history({"event": "b"})
        self.assertTrue(verify_chain(HISTORY_FILE, HISTORY_CHAIN_FILE))

    def test_audit_chain_verify(self) -> None:
        write_audit({"event": "x"})
        write_audit({"event": "y"})
        self.assertTrue(verify_chain(AUDIT_FILE, AUDIT_CHAIN_FILE))


if __name__ == "__main__":
    unittest.main()
