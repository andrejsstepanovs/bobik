import os
from langchain_core.messages import AIMessage
from langchain_core.exceptions import OutputParserException
from langchain.memory import ConversationBufferMemory
from app.config import Configuration
from app.state import ApplicationState
from langchain.agents import initialize_agent
from app.tool_loader import ToolLoader
from app.llm_provider import LanguageModelProvider
from langchain.chains import ConversationChain
from langchain_core.memory import BaseMemory
from langchain.chains.question_answering import load_qa_chain


class LargeLanguageModelAgent:
    def __init__(
        self,
        config: Configuration,
        state: ApplicationState,
        function_provider: ToolLoader,
        llm_provider: LanguageModelProvider,
    ):
        self.state = state
        self.config = config
        self.llm_provider = llm_provider
        self.function_provider = function_provider
        self.loaded_prompts = {}

        self.tools = None
        self.agent = None
        self.memory = None
        self.model = None
        self.prompt = None

    def load_memory(self, force: bool = False):
        return_messages = True
        if self.state.is_quiet:
            return_messages = False

        if self.memory is None or force:
            self.memory = ConversationBufferMemory(
                ai_prefix=self.config.agent_name,
                human_prefix=self.config.user_name,
                memory_key="chat_history",
                return_messages=return_messages,
            )

    def initialize_prompt(self):
        prompts_changed = set(self.loaded_prompts) != set(self.state.prompts)
        if prompts_changed:
            self.loaded_prompts = {}
            self.memory.clear()

        for file_path in self.state.prompts:
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"Prompt file not found: {file_path}")

            with open(file_path, 'r') as file:
                system_prompt = file.read().strip()
                for key, value in self.config.prompt_replacements.items():
                    system_prompt = system_prompt.replace("{" + key + "}", value)
                self.memory.save_context({"input": system_prompt}, {"output": "Got it!"})
                self.loaded_prompts[file_path] = True

    def reload(self):
        self.load_memory()
        self.initialize_prompt()

        self.model = self.llm_provider.get_model()

        if self.state.are_tools_enabled:
            self.function_provider.set_memory(self.memory)
            self.tools = self.function_provider.get_tools()
            self.reload_agent()

    def reload_agent(self):
        def _handle_error(error) -> str:
            if isinstance(error, OutputParserException):
                return "Check last answer and fix it to comply with Action/Action Input syntax!"
            return str(error)

        self.agent = initialize_agent(
            agent=self.state.llm_agent_type,
            llm=self.model,
            tools=self.tools,
            verbose=not self.state.is_quiet,
            handle_parsing_errors=_handle_error,
            return_intermediate_steps=not self.state.is_quiet,
            early_stopping_method="generate",
            memory=self.memory,
            tool_choice="any",
            max_iterations=self.config.settings["agent"]["max_iterations"],
            max_execution_time=None,
        )

    def ask_question(self, text) -> str:
        if self.state.are_tools_enabled:
            response = self.agent.invoke(input={"input": text})
        else:
            response = self.model.invoke(text)

        if isinstance(response, AIMessage):
            return response.content
        return response["output"]
