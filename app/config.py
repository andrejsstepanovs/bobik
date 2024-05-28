import os
import logging
import time
import datetime
from app.settings import Settings
from typing import Optional, Dict, Union, List


class Configuration:
    def __init__(self, settings: Settings):
        self.settings = settings

        self.user_name: str = self.settings.user.name
        self.agent_temperature: float = self.settings.agent.temperature
        self.agent_name: str = self.settings.agent.name
        self.directory: str = os.path.dirname(os.path.realpath(__file__))

        self.history_file: Optional[str] = None
        if self.settings.history.enabled:
            self.history_file = self.settings.history.file

        self.deepgram_settings: Dict[str, str] = {
            "url": "https://api.deepgram.com/v1/",
            "api_key": os.getenv("DEEPGRAM_API_KEY"),
        }
        self.groq_settings: Dict[str, str] = {
            "api_key": os.getenv("GROQ_API_KEY"),
        }
        self.google_settings: Dict[str, str] = {
            "api_key": os.getenv("GOOGLE_API_KEY"),
        }
        self.ollama_settings: Dict[str, Union[str, bool]] = {
            "url": "http://localhost:11434",
            "enabled": True,
        }
        self.openai_settings: Dict[str, str] = {
            "api_key": os.getenv("OPENAI_API_KEY"),
        }
        self.mistral_settings: Dict[str, str] = {
            "api_key": os.getenv("MISTRAL_API_KEY"),
        }
        self.custom_provider_settings: Dict[str, str] = {
            "api_key": os.getenv("CUSTOM_PROVIDER_API_KEY"),
            "base_url": os.getenv("CUSTOM_PROVIDER_BASE_URL"),
        }
        self.lmstudio_provider_settings: Dict[str, str] = {
            "base_url": os.getenv("LMSTUDIO_PROVIDER_BASE_URL"),
        }
        self.serpapi_settings: Dict[str, str] = {
            "api_key": os.getenv("SERPAPI_API_KEY"),
        }
        self.bing_settings: Dict[str, Union[str, Dict[str, str]]] = {
            "subscription_key": os.getenv("BING_SUBSCRIPTION_KEY"),
            "url": {
                "search": os.getenv("BING_SEARCH_URL"),
                "news": os.getenv("BING_NEWS_URL"),
            }
        }
        self.retry_settings: Dict[str, int] = {
            "max_tries": self.settings.agent.max_tries,
            "sleep_seconds_between_tries": self.settings.agent.sleep_seconds_between_tries,
        }
        self.available_prompts: Dict[str, str] = {}
        if len(self.settings.prompts) > 0:
            for name, file in self.settings.prompts.items():
                if not os.path.exists(file):
                    file = os.path.join(self.directory, "..", "prompts", file)
                    if not os.path.exists(file):
                        raise FileNotFoundError(f"Prompt file not found: {file}")
                self.available_prompts[name] = file

        self.prompt_replacements: Dict[str, Union[str, datetime.timezone]] = {
            "agent_name": self.agent_name,
            "user_name": self.user_name,
            "date": time.strftime("%Y-%m-%d"),
            "time": time.strftime("%H:%M:%S"),
            "timezone": str(datetime.datetime.now(datetime.timezone(datetime.timedelta(0))).astimezone().tzinfo),
            "location": self.settings.user.location,
        }
        if self.settings.user.timezone is not None:
            self.prompt_replacements["timezone"] = self.settings.user.timezone

        self.exit_phrases: List[str] = self.settings.phrases.exit
        self.no_tools_phrases: List[str] = self.settings.phrases.no_tools
        self.with_tools_phrases: List[str] = self.settings.phrases.with_tools

        self.log_level: int = logging.ERROR
