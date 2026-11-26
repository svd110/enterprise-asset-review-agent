"""Runs the demonstration cases and reports whether each behaved as expected."""

import re

from src.agent import run_agent
from src.db import DB_PATH

CASES = [
    ("Needs attention",
     "Should Kosha Bank be concerned about the loan origination system?",
     r"investigate|replace"),
    ("No immediate action",
     "Does Windows Server 2022 (A03) need any action right now?",
     r"maintain"),
    ("Missing information",
     "Review Windows Server 2016 (A02). Should it be maintained, replaced, or investigated?",
     r"investigate"),
    ("Invalid request",
     "Review asset A99.",
     r"not (found|exist)|does not exist|no (such )?asset"),
]

FAILURE_CASE = (
    "Tool failure (database missing)",
    "Which assets need review?",
    r"database|unavailable|error|not found",
)


def run_case(label, question, expected):
    print("=" * 70)
    print(f"CASE: {label}")
    answer, checks = run_agent(question)
    behaved = bool(answer) and re.search(expected, answer, re.IGNORECASE) is not None
    grounded = all(passed for _, passed, _ in checks)
    return label, behaved, grounded


def main():
    results = [run_case(*case) for case in CASES]

    backup = DB_PATH.with_suffix(".db.bak")
    DB_PATH.rename(backup)
    try:
        results.append(run_case(*FAILURE_CASE))
    finally:
        backup.rename(DB_PATH)

    print("=" * 70)
    print("SUMMARY")
    for label, behaved, grounded in results:
        print(f"  {'PASS' if behaved else 'FAIL'}  expected behavior | "
              f"{'PASS' if grounded else 'FAIL'}  grounding | {label}")


if __name__ == "__main__":
    main()