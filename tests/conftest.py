"""Conftest for pytest."""

import os
import sys
from pathlib import Path

import pytest

# Add the parent directory to the path so that custom_components can be imported
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import pytest-homeassistant-custom-component fixtures
pytest_plugins = ["pytest_homeassistant_custom_component"]
