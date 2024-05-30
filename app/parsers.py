import pyperclip
import time
from typing import List, Tuple
from .state import ApplicationState
from .config import Configuration
from .my_print import print_text


def split_text_into_words(text: str) -> List[str]:
    return [word.strip() for line in text.split('\n') for word in line.rstrip('\n').split()] + ['\n']


def format_text(text: str) -> str:
    formatted_text: List[str] = []
    current_line: str = ""
    for word in split_text_into_words(text):
        if len(current_line) + len(word) + 1 > 110:
            formatted_text.append(current_line.strip())
            current_line = word + " "
        else:
            current_line += word + " "
    formatted_text.append(current_line.strip())
    return "\n".join(formatted_text)


def check_text_for_phrases(state: ApplicationState, question: str, phrases: List[str], contains: bool = False) -> bool:
    response_lower: str = question.lower()
    for phrase in phrases:
        if contains:
            if phrase in response_lower:
                print_text(state=state, text=f"phrase '{phrase}' detected.")
                return True
        else:
            if phrase in [response_lower, response_lower + "."]:
                print_text(state=state, text=f"phrase '{phrase}' detected.")
                return True
    return False


class ClipboardContentParser:
    def parse(self, question: str) -> Tuple[bool, str]:
        clipboard_content = pyperclip.paste().rstrip('\n')
        return (False, question) if clipboard_content == "" else (True, question + f"\n<clipboard>\n{clipboard_content}\n</clipboard>")


class CurrentTimeAndDateParser:
    def __init__(self, state: ApplicationState, timezone: str):
        self.timezone = timezone
        self.state = state

    def parse(self, question: str) -> Tuple[bool, str]:
        phrases: list[str] = ["time", "date", "now", "today", "tomorrow", "yesterday", "week", "month", "year", "current"]
        if not check_text_for_phrases(state=self.state, contains=True, phrases=phrases, question=question):
            return False, question

        current_time: str = time.strftime("%H:%M:%S")
        current_date: str = time.strftime("%Y-%m-%d")

        return True, question + f"\n- Today:\n-- Date: {current_date}\n-- Time: {current_time}\n-- Timezone: {self.timezone}"


class StateTransitionParser:
    def __init__(self, state: ApplicationState, config: Configuration):
        self.state = state
        self.config = config

    def quick_state_change(self, question: str = "") -> Tuple[bool, bool]:
        if not question:
            return False, False

        question = question[:-1] if question.endswith('.') or question.endswith('!') else question

        if check_text_for_phrases(state=self.state, phrases=["verbal"], question=question):
            self.state.set_input_model("listen")
            self.state.set_output_model("speak")
            print_text(state=self.state, text="Changed to verbal mode")
            return True, False

        if check_text_for_phrases(state=self.state, phrases=["text"], question=question):
            self.state.set_input_model("text")
            self.state.set_output_model("text")
            print_text(state=self.state, text="Changed to text mode")
            return True, False

        if check_text_for_phrases(state=self.state, phrases=list(self.config.settings.io_input.keys()), question=question):
            self.state.set_input_model(question)
            return True, False

        if check_text_for_phrases(state=self.state, phrases=list(self.config.settings.io_output.keys()), question=question):
            self.state.set_output_model(question)
            return True, False

        if check_text_for_phrases(state=self.state, phrases=list(self.config.settings.models.keys()), question=question):
            self.state.set_llm_model(question)
            print_text(state=self.state, text=f"Changed model to {self.state.llm_model}")
            return True, False

        if check_text_for_phrases(state=self.state, phrases=self.config.phrases["no_tools"], question=question):
            print_text(state=self.state, text="No Tools")
            self.state.are_tools_enabled = False
            return True, False

        if check_text_for_phrases(state=self.state, phrases=self.config.phrases["with_tools"], question=question):
            print_text(state=self.state, text="With Tools (Agent)")
            self.state.are_tools_enabled = True
            return True, False

        if check_text_for_phrases(state=self.state, phrases=self.config.phrases["exit"], question=question):
            print_text(state=self.state, text="Exiting conversation")
            self.state.stop = True
            return False, True

        return False, False
