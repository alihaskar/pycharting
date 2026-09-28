"""Stress and load tests, run by ``make stress`` (selected via ``-m stress``).

Excluded from ``make test`` (``--ignore=tests/stress``) because these push
volume and concurrency rather than assert a single behaviour, and are slower
than the unit suite.
"""
