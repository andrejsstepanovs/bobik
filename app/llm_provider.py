from app.config import Configuration
from app.state import ApplicationState
from app.my_print import print_text
from langchain_groq import ChatGroq
from langchain_openai import ChatOpenAI
from langchain_google_genai import GoogleGenerativeAI
from langchain_community.llms import Ollama
from langchain_mistralai.chat_models import ChatMistralAI


class LanguageModelProvider:
    def __init__(self, config: Configuration, state: ApplicationState):
        self.state = state
        self.config = config

    def get_model(self):
        if self.state.llm_model_options.model == "":
            raise ValueError("No model specified.")

        provider_name = self.state.llm_model_options.provider
        model_name = self.state.llm_model_options.model

        print_text(state=self.state, text=f"Model: {self.state.llm_model}, LLM: {model_name}, Provider: {provider_name}, Temp: {self.config.agent_temperature}")

        if provider_name == "google" and self.config.google_settings["api_key"] is not None:
            return GoogleGenerativeAI(
                model=model_name,
                temperature=self.state.temperature,
                google_api_key=self.config.google_settings["api_key"],
            )

        if provider_name == "mistral" and self.config.mistral_settings["api_key"] is not None:
            return ChatMistralAI(
                model_name=model_name,
                temperature=self.state.temperature,
                mistralai_api_key=self.config.mistral_settings["api_key"],
            )

        if provider_name == "groq" and self.config.groq_settings["api_key"] is not None:
            return ChatGroq(
                model_name=model_name,
                temperature=self.state.temperature,
                groq_api_key=self.config.groq_settings["api_key"],
            )

        if provider_name == "openai" and self.config.openai_settings["api_key"] is not None:
            return ChatOpenAI(
                model=model_name,
                temperature=self.state.temperature,
                openai_api_key=self.config.openai_settings["api_key"],
            )

        if provider_name == "openai_custom" and self.config.custom_provider_settings["api_key"] is not None and self.config.custom_provider_settings["base_url"] is not None:
            token = self.config.custom_provider_settings["api_key"]
            model = ChatOpenAI(
                model=model_name,
                temperature=self.state.temperature,
                base_url=self.config.custom_provider_settings["base_url"],
                openai_api_key=token,
            )
            return model

        if provider_name == "lm_studio" and self.config.lmstudio_provider_settings["base_url"] is not None:
            model = ChatOpenAI(
                temperature=self.state.temperature,
                base_url=self.config.lmstudio_provider_settings["base_url"],
                openai_api_key="not-needed",
                max_tokens=4096,
            )
            return model

        if provider_name == "ollama" and self.config.ollama_settings["enabled"]:
            return Ollama(
                model=model_name,
                temperature=self.state.temperature,
                base_url=self.config.ollama_settings["url"],
                #max_tokens=8192,
            )

        raise ValueError(f"model {self.state.llm_model} was not found. Probably it dont have api key set.")
