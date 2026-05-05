"""
main.py — Weather Reporting Agent

ReAct agent that answers natural language weather questions for any city.
Uses the Open-Meteo API (free, no API key required).
"""

import argparse
import sys
import requests
from pydantic import BaseModel, Field
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage
from langgraph.prebuilt import create_react_agent
from common.llm_factory import get_chat_llm
from common.utils import get_logger

logger = get_logger(__name__)

WEATHER_SYSTEM_PROMPT = """You are a weather reporting assistant.

STRICT RULES:
- Always call the get_weather tool to answer weather questions. Never answer from memory or training data.
- Report the temperature, conditions, and wind speed EXACTLY as the tool returns them. Do not paraphrase, round, or substitute synonyms.
- If the tool says "Partly cloudy", output "Partly cloudy". Do NOT say "mostly cloudy" or "cloudy".
- If the tool says "12.4°C", output "12.4°C". Do NOT say "around 12°C" or any other value.
- Populate the structured response fields only with values taken directly from the tool output.
"""


class WeatherReport(BaseModel):
    city: str = Field(description="City name exactly as returned by the tool")
    temperature_celsius: float = Field(description="Temperature exactly as returned by the tool")
    conditions: str = Field(description="Weather description exactly as returned by the tool")
    wind_speed_kmh: float = Field(description="Wind speed exactly as returned by the tool")
    summary: str = Field(description="One sentence using only the above fields, no invented data")


# WMO Weather Code → human-readable description
WMO_CODES = {
    0: "Clear sky",
    1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast",
    45: "Fog", 48: "Icy fog",
    51: "Light drizzle", 53: "Moderate drizzle", 55: "Dense drizzle",
    61: "Slight rain", 63: "Moderate rain", 65: "Heavy rain",
    71: "Slight snow", 73: "Moderate snow", 75: "Heavy snow",
    80: "Slight showers", 81: "Moderate showers", 82: "Violent showers",
    95: "Thunderstorm", 96: "Thunderstorm with hail", 99: "Thunderstorm with heavy hail",
}


@tool
def get_weather(city: str) -> str:
    """
    Get the current weather for a given city name.
    Returns temperature in Celsius, wind speed in km/h, and weather description.
    """
    geo_response = requests.get(
        "https://geocoding-api.open-meteo.com/v1/search",
        params={"name": city, "count": 1},
        timeout=10,
    )
    geo_response.raise_for_status()
    geo_data = geo_response.json()

    if not geo_data.get("results"):
        return f"City '{city}' not found. Please check the spelling."

    result = geo_data["results"][0]
    lat = result["latitude"]
    lon = result["longitude"]
    resolved_name = result["name"]
    country = result.get("country", "")

    weather_response = requests.get(
        "https://api.open-meteo.com/v1/forecast",
        params={
            "latitude": lat,
            "longitude": lon,
            "current": "temperature_2m,windspeed_10m,weathercode",
            "timezone": "auto",
        },
        timeout=10,
    )
    weather_response.raise_for_status()
    current = weather_response.json()["current"]

    temperature = current["temperature_2m"]
    windspeed = current["windspeed_10m"]
    description = WMO_CODES.get(current["weathercode"], f"Weather code {current['weathercode']}")

    logger.info("get_weather called for %s → %s°C, %s", city, temperature, description)
    return (
        f"Current weather in {resolved_name}, {country}: "
        f"{temperature}°C, {description}, wind speed {windspeed} km/h."
    )


def build_agent():
    """
    Create a LangGraph ReAct agent with the get_weather tool.
    Uses a strict system prompt and structured output to prevent hallucination.

    Returns:
        Compiled agent graph
    """
    llm = get_chat_llm()
    return create_react_agent(
        model=llm,
        tools=[get_weather],
        prompt=WEATHER_SYSTEM_PROMPT,
    )


def ask(agent, question: str) -> str:
    """
    Invoke the agent with a single natural language question.

    Args:
        agent: Compiled LangGraph agent
        question: Natural language weather question

    Returns:
        Formatted weather report sourced strictly from tool output
    """
    result = agent.invoke({"messages": [HumanMessage(content=question)]})
    report: WeatherReport = result["structured_response"]
    return (
        f"{report.city}: {report.temperature_celsius}°C, "
        f"{report.conditions}, wind {report.wind_speed_kmh} km/h.\n"
        f"{report.summary}"
    )


def main():
    """Main entry point — supports CLI city argument, interactive mode, or default demo queries."""
    parser = argparse.ArgumentParser(description="Weather Reporting Agent")
    parser.add_argument(
        "city",
        nargs="?",
        help="City name to get weather for (e.g. 'Paris' or 'New York')",
    )
    parser.add_argument(
        "--interactive", "-i",
        action="store_true",
        help="Start an interactive prompt loop to query any city",
    )
    args = parser.parse_args()

    logger.info("Starting Weather Reporting Agent...")
    agent = build_agent()

    def _run(question: str) -> None:
        logger.info("Q: %s", question)
        answer = ask(agent, question)
        logger.info("A: %s", answer)
        print(f"\nQ: {question}")
        print(f"A: {answer}")
        print("-" * 60)

    if args.city:
        # Single city passed as CLI argument
        _run(f"What is the current weather in {args.city}?")

    elif args.interactive:
        # Interactive REPL — keeps agent in memory between queries
        print("Weather Agent (interactive) — type a city name or question, 'quit' to exit.\n")
        while True:
            try:
                user_input = input("Ask: ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\nExiting.")
                sys.exit(0)
            if not user_input:
                continue
            if user_input.lower() in {"quit", "exit", "q"}:
                print("Exiting.")
                sys.exit(0)
            _run(user_input)

    else:
        # Default demo: three hardcoded cities
        questions = [
            "What is the weather like in Tokyo right now?",
            "Tell me the current temperature in London.",
            "Is it raining in Sydney today?",
        ]
        for question in questions:
            _run(question)


if __name__ == "__main__":
    main()
