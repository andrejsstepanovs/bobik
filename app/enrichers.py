from abc import abstractmethod
from typing import List, Tuple
from app.state import ApplicationState
from app.my_print import print_text
import pyperclip
import time
import os
import re


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
    question: str = question.lower()
    parts = question.split()
    for phrase in phrases:
        if not contains:
            if phrase == parts[0]:
                return phrase, True
        else:
            if phrase in parts:
                return phrase, True
    return "", False


class CurrentTime(PreParserInterface):
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


class Clipboard(PreParserInterface):
    def name(self) -> str:
        return "clipboard"

    def description(self) -> str:
        return "Adds current active clipboard to question context."

    def phrases(self) -> List[str]:
        return ["clipboard", "paste"]

    def parse(self, question: str) -> Tuple[bool, str]:
        clipboard_content = pyperclip.paste().rstrip('\n')
        return (False, question) if clipboard_content == "" else (True, question + f"\n<clipboard>\n{clipboard_content}\n</clipboard>")


class LocalFile(PreParserInterface):
    def name(self) -> str:
        return "file"

    def description(self) -> str:
        return "Adds local file content to question context."

    def phrases(self) -> List[str]:
        return ["file", "code"]

    def parse(self, question: str) -> Tuple[bool, str]:
        sep = os.path.sep
        if sep not in question:
            return False, question

        found = False
        paths = re.findall(f'(?:[A-Za-z]:)?{os.path.sep}(?:[^{os.path.sep}\\s]+{os.path.sep})*[^{os.path.sep}\\s]*', question)
        existing_paths = [path for path in paths if os.path.exists(path)]
        for path in existing_paths:
            with open(path, 'r') as file:
                found = True
                content = file.read()
                filename = os.path.basename(path)
                question = question.replace(path, f"\n# File: {filename}\n```\n{content}\n```\n")

        return found, question
