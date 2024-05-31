from typing import List
from langchain.agents.agent_types import AgentType
from .config import Configuration
from .settings import ModelConfig, IOInputConfig, IOOutputConfig


class ApplicationState:
    def __init__(self, config: Configuration):
        self.config = config
        self.is_hotkey_enabled: bool = True
        self.is_stopped: bool = False
        self.is_quiet: bool = False

        self.are_tools_enabled: bool = None
        self.input_model: str = None
        self.output_model: str = None
        self.llm_model: str = None
        self.temperature: float = None
        self.prompts: List[str] = []

        self.llm_agent_type: AgentType = None
        self.llm_model_options: ModelConfig = None
        self.input_model_options: IOInputConfig = None
        self.output_model_options: IOOutputConfig = None
        self._reload()

    def get_hash(self) -> str:
        attributes = (
            self.is_stopped,
            self.is_quiet,
            self.input_model,
            self.output_model,
            self.llm_model,
            self.is_hotkey_enabled,
            self.are_tools_enabled,
            self.llm_agent_type,
            self.temperature,
            ";".join(self.prompts),
        )
        return str(hash(attributes))

    def set_llm_model(self, llm: str):
        if llm not in self.config.settings.models:
            raise ValueError(f"Model {llm} definition not found")

        self.llm_model = llm
        self.llm_model_options = self._load_llm_options()
        self._set_llm_agent_type(self.llm_model_options.agent_type or self._get_default_llm_agent_type())
        self.temperature = self.llm_model_options.temperature or self._get_default_temperature()
        self.are_tools_enabled = self.llm_model_options.tools_enabled or self._get_default_tools_are_enabled()
        self._set_prompts(self.llm_model_options.prompts or self.config.settings.agent.prompts)

    def set_input_model(self, model: str):
        self.input_model = model
        self.input_model_options = self.config.settings.io_input.get(self.input_model)

    def set_output_model(self, model: str):
        self.output_model = model
        self.output_model_options = self.config.settings.io_output.get(self.output_model)

    def _set_prompts(self, prompts: List[str]):
        available_prompts = self.config.available_prompts
        self.prompts = [available_prompts[name] for name in prompts if name in available_prompts]

    def _set_llm_agent_type(self, llm_agent_type: str):
        self.llm_agent_type = llm_agent_type

    def _get_default_llm(self) -> str:
        return next(iter(self.config.settings.models))

    def _get_default_input_model(self) -> str:
        return "text"

    def _get_default_output_model(self) -> str:
        return "write"

    def _get_default_llm_agent_type(self) -> str:
        return self.config.settings.agent.agent_type or AgentType.CONVERSATIONAL_REACT_DESCRIPTION

    def _get_default_tools_are_enabled(self) -> bool:
        return self.config.settings.agent.tools_enabled or True

    def _get_default_temperature(self):
        return self.config.settings.agent.temperature or 0

    def _load_llm_options(self) -> ModelConfig:
        return self.config.settings.models.get(self.llm_model)

    def _reload(self):
        self.set_llm_model(self._get_default_llm())
        self.set_input_model(self._get_default_input_model())
        self.set_output_model(self._get_default_output_model())
