from typing import Any, Dict, Type, Optional, Union
from .config import Configuration
from .state import ApplicationState
from .my_print import print_text
from langchain_groq import ChatGroq
from langchain_openai import ChatOpenAI
from langchain_google_genai import GoogleGenerativeAI
from langchain_mistralai.chat_models import ChatMistralAI
from langchain_community.llms import VLLMOpenAI


class LanguageModelProvider:
    def __init__(self, config: Configuration, state: ApplicationState):
        self.state: ApplicationState = state
        self.config: Configuration = config

    def get_model(self) -> Any:
        self.state.set_llm_model(self.state.llm_model)
        provider_name: str = self.state.llm_model_options.provider
        model_name: str = self.state.llm_model_options.model
        temperature: float = self.state.temperature

        print_text(
            state=self.state,
            text=f"Model: {self.state.llm_model}, LLM: {model_name}, Provider: {provider_name}, Temp: {self.config.agent_temperature}"
        )

        models: Dict[str, Type] = {
            "google": GoogleGenerativeAI,
            "mistral": ChatMistralAI,
            "groq": ChatGroq,
            "openai": ChatOpenAI,
            "openai_custom": ChatOpenAI,
            "runpod": VLLMOpenAI,
            "lm_studio": ChatOpenAI,
            "ollama": ChatOpenAI,
        }

        model_class: Optional[Type] = models.get(provider_name)
        if model_class is None:
            raise ValueError(f"Provider {provider_name} is not supported.")

        common_params: Dict[str, Union[str, float]] = {
            "model": model_name,
            "temperature": temperature,
        }

        provider_specific_params: Dict[str, Dict[str, str]] = {
            "google": {"google_api_key": self.config.api_keys["google"]},
            "mistral": {"mistralai_api_key": self.config.api_keys["mistral"]},
            "groq": {"groq_api_key": self.config.api_keys["groq"]},
            "openai": {"openai_api_key": self.config.api_keys["openai"]},
            "openai_custom": {
                "openai_api_key": self.config.api_keys["openai_custom"],
            },
            "lm_studio": {
                "base_url": self.config.urls["lm_studio"],
                "openai_api_key": "not-needed",
                "max_tokens": 4096,
            },
            "ollama": {
                "base_url": self.config.urls["ollama"] + "/v1/",
            },
            "runpod": {
                "openai_api_key": self.config.api_keys["runpod"],
                "openai_api_base": self.config.urls["runpod"].replace(
                    "{endpoint_id}",
                    self.state.llm_model_options.endpoint_id if self.state.llm_model_options.endpoint_id else "unknown"
                ),
            }
        }

        if self.state.llm_model_options.base_url is not None:
            provider_specific_params[provider_name]["base_url"] = self.state.llm_model_options.base_url

        try:
            model: Any = model_class(**common_params, **provider_specific_params[provider_name])
            return model
        except KeyError:
            raise ValueError(f"API key for provider {provider_name} is missing.")
