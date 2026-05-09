"""test_main.py — Tests for 03_weather_reporting_agent."""

import pytest
import requests
from unittest.mock import Mock, patch, call
from langchain_core.messages import AIMessage

from src.main import get_weather, build_agent, ask, main, WMO_CODES


# ---------------------------------------------------------------------------
# get_weather tool
# ---------------------------------------------------------------------------

class TestGetWeather:
    def test_valid_city_returns_weather_string(
        self, geocode_response, weather_response
    ):
        """Tool returns a formatted string for a known city."""
        geo_mock = Mock()
        geo_mock.raise_for_status = Mock()
        geo_mock.json.return_value = geocode_response

        weather_mock = Mock()
        weather_mock.raise_for_status = Mock()
        weather_mock.json.return_value = weather_response

        with patch("src.main.requests.get", side_effect=[geo_mock, weather_mock]):
            result = get_weather.invoke({"city": "Berlin"})

        assert "Berlin" in result
        assert "Germany" in result
        assert "12.4\u00b0C" in result
        assert "18.2 km/h" in result
        assert "Partly cloudy" in result

    def test_unknown_wmo_code_shows_code_number(
        self, geocode_response
    ):
        """Unknown WMO code falls back to 'Weather code N'."""
        weather_mock_data = {
            "current": {"temperature_2m": 5.0, "windspeed_10m": 3.0, "weathercode": 999}
        }
        geo_mock = Mock()
        geo_mock.raise_for_status = Mock()
        geo_mock.json.return_value = geocode_response

        weather_mock = Mock()
        weather_mock.raise_for_status = Mock()
        weather_mock.json.return_value = weather_mock_data

        with patch("src.main.requests.get", side_effect=[geo_mock, weather_mock]):
            result = get_weather.invoke({"city": "Berlin"})

        assert "Weather code 999" in result

    def test_city_not_found_returns_message(self):
        """Tool returns a user-friendly message when geocoding finds nothing."""
        geo_mock = Mock()
        geo_mock.raise_for_status = Mock()
        geo_mock.json.return_value = {"results": []}

        with patch("src.main.requests.get", return_value=geo_mock):
            result = get_weather.invoke({"city": "Xyzabc123"})

        assert "not found" in result
        assert "Xyzabc123" in result

    def test_geocode_network_error_propagates(self):
        """requests.Timeout raised by geocode call propagates to caller."""
        with patch(
            "src.main.requests.get", side_effect=requests.exceptions.Timeout
        ):
            with pytest.raises(requests.exceptions.Timeout):
                get_weather.invoke({"city": "Tokyo"})

    def test_weather_api_http_error_propagates(self, geocode_response):
        """HTTPError from the forecast call propagates to caller."""
        geo_mock = Mock()
        geo_mock.raise_for_status = Mock()
        geo_mock.json.return_value = geocode_response

        weather_mock = Mock()
        weather_mock.raise_for_status.side_effect = requests.exceptions.HTTPError("500")

        with patch("src.main.requests.get", side_effect=[geo_mock, weather_mock]):
            with pytest.raises(requests.exceptions.HTTPError):
                get_weather.invoke({"city": "Berlin"})

    def test_city_without_country_field(self):
        """Tool handles geocoding results that omit the 'country' key."""
        geo_mock = Mock()
        geo_mock.raise_for_status = Mock()
        geo_mock.json.return_value = {
            "results": [{"name": "NoCountryCity", "latitude": 10.0, "longitude": 20.0}]
        }
        weather_mock = Mock()
        weather_mock.raise_for_status = Mock()
        weather_mock.json.return_value = {
            "current": {"temperature_2m": 30.0, "windspeed_10m": 5.0, "weathercode": 0}
        }
        with patch("src.main.requests.get", side_effect=[geo_mock, weather_mock]):
            result = get_weather.invoke({"city": "NoCountryCity"})

        assert "NoCountryCity" in result
        assert "Clear sky" in result


# ---------------------------------------------------------------------------
# WMO_CODES coverage
# ---------------------------------------------------------------------------

class TestWmoCodes:
    def test_all_expected_codes_present(self):
        """Spot-check that key WMO codes are in the mapping."""
        for code in (0, 1, 2, 3, 45, 61, 63, 65, 71, 80, 95):
            assert code in WMO_CODES


# ---------------------------------------------------------------------------
# build_agent
# ---------------------------------------------------------------------------

class TestBuildAgent:
    def test_build_agent_returns_agent(self, mock_chat_llm):
        """build_agent() returns a compiled graph without errors."""
        agent = build_agent()
        assert agent is not None
        # Mock prevents real API calls; just verify agent was created


# ---------------------------------------------------------------------------
# ask
# ---------------------------------------------------------------------------

class TestAsk:
    def test_ask_returns_last_message_content(self):
        """ask() returns the content of the final AIMessage."""
        final_message = AIMessage(content="It is 22°C in Tokyo.")
        mock_agent = Mock()
        mock_agent.invoke.return_value = {
            "messages": [Mock(), final_message]
        }
        result = ask(mock_agent, "What is the weather in Tokyo?")
        assert result == "It is 22°C in Tokyo."
        mock_agent.invoke.assert_called_once()


# ---------------------------------------------------------------------------
# main()
# ---------------------------------------------------------------------------

class TestMain:
    @pytest.mark.integration
    @pytest.mark.skip(reason="Requires running Ollama server - test manually before PR merge")
    def test_main_runs_without_error(self, capsys):
        """main() runs with real Ollama - MANUAL TEST ONLY."""
        # This is an integration test with real LLM calls
        # Run manually: pytest -m integration --run-integration-real
        main([])

        captured = capsys.readouterr()
        assert "Tokyo" in captured.out
        assert "London" in captured.out
        assert "Sydney" in captured.out

