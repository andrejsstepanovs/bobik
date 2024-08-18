from .enrichers import check_text_for_phrases, CurrentTime, Clipboard, LocalFile, LocalImage, PreParserInterface
from typing import List
from .state import ApplicationState
from .config import Configuration
from .my_print import print_text


class StateTransitionParser:
    def __init__(self, state: ApplicationState, config: Configuration):
        self.state: ApplicationState = state
        self.config: Configuration = config

        self.enrichers: List[PreParserInterface] = []
        self.add_enricher(self.config.settings.pre_parsers.clipboard.enabled, Clipboard())
        self.add_enricher(self.config.settings.pre_parsers.time.enabled, CurrentTime(timezone=self.config.prompt_replacements["timezone"]))
        self.add_enricher(self.config.settings.pre_parsers.file.enabled, LocalFile())
        self.add_enricher(self.config.settings.pre_parsers.image.enabled, LocalImage())

    def add_enricher(self, enabled: bool, parser: PreParserInterface):
        if enabled:
            self.enrichers.append(parser)

    def enrich(self, text: str) -> tuple[bool, str]:
        improved_text = text
        was_changed = False

        for enricher in self.enrichers:
            found_phrase, found = check_text_for_phrases(state=self.state, contains=True, phrases=enricher.phrases(), question=text)
            if not found:
                continue

            changed, out = enricher.parse(improved_text)
            if changed:
                was_changed = True
                improved_text = out

        return was_changed, improved_text

    def is_empty(self, question: str = "") -> bool:
        if not question:
            return True
        return not question.strip()

    def change_state(self, commands: str = "") -> tuple[list[str], bool]:
        phrases_found = []
        for part in commands.split():
            part = part[:-1] if part.endswith('.') or part.endswith(',') else part
            found_phrases = self._change_state(part)
            if not found_phrases:
                break
            phrases_found.extend(found_phrases)

        return phrases_found, bool(phrases_found)

    def _change_state(self, phrase: str = "") -> list[str]:
        if self.is_empty(question=phrase):
            return []
        phrases_config = self.config.phrases

        actions = [
            {"phrases": phrases_config["exit"], "action": lambda: setattr(self.state, 'is_stopped', True)},
            {"phrases": phrases_config["clear_memory"], "action": lambda: setattr(self.state, 'is_new_memory', True)},
            {"phrases": phrases_config["run_once"], "action": lambda: setattr(self.state, 'is_stopped', True)},
            {"phrases": phrases_config["quiet"], "action": lambda: setattr(self.state, 'is_quiet', True)},
            {"phrases": phrases_config["verbose"], "action": lambda: setattr(self.state, 'is_quiet', False)},
            {"phrases": ["verbal"], "action": lambda: (self.state.set_input_model("listen"), self.state.set_output_model("speak"))},
            {"phrases": ["text"], "action": lambda: (self.state.set_input_model("text"), self.state.set_output_model("text"))},
            {"phrases": list(self.config.settings.io_input.keys()), "action": lambda phrase: self.state.set_input_model(phrase)},
            {"phrases": list(self.config.settings.io_output.keys()), "action": lambda phrase: self.state.set_output_model(phrase)},
            {"phrases": list(self.config.settings.models.keys()), "action": lambda phrase: self.state.set_llm_model(phrase)},
            {"phrases": phrases_config["no_tools"], "action": lambda: setattr(self.state, 'are_tools_enabled', False)},
            {"phrases": phrases_config["with_tools"], "action": lambda: setattr(self.state, 'are_tools_enabled', True)},
        ]

        for action in actions:
            found_phrase, found = check_text_for_phrases(phrases=action["phrases"], question=phrase, contains=False, state=self.state)
            if found:
                if action["action"].__code__.co_argcount == 0:
                    action["action"]()
                else:
                    action["action"](found_phrase)

                return [found_phrase]

        return []
