import time
import traceback
from .parsers import StateTransitionParser
from .tool_loader import ToolLoader
from .config import Configuration
from .state import ApplicationState
from .transcript import Transcript
from .io_output import TextToSpeech
from .llm_agent import LargeLanguageModelAgent
from .pkg.beep import BeepGenerator
from .llm_provider import LanguageModelProvider
from .io_input import UserInput
from .my_print import print_text
from .history import History


class ConversationManager:
    def __init__(
            self,
            config: Configuration,
            state: ApplicationState,
            agent: LargeLanguageModelAgent,
            provider: LanguageModelProvider,
            collector: Transcript,
            tool_loader: ToolLoader,
            parser: StateTransitionParser,
            response: TextToSpeech,
            beep: BeepGenerator,
    ):
        # Initialize configuration and state
        self.config = config
        self.state = state

        # Initialize components related to language processing
        self.agent = agent
        self.provider = provider
        self.parser = parser

        # Initialize components related to interaction and tools
        self.collector = collector
        self.tool_loader = tool_loader
        self.response = response
        self.beep = beep

        # Initialize conversation-specific attributes
        self.answer_text: str = ""
        self.current_state_hash: str = None

        self.user_input: UserInput = UserInput(
            config=self.config,
            state=self.state,
            transcript_collector=self.collector,
            beep=self.beep,
        )
        self.history = History(
            config=self.config,
            state=self.state,
            agent=self.agent,
            user_input=self.user_input,
            parser=self.parser,
        )

    def reload_agent(self, force: bool = False):
        if self.current_state_hash != self.state.get_hash() or force:
            self.current_state_hash = self.state.get_hash()
            print_text(state=self.state, text="Loading LLM...")
            self.agent.reload()
        return self.agent

    def clear_memory(self):
        if self.agent.memory:
            self.agent.memory.clear()
        self.agent.load_memory(force=True)
        self.agent.initialize_prompt()

    async def main_loop(self, first_question: list[str] = None):
        while not self.state.is_stopped:
            stop = await self.question_answer(first_question)
            first_question = None
            if stop:
                break

    async def question_answer(self, first_question: list[str] = None) -> bool:
        self._print_status()

        if first_question:
            for question in first_question:
                self.user_input.set(question)
            print_text(state=self.state, text=f"{self.config.user_name}: {' '.join(first_question)}")
        else:
            await self.user_input.ask_input()

        if self.parser.is_empty(self.user_input.get()):
            return False

        if self.parser.must_exit(self.user_input.get()):
            return True

        if self.parser.change_state(self.user_input.get()):
            self.reload_agent(force=True)
            return False

        was_changed, enriched_text = self.parser.enrich(self.user_input.get())
        self.user_input.set(enriched_text)
        who = self.config.user_name if not was_changed else "Pre-parser"
        self.history.save(who, self.user_input.get())

        if self.agent.model is None:
            self.reload_agent(force=False)

        tries = 0
        while tries < self.config.retry_settings["max_tries"]:
            try:
                self._process()
                break
            except KeyboardInterrupt:
                if not self.state.is_quiet:
                    print("OK...")
                break
            except Exception as e:
                tr = traceback.format_exc()
                print_text(state=self.state, text=f"Exception: {e.__class__.__name__} > {tr}")
                sleep_sec = self.config.retry_settings["sleep_seconds_between_tries"]
                print_text(state=self.state, text=f"Sleep and try again after: {sleep_sec} sec")
                tries += 1
                time.sleep(sleep_sec)

    def _process(self):
        stream = not self.state.is_quiet and not self.state.are_tools_enabled
        text = self.user_input.get()

        if not self.state.are_tools_enabled:
            text = str(self.agent.memory.chat_memory) + "\n" + text
        text = text.lstrip()

        response = self.agent.ask_question(text=text, stream=stream)
        self.answer_text = self.response.write_response(stream=stream, agent_response=response)
        self.history.save(self.config.agent_name, self.answer_text)
        if self.state.is_stopped:
            return

        self.response.respond(self.answer_text)
        self.response.wait_for_audio_process()
        self.user_input.set("")

    def _print_status(self):
        yellow = "\033[93m"
        red_bold_underline = "\033[91;1;4m"
        reset = "\033[0m"
        blue = "\033[94m"

        mode = "simple"
        if self.state.are_tools_enabled:
            mode = f"{blue}agent{reset}"
        formatted_string = (
            f"{yellow}{self.state.input_model}{reset} → "
            f"{mode} {red_bold_underline}{self.state.llm_model}{reset} ({self.state.llm_model_options.model}) → "
            f"{yellow}{self.state.output_model}{reset}"
        )
        print_text(state=self.state, text=formatted_string)
