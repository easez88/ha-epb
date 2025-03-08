"""Test configuration for EPB API client."""

import logging

import pytest

# Configure logging for tests
logging.basicConfig(level=logging.DEBUG)


@pytest.fixture(autouse=True)
def no_http_requests(monkeypatch):
    """Prevent any real HTTP requests during tests."""

    def urlopen_mock(self, method, url, *args, **kwargs):
        raise RuntimeError(f"The test was about to {method} {url}")

    monkeypatch.setattr("aiohttp.ClientSession._request", urlopen_mock)
