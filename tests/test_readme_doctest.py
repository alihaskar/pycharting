"""Run the README's ``pycon`` examples as doctests (#101).

The README documents the API as interactive sessions, which rhiza's README check
(it executes ``python`` fences only) does not run. This test does, with the exact
command the README gives readers: ``python -m doctest README.md``.

It runs in a fresh interpreter rather than through :func:`doctest.testfile`
in-process: the examples start a real chart server and register sessions, and
neither should leak into the pytest worker that runs the rest of the suite.
"""

import subprocess
import sys
from pathlib import Path

README = Path(__file__).resolve().parents[1] / "README.md"


def test_readme_examples_pass_as_doctests():
    """Every ``>>>`` example in README.md produces its documented output."""
    result = subprocess.run(
        [sys.executable, "-m", "doctest", str(README)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=120,
        check=False,
    )
    assert result.returncode == 0, result.stdout
