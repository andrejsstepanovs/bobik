import requests
import json
from datetime import datetime
from typing import Optional, Dict, List
from langchain_core.callbacks import CallbackManagerForToolRun
from langchain_core.tools import BaseTool
from src.config import Configuration
import dateparser


class WeatherTool(BaseTool):
    """Tool that gets current and upcoming weather."""

    name: str = "weather"
    description: str = (
        "A wrapper around Weather Search. "
        "Useful for when you need to know current or upcoming weather. "
        "Tool have one optional argument that can have values like 'now', 'today', 'tomorrow' or specific date in format 'YYYY-MM-DD'."
        "Returns:"
        "A JSON string representing a weather."
    )
    cache: dict = {}
    config: Configuration = None

    def _run(self, date: str = None, run_manager: Optional[CallbackManagerForToolRun] = None) -> str:
        """Use the tool."""

        now: datetime = datetime.now()
        filter_date: Optional[datetime] = dateparser.parse(date) if date else None
        filter_date_date: str = filter_date.strftime("%Y-%m-%d") if filter_date else now.strftime("%Y-%m-%d")

        if filter_date_date not in self.cache:
            location: str = self.config.prompt_replacements["location"].replace(",", "").replace(" ", "-")
            response: requests.Response = requests.get(f"https://wttr.in/{location}?format=j1")

            weather_info: List[str] = [f"Current time is {now.strftime('%Y-%m-%d %H:%M')}"]

            if response.status_code == 200:
                data = response.json()
                location_info: List[str] = [area['value'] for area in data['nearest_area'][0]['areaName']] + [area['value'] for area in data['nearest_area'][0]['country']]
                weather_info.extend(["Location: " + ", ".join(location_info), ""])

                if not filter_date or filter_date_date == now.strftime("%Y-%m-%d"):
                    current_condition = data['current_condition'][0]
                    weather_info.extend([
                        "# Current Weather:",
                        f"- Condition: {current_condition['weatherDesc'][0]['value']}",
                        f"- Temperature (°C): {current_condition['temp_C']}",
                        f"- Humidity: {current_condition['humidity']}",
                        f"- Cloud Cover (%): {current_condition['cloudcover']}",
                        f"- Wind Speed (km/h): {current_condition['windspeedKmph']}",
                    ])

                weather_info.append("# Forecast:")
                for current_condition in data['weather']:
                    if filter_date and filter_date_date != current_condition['date']:
                        continue
                    weather_info.append(f"- {current_condition['date']}")
                    for description in current_condition['hourly']:
                        time: str = str(description['time']).zfill(4)
                        weather_info.append(f"-- {time[:2]}:{time[2:]}: {description['weatherDesc'][0]['value']}, {description['tempC']}°C, {description['chanceofrain']}% rain, {description['windspeedKmph']} km/h")

            self.cache[filter_date_date] = json.dumps(weather_info)

        return self.cache[filter_date_date]

    async def _arun(self, *args, **kwargs):
        """Use the tool asynchronously. Not implemented."""
        raise NotImplementedError
