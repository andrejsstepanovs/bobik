from abc import abstractmethod
from typing import Tuple, Set
from src.state import ApplicationState
import pyperclip
import time
import re
from pathlib import Path


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
    def phrases(self) -> Set[str]:
        pass


def check_text_for_phrases(state: ApplicationState, question: str, phrases: Set[str], contains: bool = False) -> tuple[str, bool]:
    question: str = question.lower()
    parts = set(question.split())
    for phrase in phrases:
        if not contains:
            if phrase == next(iter(parts), None):
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

    def phrases(self) -> Set[str]:
        return {"time", "date", "now", "today", "tomorrow", "yesterday", "week", "month", "year", "current"}

    def parse(self, question: str) -> Tuple[bool, str]:
        current_time: str = time.strftime("%H:%M:%S")
        current_date: str = time.strftime("%Y-%m-%d")
        _, found = check_text_for_phrases(None, question, self.phrases(), contains=True)
        return found, question + f"\n- Today:\n-- Date: {current_date}\n-- Time: {current_time}\n-- Timezone: {self.timezone}" if found else (False, question)

class Clipboard(PreParserInterface):
    def name(self) -> str:
        return "clipboard"

    def description(self) -> str:
        return "Adds clipboard content to question."

    def phrases(self) -> Set[str]:
        return {"clipboard", "content", "copy"}

    def parse(self, question: str) -> Tuple[bool, str]:
        try:
            clipboard_content = pyperclip.paste().rstrip('\n')
            _, found = check_text_for_phrases(None, question, self.phrases(), contains=True)
            return found, question + f"\n# Clipboard Content:\n```\n{clipboard_content}\n```\n" if found else (False, question)
        except pyperclip.PyperclipException:
            return False, question

class LocalFile(PreParserInterface):
    def name(self) -> str:
        return "localfile"

    def description(self) -> str:
        return "Adds local file content to question."

    def phrases(self) -> Set[str]:
        return {"file"}

    def parse(self, question: str) -> Tuple[bool, str]:
        found = False
        paths = re.findall(r'[\w\./\\]+', question)
        existing_paths = [Path(path) for path in paths if Path(path).exists()]
        for path in existing_paths:
            try:
                with open(path, 'r') as file:
                    found = True
                    content = file.read()
                    filename = path.name
                    question = question.replace(str(path), f"\n# File: {filename}\n```\n{content}\n```\n")
            except IOError:
                pass
        return found, question
