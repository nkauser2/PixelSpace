"""Checks that the test suite itself follows the project rules:
  * every test names the requirement it checks (test_r1_... to test_r15_...)
  * every requirement (R1-R8 from Round 1, R9-R10 from Round 2, R11 from Round 3, R12 from Round 4, R13-R14 from Round 5, R15 from Round 6) has tests
"""

import re
from pathlib import Path

TEST_DIR = Path(__file__).parent
LAST_REQUIREMENT = 15
REQUIREMENTS = {f"r{n}" for n in range(1, LAST_REQUIREMENT + 1)}


def all_test_names():
    names = []
    for path in TEST_DIR.glob("test_*.py"):
        names += re.findall(r"^def (test_\w+)\(", path.read_text(encoding="utf-8"), flags=re.MULTILINE)
    return names


def requirement_of(test_name):
    """'test_r9_something' -> 'r9'. Returns None if no known requirement is named."""
    match = re.match(r"test_(r\d+)_", test_name)
    if match and match.group(1) in REQUIREMENTS:
        return match.group(1)
    return None


def test_r1_to_r15_every_test_names_its_requirement():
    """R1-R15: Every test function starts with test_r<number>_ for a real requirement."""
    unlabeled = [n for n in all_test_names() if requirement_of(n) is None]
    assert unlabeled == [], f"These tests don't name a requirement: {unlabeled}"


def test_r1_to_r15_every_requirement_has_tests():
    """R1-R15: Each requirement is checked by at least one test."""
    covered = {requirement_of(n) for n in all_test_names()}
    missing = sorted(REQUIREMENTS - covered, key=lambda r: int(r[1:]))
    assert missing == [], f"No tests found for: {missing}"
