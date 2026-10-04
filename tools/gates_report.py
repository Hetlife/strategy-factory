"""CE-4-01 CLI: print the capital activation gates per class (read-only).

    python3 tools/gates_report.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from portfolio import gates  # noqa: E402

if __name__ == "__main__":
    sys.exit(gates.main())
