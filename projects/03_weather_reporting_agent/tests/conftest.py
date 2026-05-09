"""
conftest.py — pytest fixtures for 03_weather_reporting_agent.
"""

import sys

from pathlib import Path
import pytest
from unittest.mock import Mock

# Explicitly load this project's src.main module to avoid conflicts with other projects
_project_root = Path(__file__).parent.parent
_src_path = _project_root / "src"
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

# Remove any cached src.main from other projects to ensure we get THIS project's src.main
if 'src.main' in sys.modules:
    del sys.modules['src.main']
if 'src' in sys.modules:
    del sys.modules['src']


@pytest.fixture
def mock_chat_llm(mocker):
    """Mock ChatOllama so no real Ollama calls are made."""
    mock = Mock()
    mocker.patch("src.main.get_chat_llm", return_value=mock)
    return mock


@pytest.fixture
def geocode_response():
    """Successful Open-Meteo geocoding API response for Berlin."""
    return {
        "results": [
            {
                "name": "Berlin",
                "country": "Germany",
                "latitude": 52.52,
                "longitude": 13.405,
            }
        ]
    }


@pytest.fixture
def weather_response():
    """Successful Open-Meteo forecast API response."""
    return {
        "current": {
            "temperature_2m": 12.4,
            "windspeed_10m": 18.2,
            "weathercode": 2,
        }
    }

