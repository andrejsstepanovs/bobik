from typing import Optional
from langchain_core.callbacks import CallbackManagerForToolRun
from langchain_core.tools import BaseTool
from app.state import ApplicationState
from app.config import Configuration
from langchain.memory import ConversationBufferMemory


class EndConversation(BaseTool):
    name: str = "end_conversation"
    description: str = "Use tool when phrases like 'Please exit.', 'Stop conversation.', etc., are used."
    state: ApplicationState

    def _run(self, model: str, run_manager: Optional[CallbackManagerForToolRun] = None) -> str:
        self.state.is_stopped = True
        return "AI: Exit"


class RetrieveModels(BaseTool):
    name: str = "get_models"
    description: str = (
        "Returns all available model names that can be used using switch_model() tool. "
        "Tool returns json array with values. "
    )
    config: Configuration

    def _run(self, model: str, run_manager: Optional[CallbackManagerForToolRun] = None) -> str:
        models = [model_name for model_name, options in self.config.settings.models.items()]
        models.extend(synonym for options in self.config.settings.models.values() for synonym in options.synonyms)
        return "AI: "+str(models)


class SwitchModel(BaseTool):
    name: str = "switch_model"
    description: str = (
        "Switch between different language models. "
        "Allows to switch agent to use different models. "
        "Use this tool for anything to do with model change, including model name mention. "
        "Use this tool when phrases like 'change model to', 'switch model' is used. "
        "Available can be retrieved using get_models() tool. "
    )
    state: ApplicationState
    config: Configuration

    def _run(self, model: str, run_manager: Optional[CallbackManagerForToolRun] = None) -> str:
        for name, options in self.config.settings.models.items():
            if model in [name] + options.synonyms:
                self.state.set_llm_model(name)
                return f"Changed to {model}"
        return f"AI: Not changed. Given model does not exist: '{model}'"


class ResetChat(BaseTool):
    name: str = "reset_chat"
    description: str = (
        "Use this tool when phrases like 'forget this conversation', "
        "'lets change the topic', 'forget about that' or similar is mentioned. "
    )
    memory: ConversationBufferMemory

    def _run(self, something: str, run_manager: Optional[CallbackManagerForToolRun] = None) -> str:
        self.memory.clear()
        return "AI: Cleared this conversation."


class SwitchInputMethod(BaseTool):
    name: str = "use_input_method"
    description: str = (
        "Switch between different input methods. "
        "Use this tool for anything to do with input change. "
        "Available values are: 'text', 'voice', 'speech', 'listen'. "
    )
    state: ApplicationState

    def _run(self, method: str, run_manager: Optional[CallbackManagerForToolRun] = None) -> str:
        input_model = "text" if method in ["text", "voice", "speech", "deepgram", "listen"] else method
        self.state.set_input_model(input_model)
        return f"AI: Input changed to {input_model}"


class SwitchOutputMethod(BaseTool):
    name: str = "use_output_method"
    description: str = (
        "Switch between different output methods. "
        "Use tool with value 'voice' when phrases like 'Talk to me', 'Speak with me', 'Talk' are used. "
        "Use tool with value 'text' when phrases like 'Stop talking' or 'Shut up' are used. "
        "Use this tool for anything to do with output change or desired response method. "
        "Available values are: 'text', 'voice', 'speech', 'speak'. "
    )
    state: ApplicationState

    def _run(self, method: str, run_manager: Optional[CallbackManagerForToolRun] = None) -> str:
        output_model = "text" if method in ["text", "write"] else "speak"
        self.state.set_output_model(output_model)
        return f"AI: Output changed to {output_model}"


class SetToolUsage(BaseTool):
    name: str = "set_use_tools"
    description: str = (
        "Use tool with value 'Yes' when phrases like 'Use tools', 'Use functions', 'Use function calling', "
        "'Please make sure to use tools' are used. "
        "Use tool with value 'No' when phrases like 'Dont use tools', 'No tools', 'No function calling' are used. "
        "Available values are: 'Yes', 'No'. "
    )
    state: ApplicationState

    def _run(self, use_tools: str, run_manager: Optional[CallbackManagerForToolRun] = None) -> str:
        self.state.use_tools = use_tools.lower() == "yes"
        return "AI: Set to use tools." if self.state.use_tools else "Set to not use tools."
