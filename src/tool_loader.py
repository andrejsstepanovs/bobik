from typing import List
import os
import yaml
from langchain.agents import load_tools
from langchain_core.tools import BaseTool
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
from typing import Any, Dict, List, Union, Optional


class ToolLoader:
    def __init__(self, config: Configuration, state: ApplicationState):
        self.state = state
        self.config = config
        self.memory: ConversationBufferMemory = None
        self.tools: List[BaseTool] = []

    def set_memory(self, memory: ConversationBufferMemory):
        self.memory = memory

    def add_tool(self, tool: BaseTool):
        if tool is not None:
            self.tools.append(tool)

    def get_tools(self) -> List[BaseTool]:
        if self.tools:
            return self.tools

        self.tools: List[BaseTool] = []
        try:
            self._add_tools_based_on_config()
        except Exception as e:
            print(f"Tool loading error occurred: {e}")
            quit(1)
        return self.tools

    def _is_tool_enabled(self, name: str) -> bool:
        return bool(self.config.settings.tools.get(name).enabled) if self.config.settings.tools else False

    def _add_tools_based_on_config(self):
        tool_config_methods = {
            "bing_search": lambda: self.add_tool(self._get_bing_search_tool()),
            "bing_news": lambda: self.add_tool(self._get_bing_news_tool()),
            "wttr_weather": lambda: self.add_tool(self._get_weather_tool()),
            "ics_calendar": lambda: self.add_tool(self._get_calendar_tool()),
            "enable_disable_tools": lambda: self.add_tool(state_tools.SetToolUsage(state=self.state)),
            "end_conversation": lambda: self.add_tool(state_tools.EndConversation(state=self.state)),
            "change_model": lambda: self.add_tool(state_tools.SwitchModel(state=self.state, config=self.config)),
            "available_models": lambda: self.add_tool(state_tools.RetrieveModels(config=self.config)),
            "output_switch": lambda: self.add_tool(state_tools.SwitchOutputMethod(state=self.state)),
            "input_switch": lambda: self.add_tool(state_tools.SwitchInputMethod(state=self.state)),
            "date_time_tool": lambda: self.add_tool(datetime_tools.TimeTool()),
            "clear_memory": lambda: self.add_tool(state_tools.ResetChat(state=self.state)),
            "wikipedia": lambda: self.tools.extend(load_tools(['wikipedia'])),
            "google_search": lambda: self.tools.extend(load_tools(["serpapi"])) if self.config.api_keys["serpapi"] else None,
        }

        for name in self.available_tool_names():
            if name in tool_config_methods:
                tool_config_methods[name]()

    def call_tool(self, name: str, param: str = None) -> tuple[str, str]:
        for tool in self.get_tools():
            if tool.name == name:
                input: Union[str, Dict[str, Any]] = param
                verbose: Optional[bool] = True
                response = tool.run(tool_input=input, verbose=verbose)
                return name, str(response)
        return "", ""

    def available_tool_names(self) -> List[str]:
        tools_names = [
            "bing_search",
            "bing_news",
            "wttr_weather",
            "ics_calendar",
            "enable_disable_tools",
            "end_conversation",
            "change_model",
            "available_models",
            "output_switch",
            "input_switch",
            "date_time_tool",
            "clear_memory",
            "wikipedia",
            "google_search",
        ]
        return [tool_name for tool_name in tools_names if self._is_tool_enabled(tool_name)]

    def _get_bing_search_tool(self) -> BaseTool:
        if self.config.api_keys["bing"] is not None:
            bing_api = BingSearchAPIWrapper(
                bing_subscription_key=self.config.api_keys["bing"],
                bing_search_url=self.config.urls["bing"]["search"],
            )
            return BingSearchResults(api_wrapper=bing_api)

    def _get_bing_news_tool(self) -> BaseTool:
        if self.config.api_keys["bing"] is not None and self.config.urls["bing"]["news"]:
            return news_tools.NewsRetrievalTool(
                bing_search_url=self.config.urls["bing"]["news"],
                subscription_key=self.config.api_keys["bing"],
            )

    def _get_weather_tool(self) -> BaseTool:
        return WeatherTool(config=self.config)

    def _get_calendar_tool(self) -> BaseTool:
        calendar_config_file = self.config.settings.tools.ics_calendar.config_file
        try:
            with open(calendar_config_file, "r") as file:
                calendar_options = yaml.safe_load(file)
                calendar = Calendar(state=self.state, options=calendar_options)
                return calendar_tools.CalendarEventTool(calendar=calendar)
        except FileNotFoundError:
            print(f"File {calendar_config_file} not found, skipping calendar tool...")
            return None
