class Transcript:
    def __init__(self):
        self.transcript_parts = None
        self.initialize()

    def initialize(self):
        self.transcript_parts = []

    def add_section(self, section):
        self.transcript_parts.append(section)

    def retrieve_transcript(self):
        return ' '.join(self.transcript_parts)
