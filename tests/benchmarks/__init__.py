"""Performance benchmarks, run by ``make benchmark``.

Excluded from ``make test`` (``--ignore=tests/benchmarks``) because benchmarks
measure rather than assert, and are unreliable under ``pytest-xdist``.
"""
