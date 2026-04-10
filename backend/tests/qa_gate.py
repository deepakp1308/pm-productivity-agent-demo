#!/usr/bin/env python3
"""QA gate script — runs all pytest tests and prints a color-coded summary.

Exit 0 if all tests pass, exit 1 if any fail.
"""

import subprocess
import sys
import os

# ANSI color codes
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BOLD = "\033[1m"
RESET = "\033[0m"


def main():
    tests_dir = os.path.dirname(os.path.abspath(__file__))

    print(f"\n{BOLD}{'=' * 60}{RESET}")
    print(f"{BOLD}  PM Productivity Agent — QA Gate{RESET}")
    print(f"{BOLD}{'=' * 60}{RESET}\n")

    result = subprocess.run(
        [sys.executable, "-m", "pytest", tests_dir, "-v", "--tb=short", "-q"],
        capture_output=True,
        text=True,
        cwd=os.path.dirname(os.path.dirname(tests_dir)),  # project root
    )

    # Print test output
    print(result.stdout)
    if result.stderr:
        print(result.stderr)

    # Parse results from the last line of pytest output
    lines = result.stdout.strip().split("\n")
    summary_line = lines[-1] if lines else ""

    passed = 0
    failed = 0
    errors = 0
    total = 0

    # Parse "X passed, Y failed, Z error" style output
    import re
    m_passed = re.search(r"(\d+) passed", summary_line)
    m_failed = re.search(r"(\d+) failed", summary_line)
    m_errors = re.search(r"(\d+) error", summary_line)

    if m_passed:
        passed = int(m_passed.group(1))
    if m_failed:
        failed = int(m_failed.group(1))
    if m_errors:
        errors = int(m_errors.group(1))

    total = passed + failed + errors

    # Print summary
    print(f"\n{BOLD}{'=' * 60}{RESET}")
    print(f"{BOLD}  QA Gate Summary{RESET}")
    print(f"{'=' * 60}")
    print(f"  {GREEN}Passed:  {passed}{RESET}")
    if failed:
        print(f"  {RED}Failed:  {failed}{RESET}")
    if errors:
        print(f"  {RED}Errors:  {errors}{RESET}")
    print(f"  Total:   {total}")
    print(f"{'=' * 60}")

    if failed == 0 and errors == 0:
        print(f"\n  {GREEN}{BOLD}ALL TESTS PASSED{RESET}\n")
        return 0
    else:
        print(f"\n  {RED}{BOLD}SOME TESTS FAILED{RESET}\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())
