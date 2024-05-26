import os
import yaml
from langchain.agents import load_tools
from app.config import Configuration
from app.state import ApplicationState
from langchain_community.utilities.bing_search import BingSearchAPIWrapper
from langchain_community.tools.bing_search.tool import BingSearchResults
import app.tools.state as state_tools
import app.tools.news as news_tools
import app.tools.datetime as datetime_tools
import app.tools.my_calendar as calendar_tools
from app.tools.weather import WeatherTool
from app.pkg.my_calendar import Calendar
from langchain.memory import ConversationBufferMemory
from langchain_community.utilities import SerpAPIWrapper
from app.my_print import print_text


class ToolLoader:
    def __init__(self, config: Configuration, state: ApplicationState):
        self.state = state
        self.config = config
        self.memory = None
        self.other_tools = []

    def set_memory(self, memory: ConversationBufferMemory):
        self.memory = memory

    def add_tool(self, tool: list):
        self.other_tools.append(tool)

    def get_tools(self):
        tools = []
        if len(self.other_tools) > 0:
            tools.extend(self.other_tools)

        self.add_wttr_weather_tool(tools)
        self.add_my_calendar_tool(tools)
        self.add_bing_search_tool(tools)
        self.add_bing_news_tool(tools)

        if self.is_tool_enabled("enable_disable_tools"):
            tools.append(state_tools.SetToolUsage(state=self.state))

        if self.is_tool_enabled("end_conversation"):
            tools.append(state_tools.EndConversation(state=self.state))

        if self.is_tool_enabled("model_switch"):
            tools.append(state_tools.SwitchModel(state=self.state, config=self.config))

        if self.is_tool_enabled("available_models"):
            tools.append(state_tools.RetrieveModels(config=self.config))

        if self.is_tool_enabled("output_switch"):
            tools.append(state_tools.SwitchOutputMethod(state=self.state))

        if self.is_tool_enabled("input_switch"):
            tools.append(state_tools.SwitchInputMethod(state=self.state))

        if self.is_tool_enabled("date_time_tool"):
            tools.append(datetime_tools.TimeTool())

        if self.is_tool_enabled("clear_memory"):
            tools.append(state_tools.ResetChat(memory=self.memory))

        if self.is_tool_enabled("wikipedia"):
            tools.extend(load_tools(['wikipedia']))

        if self.is_tool_enabled("google_search") and self.config.serpapi_settings["api_key"] is not None:
            tools.extend(load_tools(["serpapi"]))

        return tools

    def is_tool_enabled(self, name: str) -> bool:
        if self.config.settings.tools is None:
            return False
        return bool(self.config.settings.tools.get(name).enabled)

    def add_bing_search_tool(self, tools: list):
        if self.is_tool_enabled("bing_search") and self.config.bing_settings["subscription_key"] is not None:
            print_text(state=self.state, text="Using Bing Search Tool")
            bing_api = BingSearchAPIWrapper(
                bing_subscription_key=self.config.bing_settings["subscription_key"],
                bing_search_url=self.config.bing_settings["url"]["search"]
            )
            search = BingSearchResults(api_wrapper=bing_api)
            tools.append(search)

    def add_bing_news_tool(self, tools: list):
        if self.is_tool_enabled("bing_news") and self.config.bing_settings["subscription_key"] is not None:
            print_text(state=self.state, text="Using Bing News Tool")
            if self.config.bing_settings["url"]["news"]:
                news_search = news_tools.NewsRetrievalTool(
                    bing_search_url=self.config.bing_settings["url"]["news"],
                    subscription_key=self.config.bing_settings["subscription_key"]
                )
                tools.append(news_search)

    def add_wttr_weather_tool(self, tools: list):
        if self.is_tool_enabled("wttr_weather"):
            print_text(state=self.state, text="Using Wttr Weather Tool")
            tools.append(WeatherTool(config=self.config))

    def add_my_calendar_tool(self, tools: list):
        if self.is_tool_enabled("ics_calendar"):
            calendar_config_file = self.config.settings.tools.ics_calendar.config_file
            if not os.path.exists(calendar_config_file):
                raise FileNotFoundError(f"File {calendar_config_file} not found")

            with open(calendar_config_file, "r") as file:
                print_text(state=self.state, text="Using My Calendar Tool")
                calendar_options = yaml.safe_load(file)
                calendar = Calendar(state=self.state, options=calendar_options)
                my_calendar_tool = calendar_tools.CalendarEventTool(calendar=calendar)
                tools.append(my_calendar_tool)
