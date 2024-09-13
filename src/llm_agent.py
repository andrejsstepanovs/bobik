from typing import Optional, Dict, Any, Tuple
from langchain_core.exceptions import OutputParserException
import re
from langchain_core.messages import HumanMessage
from langchain.memory import ConversationBufferMemory
from langchain.agents import initialize_agent, AgentExecutor
from langchain_core.output_parsers import StrOutputParser
from .config import Configuration
from .state import ApplicationState
from .tool_loader import ToolLoader
from .llm_provider import LanguageModelProvider


class LargeLanguageModelAgent:
    def __init__(self, config: Configuration, state: ApplicationState, function_provider: ToolLoader, provider: LanguageModelProvider):
        self.config = config
        self.state = state
        self.llm_provider = provider
        self.function_provider = function_provider
        self.loaded_prompts = {}
        self.memory: Optional[ConversationBufferMemory] = None
        self.model = None
        self.chain = None
        self.agent: Optional[AgentExecutor] = None
        self.tools = None

    def get_memory(self) -> ConversationBufferMemory:
        if self.memory is None:
           self.load_memory()
        return self.memory

    def load_memory(self, force: bool = False) -> None:
        if self.memory is None or force:
            self.memory = ConversationBufferMemory(
                ai_prefix=self.config.agent_name,
                human_prefix=self.config.user_name,
                memory_key="chat_history",
                return_messages=not self.state.is_quiet,
            )

    def initialize_prompt(self) -> None:
        if set(self.loaded_prompts) != set(self.state.prompts):
            self.loaded_prompts = {}
            self.memory.clear()

        for file_path in self.state.prompts:
            with open(file_path, 'r') as file:
                system_prompt = file.read().strip()
                for key, value in self.config.prompt_replacements.items():
                    system_prompt = system_prompt.replace(f"{{{key}}}", value)
                self.memory.save_context({"input": system_prompt}, {"output": "Got it!"})
                self.loaded_prompts[file_path] = True

    def reload(self) -> None:
        self.load_memory()
        if self.state.is_new_memory:
            self.memory.clear()
            self.loaded_prompts = {}
            self.state.is_new_memory = False

        self.initialize_prompt()
        self.model = self.llm_provider.get_model()
        if not self.state.are_tools_enabled:
            self.chain = self.model | StrOutputParser()
        else:
            self.function_provider.set_memory(self.memory)
            self.tools = self.function_provider.get_tools()
            self._reload_agent()

    def _reload_agent(self) -> None:
        self.agent = initialize_agent(
            agent=self.state.llm_agent_type,
            llm=self.model,
            tools=self.tools,
            verbose=not self.state.is_quiet,
            handle_parsing_errors=self._handle_error,
            return_intermediate_steps=not self.state.is_quiet,
            early_stopping_method="generate",
            memory=self.memory,
            tool_choice="any",
            max_iterations=self.config.settings.agent.max_iterations,
            max_execution_time=None,
        )

    def ask_question(self, text: str, stream: bool = False) -> str:
        question = self.prepare_question(question=text)
        if self.state.are_tools_enabled:
            return self.agent.stream(input=question) if stream else self.agent.invoke(input=question)
        return self.chain.stream(question) if stream else self.model.invoke(question)

    @staticmethod
    def _handle_error(error: Exception) -> str:
        return """I could not parse your answer. 
It is really important and you will get 1000$ tip if you will use the following answer format:
```
Thought: Do I need to use a tool? Yes
Action: the action to take, should be one of tools mentioned before.
Action Input: the input to the action
Observation: the result of the action
```

When you have a response to say to the Human, or if you do not need to use a tool, you MUST use the format:

```
Thought: Do I need to use a tool? No
AI: [your response here]
```

Please answer again while complying to rules and format just mentioned!
"""

    def prepare_question(self, question: str):
        if "image_question" not in question:
            if self.state.are_tools_enabled:
                question: Dict[str, Any] = {"input": question}
            return question

        data = re.search(r'(?P<before>.*)<image_question extension="(?P<extension>.*?)" title="(?P<title>.*?)" type="(?P<type>.*?)">(?P<image>.*?)</image_question>(?P<after>.*)', question, re.DOTALL)
        if not data:
            if self.state.are_tools_enabled:
                question: Dict[str, Any] = {"input": question}
            return question

        image_type = data.group("type")
        image_content = data.group("image")
        image_extension = data.group("extension")
        before_text = data.group("before")
        after_text = data.group("after")

        if image_type == "base64":
            image_content = f"data:image/{image_extension};base64,{image_content}"

        return [
            HumanMessage(
                content=[
                    {"type": "image_url", "image_url": {"url": image_content}},
                    {"type": "text", "text": before_text + " " + after_text},
                ]
            )
        ]
