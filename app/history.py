import time
from typing import List
from .config import Configuration
from .state import ApplicationState
from .llm_agent import LargeLanguageModelAgent
from .parsers import StateTransitionParser
from .io_input import UserInput


class History:
    def __init__(self, config: Configuration, state: ApplicationState, agent: LargeLanguageModelAgent, user_input: UserInput, parser: StateTransitionParser):
        self.config = config
        self.agent = agent
        self.user_input = user_input
        self.parser = parser
        self.state = state

    def save(self, who: str, text: str, force: bool = False):
        if not self.state.are_tools_enabled or force:
            if who == self.config.agent_name:
                self.agent.memory.save_context({"input": self.user_input.get()}, {"output": text})

        if self.config.history_file:
            with open(self.config.history_file, "a") as file:
                datetime = time.strftime("%Y-%m-%d %H:%M:%S")
                content = self.format_text(f"{datetime} {who}: {text}")
                file.write(content+"\n")

    @staticmethod
    def format_text(text: str) -> str:
        formatted_text: List[str] = []
        current_line: str = ""
        words = [word.strip() for line in text.split('\n') for word in line.rstrip('\n').split()] + ['\n']
        for word in words:
            if len(current_line) + len(word) + 1 > 110:
                formatted_text.append(current_line.strip())
                current_line = word + " "
            else:
                current_line += word + " "
        formatted_text.append(current_line.strip())
        return "\n".join(formatted_text)
