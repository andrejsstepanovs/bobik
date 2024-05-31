from app.enrichers import check_text_for_phrases, CurrentTimeAndDateParser, ClipboardContentParser, PreParserInterface
from typing import List, Tuple
from .state import ApplicationState
from .config import Configuration
from .my_print import print_text


class StateTransitionParser:
    def __init__(self, state: ApplicationState, config: Configuration):
        self.state: ApplicationState = state
        self.config: Configuration = config

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
            found_phrase, found = check_text_for_phrases(state=self.state, contains=True, phrases=enricher.phrases(), question=text)
            if not found:
                break

            changed, out = enricher.parse(improved_text)
            if changed:
                was_changed = True
                improved_text = out

        return was_changed, improved_text

    def is_empty(self, question: str = "") -> bool:
        return not question.strip()

    def must_exit(self, question: str = "") -> bool:
        found_phrase, found = check_text_for_phrases(state=self.state, phrases=self.config.phrases["exit"], question=question)
        if found:
            print_text(state=self.state, text="Exiting conversation")
            self.state.stop = True
            return True
        return False

    def must_clear_memory(self, question: str = "") -> bool:
        found_phrase, found = check_text_for_phrases(state=self.state, phrases=self.config.phrases["clear_memory"], question=question, contains=False)
        if found:
            print_text(state=self.state, text="Clearing memory")
            return True
        return False

    def split(self, question: str = "") -> Tuple[str, str]:
        question = question.strip()
        sep = self.config.phrases["separator"][0]
        if sep in question:
            parts = question.split(sep)
            if len(parts) > 1:
                return parts[0].strip(), sep.join(parts[1:]).strip()
        return question, question

    def change_state(self, commands: str = "") -> tuple[list[str], bool]:
        if not commands:
            return [], False

        commands = commands[:-1] if commands.endswith('.') or commands.endswith('!') else commands
        phrases_found: list[str] = []

        """Phrases that will be picked no matter where they are in the sentence."""
        for contains in [True, False]:
            found_phrase, found = check_text_for_phrases(state=self.state, contains=True, phrases=self.config.phrases["run_once"], question=commands)
            if found:
                print_text(state=self.state, text="Run Once")
                self.state.is_stopped = True
                phrases_found.append(found_phrase)

            last = self.state.is_quiet
            self.state.is_quiet = True
            found_phrase, found = check_text_for_phrases(state=self.state, phrases=self.config.phrases["quiet"], contains=contains, question=commands)
            if found:
                self.state.is_quiet = True
                phrases_found.append(found_phrase)
            else:
                self.state.is_quiet = last

            found_phrase, found = check_text_for_phrases(state=self.state, phrases=self.config.phrases["verbose"], contains=contains, question=commands)
            if found:
                print_text(state=self.state, text="Quiet mode OFF")
                self.state.is_quiet = False
                phrases_found.append(found_phrase)

            found_phrase, found = check_text_for_phrases(state=self.state, phrases=["verbal"], contains=contains, question=commands)
            if found:
                self.state.set_input_model("listen")
                self.state.set_output_model("speak")
                print_text(state=self.state, text="Changed to verbal mode")
                phrases_found.append(found_phrase)

            found_phrase, found = check_text_for_phrases(state=self.state, phrases=["text"], question=commands, contains=contains)
            if found:
                self.state.set_input_model("text")
                self.state.set_output_model("text")
                print_text(state=self.state, text="Changed to text mode")
                phrases_found.append(found_phrase)

            found_phrase, found = check_text_for_phrases(state=self.state, phrases=list(self.config.settings.io_input.keys()), question=commands, contains=contains)
            if found:
                self.state.set_input_model(found_phrase)
                phrases_found.append(found_phrase)

            found_phrase, found = check_text_for_phrases(state=self.state, phrases=list(self.config.settings.io_output.keys()), question=commands, contains=contains)
            if found:
                self.state.set_output_model(found_phrase)
                phrases_found.append(found_phrase)

            found_phrase, found = check_text_for_phrases(state=self.state, phrases=list(self.config.settings.models.keys()), question=commands, contains=contains)
            if found:
                self.state.set_llm_model(found_phrase)
                print_text(state=self.state, text=f"Changed model to {self.state.llm_model}")
                phrases_found.append(found_phrase)

            found_phrase, found = check_text_for_phrases(state=self.state, phrases=self.config.phrases["no_tools"], question=commands, contains=contains)
            if found:
                print_text(state=self.state, text="No Tools")
                self.state.are_tools_enabled = False
                phrases_found.append(found_phrase)

            found_phrase, found = check_text_for_phrases(state=self.state, phrases=self.config.phrases["with_tools"], question=commands, contains=contains)
            if found:
                print_text(state=self.state, text="With Tools (Agent)")
                self.state.are_tools_enabled = True
                phrases_found.append(found_phrase)

        return phrases_found, len(phrases_found) > 0
