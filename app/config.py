import os
import logging
import time
import datetime
from typing import Optional, Dict, Union, List
from .settings import Settings


class Configuration:
    def __init__(self, settings: Settings):
        self.settings = settings

        self.keypress_count_start_talking: int = 3
        self.keypress_count_stop_listening: int = 2

        self.user_name: str = settings.user.name
        self.agent_temperature: float = settings.agent.temperature
        self.agent_name: str = settings.agent.name
        self.directory: str = os.path.dirname(os.path.realpath(__file__))

        self.history_file: Optional[str] = settings.history.file if settings.history.enabled else None

        self.api_keys: Dict[str, str] = {
            "deepgram": os.getenv("DEEPGRAM_API_KEY"),
            "groq": os.getenv("GROQ_API_KEY"),
            "google": os.getenv("GOOGLE_API_KEY"),
            "openai": os.getenv("OPENAI_API_KEY"),
            "mistral": os.getenv("MISTRAL_API_KEY"),
            "openai_custom": os.getenv("CUSTOM_PROVIDER_API_KEY"),
            "serpapi": os.getenv("SERPAPI_API_KEY"),
            "bing": os.getenv("BING_SUBSCRIPTION_KEY"),
        }

        self.urls: Dict[str, Union[str, Dict[str, str]]] = {
            "ollama": "http://localhost:11434",
            "deepgram": "https://api.deepgram.com/v1/",
            "lm_studio": os.getenv("LMSTUDIO_PROVIDER_BASE_URL"),
            "openai_custom": os.getenv("CUSTOM_PROVIDER_BASE_URL"),
            "bing": {
                "search": os.getenv("BING_SEARCH_URL"),
                "news": os.getenv("BING_NEWS_URL"),
            }
        }

        self.retry_settings: Dict[str, int] = {
            "max_tries": settings.agent.max_tries,
            "sleep_seconds_between_tries": settings.agent.sleep_seconds_between_tries,
        }

        self.available_prompts: Dict[str, str] = {name: self._get_prompt_file(file) for name, file in settings.prompts.items()}

        self.prompt_replacements: Dict[str, Union[str, datetime.timezone]] = {
            "agent_name": self.agent_name,
            "user_name": self.user_name,
            "date": time.strftime("%Y-%m-%d"),
            "time": time.strftime("%H:%M:%S"),
            "timezone": settings.user.timezone if settings.user.timezone else str(datetime.datetime.now(datetime.timezone(datetime.timedelta(0))).astimezone().tzinfo),
            "location": settings.user.location,
        }

        self.phrases: Dict[str, List[str]] = {
            "separator": [" .."],
            "exit": settings.phrases.exit,
            "clear_memory": settings.phrases.clear_memory,
            "run_once": settings.phrases.run_once,
            "quiet": settings.phrases.quiet,
            "verbose": settings.phrases.verbose,
            "no_tools": settings.phrases.no_tools,
            "with_tools": settings.phrases.with_tools,
        }

        self.log_level: int = logging.ERROR

    def _get_prompt_file(self, file: str) -> str:
        if not os.path.exists(file):
            file = os.path.join(self.directory, "..", "prompts", file)
            if not os.path.exists(file):
                raise FileNotFoundError(f"Prompt file not found: {file}")
        return file
