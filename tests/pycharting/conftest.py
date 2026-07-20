"""Shared fixtures and helpers for the pycharting test suite.

Two building blocks here address the flakiness tracked in #47:

* :func:`_wait_until` / the ``wait_until`` fixture replace fixed ``time.sleep``
  readiness waits with polling, so tests no longer depend on a server (or a
  thread) becoming ready within an arbitrarily chosen sleep window.
* :class:`FakeUvicornServer` / the ``fake_uvicorn`` fixture let behaviour tests
  exercise the full ``ChartServer`` start/stop/thread lifecycle without binding a
  real TCP socket. Real servers in daemon threads under ``pytest -n auto`` were
  the source of the intermittent xdist worker crashes; only genuine integration
  tests now start a real server.
"""

import time
from unittest.mock import patch

import pytest


def _wait_until(predicate, *, timeout: float = 5.0, interval: float = 0.02):
    """Poll ``predicate`` until it returns a truthy value or ``timeout`` elapses.

    Args:
        predicate: Zero-argument callable evaluated repeatedly.
        timeout: Maximum seconds to wait before giving up.
        interval: Seconds to sleep between polls.

    Returns:
        The truthy value returned by ``predicate``.

    Raises:
        AssertionError: If the timeout elapses without ``predicate`` becoming truthy.
    """
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        value = predicate()
        if value:
            return value
        time.sleep(interval)
    value = predicate()
    if value:
        return value
    return pytest.fail(f"condition not met within {timeout}s")


@pytest.fixture
def wait_until():
    """Provide the :func:`_wait_until` polling helper to tests."""
    return _wait_until


class FakeUvicornServer:
    """Drop-in replacement for ``uvicorn.Server`` that binds no network socket.

    ``run()`` blocks like the real server until ``should_exit`` is set (by
    ``ChartServer.stop_server``), so the surrounding thread/lifecycle behaviour is
    exercised faithfully without cross-worker port contention.
    """

    def __init__(self, config):
        """Store the config and initialise the shutdown flag."""
        self.config = config
        self.should_exit = False
        self.started = False

    def run(self):
        """Block until ``should_exit`` is set, mimicking a running server."""
        self.started = True
        while not self.should_exit:
            time.sleep(0.01)


@pytest.fixture
def fake_uvicorn():
    """Patch ``ChartServer``'s uvicorn server with the portless fake."""
    with patch("pycharting.core.lifecycle.uvicorn.Server", FakeUvicornServer):
        yield
