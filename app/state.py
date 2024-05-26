from app.config import Configuration
from langchain.agents.agent_types import AgentType


class ApplicationState:
    def __init__(self, config: Configuration):
        self.config = config
        self.is_hotkey_enabled = True
        self.is_stopped = False
        self.is_quiet = False

        self.are_tools_enabled = None
        self.input_model = None
        self.output_model = None
        self.llm_model = None
        self.temperature = None
        self.prompts = []

        self.llm_agent_type = None
        self.llm_model_options = None
        self.input_model_options = None
        self.output_model_options = None
        self.reload()

    def reload(self):
        self.set_llm_agent_type(self.get_default_llm_agent_type())
        self.set_llm_model(self.get_default_llm())
        self.set_input_model(self.get_default_input_model())
        self.set_output_model(self.get_default_output_model())

    def get_hash(self) -> str:
        return hash((
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
        ))

    def set_prompts(self, prompts: list):
        for name in prompts:
            if name not in self.config.available_prompts:
                raise ValueError(f"Prompt {name} not found in available prompts. Define them in my_config.yaml first")
            self.prompts.append(self.config.available_prompts[name])

    def set_llm_agent_type(self, llm_agent_type: str):
        self.llm_agent_type = llm_agent_type

    def set_llm_model(self, llm: str):
        if llm not in self.config.settings.models:
            raise ValueError(f"Model {llm} definition not found")

        self.llm_model = llm
        self.llm_model_options = self.config.settings.models[self.llm_model]
        if self.llm_model_options.agent_type is not None:
            self.set_llm_agent_type(self.llm_model_options.agent_type)
        else:
            self.set_llm_agent_type(self.get_default_llm_agent_type())

        if self.llm_model_options.temperature is not None:
            self.temperature = self.llm_model_options.temperature
        else:
            self.temperature = self.get_default_temperature()

        if self.llm_model_options.tools_enabled is not None:
            self.are_tools_enabled = self.llm_model_options.tools_enabled
        else:
            self.are_tools_enabled = self.get_default_tools_are_enabled()

        self.prompts = []
        if self.llm_model_options.prompts is not None:
            self.set_prompts(self.llm_model_options.prompts)
        else:
            self.set_prompts(self.config.settings.agent.prompts)

    def set_input_model(self, model: str):
        self.input_model = model
        self.input_model_options = self.config.settings.io_input.get(self.input_model)

    def set_output_model(self, model: str):
        self.output_model = model
        self.output_model_options = self.config.settings.io_output.get(self.output_model)

    def get_default_llm(self) -> str:
        for model, options in self.config.settings.models.items():
            return model

    def get_default_input_model(self) -> str:
        return "text"

    def get_default_output_model(self) -> str:
        return "write"

    def get_default_llm_agent_type(self) -> str:
        if self.config.settings.agent.agent_type is not None:
            return self.config.settings.agent.agent_type
        return AgentType.CONVERSATIONAL_REACT_DESCRIPTION

    def get_default_tools_are_enabled(self) -> bool:
        if self.config.settings.agent.tools_enabled is not None:
            return self.config.settings.agent.tools_enabled
        return True

    def get_default_temperature(self):
        if self.config.settings.agent.temperature is not None:
            return self.config.settings.agent.temperature
        return 0

    def load_llm_options(self) -> dict:
        return self.config.settings.models.get(self.llm_model)
