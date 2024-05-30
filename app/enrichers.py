from abc import abstractmethod
from typing import List, Tuple
from app.state import ApplicationState
from app.my_print import print_text
import pyperclip
import time


class PreParserInterface:
    @abstractmethod
    def parse(self, question: str) -> Tuple[bool, str]:
        pass


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


class CurrentTimeAndDateParser(PreParserInterface):
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


class ClipboardContentParser(PreParserInterface):
    def __init__(self, state: ApplicationState):
        self.state = state

    def parse(self, question: str) -> Tuple[bool, str]:
        phrases: list[str] = ["clipboard", "paste"]
        if not check_text_for_phrases(state=self.state, contains=True, phrases=phrases, question=question):
            return False, question

        clipboard_content = pyperclip.paste().rstrip('\n')
        return (False, question) if clipboard_content == "" else (True, question + f"\n<clipboard>\n{clipboard_content}\n</clipboard>")
