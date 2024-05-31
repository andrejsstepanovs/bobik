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

    @abstractmethod
    def name(self) -> str:
        pass

    @abstractmethod
    def description(self) -> str:
        pass

    @abstractmethod
    def phrases(self) -> List[str]:
        pass


def check_text_for_phrases(state: ApplicationState, question: str, phrases: List[str], contains: bool = False) -> tuple[str, bool]:
    response_lower: str = question.lower()
    for phrase in phrases:
        if contains:
            if phrase in response_lower:
                print_text(state=state, text=f"phrase '{phrase}' detected.")
                return phrase, True
        else:
            if phrase in [response_lower, response_lower + "."]:
                print_text(state=state, text=f"phrase '{phrase}' detected.")
                return phrase, True
    return "", False


class CurrentTimeAndDateParser(PreParserInterface):
    def __init__(self, timezone: str):
        self.timezone = timezone

    def name(self) -> str:
        return "time"

    def description(self) -> str:
        return "Adds time context to question."

    def phrases(self) -> List[str]:
        return ["time", "date", "now", "today", "tomorrow", "yesterday", "week", "month", "year", "current"]

    def parse(self, question: str) -> Tuple[bool, str]:
        current_time: str = time.strftime("%H:%M:%S")
        current_date: str = time.strftime("%Y-%m-%d")

        return True, question + f"\n- Today:\n-- Date: {current_date}\n-- Time: {current_time}\n-- Timezone: {self.timezone}"


class ClipboardContentParser(PreParserInterface):
    def name(self) -> str:
        return "clipboard"

    def description(self) -> str:
        return "Adds current active clipboard to question context."

    def phrases(self) -> List[str]:
        return ["clipboard", "paste"]

    def parse(self, question: str) -> Tuple[bool, str]:
        clipboard_content = pyperclip.paste().rstrip('\n')
        return (False, question) if clipboard_content == "" else (True, question + f"\n<clipboard>\n{clipboard_content}\n</clipboard>")
