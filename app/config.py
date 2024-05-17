import os
import logging
import time
import datetime


class Configuration:
    def __init__(self, settings: dict):
        self.settings = settings

        self.user_name = self.settings["user"]["name"]
        self.agent_temperature = self.settings["agent"]["temperature"]
        self.agent_name = self.settings["agent"]["name"]
        self.directory = os.path.dirname(os.path.realpath(__file__))

        self.history_file = None
        if self.settings["history"]["enabled"]:
            self.history_file = self.settings["history"]["file"]

        self.deepgram_settings = {
            "url": "https://api.deepgram.com/v1/",
            "api_key": os.getenv("DEEPGRAM_API_KEY"),
        }
        self.groq_settings = {
            "api_key": os.getenv("GROQ_API_KEY"),
        }
        self.google_settings = {
            "api_key": os.getenv("GOOGLE_API_KEY"),
        }
        self.ollama_settings = {
            "url": "http://localhost:11434",
            "enabled": True,
        }
        self.openai_settings = {
            "api_key": os.getenv("OPENAI_API_KEY"),
        }
        self.mistral_settings = {
            "api_key": os.getenv("MISTRAL_API_KEY"),
        }
        self.custom_provider_settings = {
            "api_key": os.getenv("CUSTOM_PROVIDER_API_KEY"),
            "base_url": os.getenv("CUSTOM_PROVIDER_BASE_URL"),
        }
        self.serpapi_settings = {
            "api_key": os.getenv("SERPAPI_API_KEY"),
        }
        self.bing_settings = {
            "subscription_key": os.getenv("BING_SUBSCRIPTION_KEY"),
            "url": {
                "search": os.getenv("BING_SEARCH_URL"),
                "news": os.getenv("BING_NEWS_URL"),
            }
        }
        self.retry_settings = {
            "max_tries": self.settings["agent"]["max_tries"],
            "sleep_seconds_between_tries": self.settings["agent"]["sleep_seconds_between_tries"],
        }
        self.available_prompts = {}
        if len(self.settings["prompts"]) > 0:
            for name, file in self.settings["prompts"].items():
                if not os.path.exists(file):
                    file = os.path.join(self.directory, "..", "prompts", file)
                    if not os.path.exists(file):
                        raise FileNotFoundError(f"Prompt file not found: {file}")
                self.available_prompts[name] = file

        self.prompt_replacements = {
            "agent_name": self.agent_name,
            "user_name": self.user_name,
            "date": time.strftime("%Y-%m-%d"),
            "time": time.strftime("%H:%M:%S"),
            "timezone": str(datetime.datetime.now(datetime.timezone(datetime.timedelta(0))).astimezone().tzinfo),
            "location": self.settings["user"]["location"],
        }
        if "timezone" in self.settings["user"]:
            self.prompt_replacements["timezone"] = self.settings["user"]["timezone"]

        self.exit_phrases = self.settings["phrases"]["exit"]
        self.log_level = logging.ERROR
