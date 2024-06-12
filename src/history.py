import time
import os
from typing import List, Set
from .config import Configuration
from .state import ApplicationState
from .llm_agent import LargeLanguageModelAgent
from .parsers import StateTransitionParser
from .io_input import UserInput
from langchain_core.chat_history import BaseMessage


class History:
    def __init__(self, config: Configuration, state: ApplicationState, agent: LargeLanguageModelAgent, user_input: UserInput, parser: StateTransitionParser):
        self.config = config
        self.state = state
        self.agent = agent
        self.user_input = user_input
        self.parser = parser

    def save(self, who: str, text: str, force: bool = False):
        if not self.state.are_tools_enabled or force:
            if who == self.config.agent_name:
                self.agent.get_memory().save_context({"input": self.user_input.get()}, {"output": text})
                self.remove_history_duplicates()

        if self.config.history_file:
            with open(self.config.history_file, "a") as file:
                datetime: str = time.strftime("%Y-%m-%d %H:%M:%S")
                content: str = self.format_text(f"{datetime} {who}: {text}")
                file.write(content+"\n")

    def remove_history_duplicates(self):
        messages = self.agent.get_memory().chat_memory.messages
        if messages:
            self.agent.get_memory().chat_memory.messages = self._remove_history_duplicates(messages=messages)

    def get_messages(self) -> str:
        self.remove_history_duplicates()
        return str(self.agent.get_memory().chat_memory)

    @staticmethod
    def _remove_history_duplicates(messages: List[BaseMessage]) -> List[BaseMessage]:
        unique_messages: List[BaseMessage] = []
        message_set: Set[str] = set()

        for message in reversed(list(messages)):
            message_str: str = message.pretty_repr()
            if message_str not in message_set:
                unique_messages.append(message)
                message_set.add(message_str)

        return unique_messages[::-1]

    @staticmethod
    def format_text(text: str) -> str:
        formatted_text: List[str] = []
        current_line: str = ""
        words: List[str] = [word.strip() for line in text.split('\n') for word in line.rstrip('\n').split()] + ['\n']
        for word in words:
            if len(current_line) + len(word) + 1 > 110:
                formatted_text.append(current_line.strip())
                current_line = word + " "
            else:
                current_line += word + " "
        formatted_text.append(current_line.strip())
        return "\n".join(formatted_text)
