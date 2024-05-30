from typing import List, Dict, Any
import os
import yaml
from langchain.agents import load_tools

from langchain_community.utilities.bing_search import BingSearchAPIWrapper
from langchain_community.tools.bing_search.tool import BingSearchResults
from langchain.memory import ConversationBufferMemory
from langchain_community.utilities import SerpAPIWrapper
from .tools import state as state_tools
from .tools import news as news_tools
from .tools import datetime as datetime_tools
from .tools import my_calendar as calendar_tools
from .my_print import print_text
from .config import Configuration
from .state import ApplicationState
from .tools.weather import WeatherTool
from .pkg.my_calendar import Calendar

class ToolLoader:
    def __init__(self, config: Configuration, state: ApplicationState):
        self.state = state
        self.config = config
        self.memory: ConversationBufferMemory = None
        self.tools: List[Any] = []

    def set_memory(self, memory: ConversationBufferMemory):
        self.memory = memory

    def add_tool(self, tool: Any):
        self.tools.append(tool)

    def get_tools(self) -> List[Any]:
        self.add_tools_based_on_config()
        return self.tools

    def is_tool_enabled(self, name: str) -> bool:
        return bool(self.config.settings.tools.get(name).enabled) if self.config.settings.tools else False

    def add_tools_based_on_config(self):
        tool_config_methods = {
            "bing_search": self.add_bing_search_tool,
            "bing_news": self.add_bing_news_tool,
            "wttr_weather": self.add_wttr_weather_tool,
            "ics_calendar": self.add_my_calendar_tool,
            "enable_disable_tools": lambda: self.add_tool(state_tools.SetToolUsage(state=self.state)),
            "end_conversation": lambda: self.add_tool(state_tools.EndConversation(state=self.state)),
            "model_switch": lambda: self.add_tool(state_tools.SwitchModel(state=self.state, config=self.config)),
            "available_models": lambda: self.add_tool(state_tools.RetrieveModels(config=self.config)),
            "output_switch": lambda: self.add_tool(state_tools.SwitchOutputMethod(state=self.state)),
            "input_switch": lambda: self.add_tool(state_tools.SwitchInputMethod(state=self.state)),
            "date_time_tool": lambda: self.add_tool(datetime_tools.TimeTool()),
            "clear_memory": lambda: self.add_tool(state_tools.ResetChat(memory=self.memory)),
            "wikipedia": lambda: self.tools.extend(load_tools(['wikipedia'])),
            "google_search": lambda: self.tools.extend(load_tools(["serpapi"])) if self.config.api_keys["serpapi"] else None,
        }

        for tool_name, add_tool_method in tool_config_methods.items():
            if self.is_tool_enabled(tool_name):
                add_tool_method()

    def add_bing_search_tool(self):
        if self.config.api_keys["bing"] is not None:
            print_text(state=self.state, text="Using Bing Search Tool")
            bing_api = BingSearchAPIWrapper(
                bing_subscription_key=self.config.api_keys["bing"],
                bing_search_url=self.config.urls["bing"]["search"],
            )
            search = BingSearchResults(api_wrapper=bing_api)
            self.add_tool(search)

    def add_bing_news_tool(self):
        if self.config.api_keys["bing"] is not None and self.config.urls["bing"]["news"]:
            print_text(state=self.state, text="Using Bing News Tool")
            news_search = news_tools.NewsRetrievalTool(
                bing_search_url=self.config.urls["bing"]["news"],
                subscription_key=self.config.api_keys["bing"],
            )
            self.add_tool(news_search)

    def add_wttr_weather_tool(self):
        print_text(state=self.state, text="Using Wttr Weather Tool")
        self.add_tool(WeatherTool(config=self.config))

    def add_my_calendar_tool(self):
        calendar_config_file = self.config.settings.tools.ics_calendar.config_file
        if not os.path.exists(calendar_config_file):
            raise FileNotFoundError(f"File {calendar_config_file} not found")

        with open(calendar_config_file, "r") as file:
            print_text(state=self.state, text="Using My Calendar Tool")
            calendar_options = yaml.safe_load(file)
            calendar = Calendar(state=self.state, options=calendar_options)
            my_calendar_tool = calendar_tools.CalendarEventTool(calendar=calendar)
            self.add_tool(my_calendar_tool)
