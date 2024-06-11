from typing import List


class Transcript:
    def __init__(self):
        self.transcript_parts: List[str] = []

    def add_section(self, section: str):
        self.transcript_parts.append(section)

    def retrieve_transcript(self) -> str:
        return ' '.join(self.transcript_parts)

    def clear_transcript(self):
        self.transcript_parts = []
