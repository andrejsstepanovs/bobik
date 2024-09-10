from abc import abstractmethod
from typing import Tuple, Set
from .state import ApplicationState
import pyperclip
import time
from datetime import datetime
from datetime import timezone
import pytz
import re
import os
from pathlib import Path
import base64

IMAGE_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.tif', '.webp', '.svg']

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
        phrase = ["time", "date", "now", "soon", "latest", "current", "clock", "calendar"]
        reference = ["today", "tomorrow", "yesterday", "weekend", "week", "month", "year", "current"]
        months = ["january", "february", "march", "april", "may", "june", "july", "august", "september", "october", "november", "december"]
        weekdays = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
        weekdays_short = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]
        return set(phrase + reference + months + weekdays + weekdays_short)

    def parse(self, question: str) -> Tuple[bool, str]:
        local_time = datetime.now()
        utc_time = datetime.now(timezone.utc)
        time_difference = abs(local_time - utc_time.replace(tzinfo=None))
        system_is_utc = time_difference.total_seconds() < 1

        if system_is_utc and self.timezone != "":
            user_tz = pytz.timezone(self.timezone)
            user_time = utc_time.astimezone(user_tz)
            current_time: str = user_time.strftime("%H:%M:%S")
            current_date: str = user_time.strftime("%Y-%m-%d")
        else:
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

# This don't work now. need to fix.
class LocalImage(PreParserInterface):
    def name(self) -> str:
        return "localimage"

    def description(self) -> str:
        return "Adds local image content to question."

    def phrases(self) -> Set[str]:
        return {"image"}

    def parse(self, question: str) -> Tuple[bool, str]:
        found = False
        paths = re.findall(r'[\w\./\\-]+', question)
        existing_paths = [Path(path) for path in paths if Path(path).exists()]
        for path in existing_paths:
            # allow only absolute file paths.
            if not os.path.isabs(path):
                continue

            extension = path.suffix.lower()
            if extension in IMAGE_EXTENSIONS:
                try:
                    with open(path, 'rb') as file:
                        found = True
                        content = file.read()
                        filenameenc = base64.b64encode(content)
                        image_data = filenameenc.rstrip()
                        filename = path.name
                        image_attachment = f"data:image/{extension[1:]};base64,{image_data}"
                        question = question.replace(str(path), f"\n<image extension=\"{extension[1:]}\" title=\"{filename}\" type=\"base64\">{image_attachment}</image>\n")
                except IOError:
                    pass

        return found, question

class LocalFile(PreParserInterface):
    def name(self) -> str:
        return "localfile"

    def description(self) -> str:
        return "Adds local file content to question."

    def phrases(self) -> Set[str]:
        return {"file"}

    def parse(self, question: str) -> Tuple[bool, str]:
        found = False
        paths = re.findall(r'[\w\./\\-]+', question)
        existing_paths = [Path(path) for path in paths if Path(path).exists()]
        for path in existing_paths:
            # allow only absolute file paths.
            if not os.path.isabs(path):
                continue

            if path.suffix.lower() not in IMAGE_EXTENSIONS:
                try:
                    with open(path, 'rb') as file:
                        found = True
                        content = file.read()
                        filename = path.name
                        question = question.replace(str(path), f"\n# File: {filename}\n```\n{content}\n```\n")
                except IOError:
                    pass
        return found, question
