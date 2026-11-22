"""Checks that the test suite itself follows the project rules:
  * every test names the requirement it checks (test_r1_... to test_r8_...)
  * all eight requirements (R1-R8) have tests
"""

import re
from pathlib import Path

TEST_DIR = Path(__file__).parent
REQUIREMENTS = {f"r{n}" for n in range(1, 9)}


def all_test_names():
    names = []
    for path in TEST_DIR.glob("test_*.py"):
        names += re.findall(r"^def (test_\w+)\(", path.read_text(encoding="utf-8"), flags=re.MULTILINE)
    return names


def test_r1_to_r8_every_test_names_its_requirement():
    """R1-R8: Every test function starts with test_r<number>_."""
    unlabeled = [n for n in all_test_names() if not re.match(r"test_r[1-8]_", n)]
    assert unlabeled == [], f"These tests don't name a requirement: {unlabeled}"


def test_r1_to_r8_every_requirement_has_tests():
    """R1-R8: Each of the eight requirements is checked by at least one test."""
    covered = {m.group(1) for n in all_test_names() if (m := re.match(r"test_(r[1-8])_", n))}
    missing = sorted(REQUIREMENTS - covered)
    assert missing == [], f"No tests found for: {missing}"
