from app.enrichers import check_text_for_phrases, CurrentTimeAndDateParser, ClipboardContentParser, PreParserInterface
from typing import List, Tuple
from .state import ApplicationState
from .config import Configuration
from .my_print import print_text


class StateTransitionParser:
    def __init__(self, state: ApplicationState, config: Configuration):
        self.state = state
        self.config = config

        self.enrichers: List[PreParserInterface] = []
        self.add_enricher(self.config.settings.pre_parsers.clipboard.enabled, ClipboardContentParser())
        self.add_enricher(self.config.settings.pre_parsers.time.enabled, CurrentTimeAndDateParser(timezone=self.config.prompt_replacements["timezone"]))

    def add_enricher(self, enabled: bool, parser: PreParserInterface):
        if enabled:
            self.enrichers.append(parser)

    def enrich(self, text: str) -> tuple[bool, str]:
        improved_text = text
        was_changed = False

        for enricher in self.enrichers:
            if not check_text_for_phrases(state=self.state, contains=True, phrases=enricher.phrases(), question=text):
                return False, text

            changed, out = enricher.parse(improved_text)
            if changed:
                was_changed = True
                improved_text = out

        return was_changed, improved_text

    def is_empty(self, question: str = "") -> bool:
        return not question.strip()

    def must_exit(self, question: str = "") -> bool:
        if check_text_for_phrases(state=self.state, phrases=self.config.phrases["exit"], question=question):
            print_text(state=self.state, text="Exiting conversation")
            self.state.stop = True
            return True
        return False

    def change_state(self, question: str = "") -> bool:
        if not question:
            return False

        question = question[:-1] if question.endswith('.') or question.endswith('!') else question

        if check_text_for_phrases(state=self.state, phrases=["verbal"], question=question):
            self.state.set_input_model("listen")
            self.state.set_output_model("speak")
            print_text(state=self.state, text="Changed to verbal mode")
            return True

        if check_text_for_phrases(state=self.state, phrases=["text"], question=question):
            self.state.set_input_model("text")
            self.state.set_output_model("text")
            print_text(state=self.state, text="Changed to text mode")
            return True

        if check_text_for_phrases(state=self.state, phrases=list(self.config.settings.io_input.keys()), question=question):
            self.state.set_input_model(question)
            return True

        if check_text_for_phrases(state=self.state, phrases=list(self.config.settings.io_output.keys()), question=question):
            self.state.set_output_model(question)
            return True

        if check_text_for_phrases(state=self.state, phrases=list(self.config.settings.models.keys()), question=question):
            self.state.set_llm_model(question)
            print_text(state=self.state, text=f"Changed model to {self.state.llm_model}")
            return True

        if check_text_for_phrases(state=self.state, phrases=self.config.phrases["no_tools"], question=question):
            print_text(state=self.state, text="No Tools")
            self.state.are_tools_enabled = False
            return True

        if check_text_for_phrases(state=self.state, phrases=self.config.phrases["with_tools"], question=question):
            print_text(state=self.state, text="With Tools (Agent)")
            self.state.are_tools_enabled = True
            return True

        return False

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
