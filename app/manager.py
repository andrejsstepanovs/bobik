import time
import traceback
from typing import List
from langchain_core.messages import BaseMessage
from langchain_core.runnables.utils import AddableDict
from .parsers import format_text, ClipboardContentParser, CurrentTimeAndDateParser, StateTransitionParser
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
        self.answer_text = ""
        self.current_state_hash = None

        # Initialize user input handler
        self.user_input = self._create_user_input()

    def _create_user_input(self):
        return UserInput(config=self.config, state=self.state, transcript_collector=self.collector, beep=self.beep)

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

    def add_text_to_history(self, who: str, text: str, force: bool = False):
        if not self.state.are_tools_enabled or force:
            if who == self.config.agent_name:
                self.agent.memory.save_context({"input": self.user_input.question_text}, {"output": text})

        if self.config.history_file:
            with open(self.config.history_file, "a") as file:
                datetime = time.strftime("%Y-%m-%d %H:%M:%S")
                content = format_text(f"{datetime} {who}: {text}")
                file.write(content+"\n")

    def pre_parse_question(self) -> tuple[bool, bool]:
        if not self.user_input.question_text.strip():
            return False, False

        state_changed, stop = self.parser.quick_state_change(self.user_input.question_text)
        if state_changed or stop:
            return state_changed, stop

        input_was_changed: bool = False
        if self.config.settings.pre_parsers.clipboard.enabled:
            changed, out = ClipboardContentParser().parse(self.user_input.question_text)
            if changed:
                input_was_changed = True
                self.user_input.question_text = out

        if self.config.settings.pre_parsers.time.enabled:
            time_parser = CurrentTimeAndDateParser(timezone=self.config.prompt_replacements["timezone"], state=self.state)
            changed, out = time_parser.parse(self.user_input.question_text)
            if changed:
                input_was_changed = True
                self.user_input.question_text = out

        if input_was_changed:
            self.add_text_to_history("Question pre-parser", self.user_input.question_text)

        return False, False

    async def main_loop(self, first_question: list[str] = None):
        while not self.state.is_stopped:
            stop = await self.question_answer(first_question)
            first_question = None
            if stop:
                break

    async def question_answer(self, first_question: list[str] = None) -> bool:
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

        if first_question:
            for question in first_question:
                self.user_input.handle_full_sentence(question)
            print_text(state=self.state, text=f"{self.config.user_name}: {' '.join(first_question)}")
        else:
            await self.user_input.get_input()

        self.add_text_to_history(self.config.user_name, self.user_input.question_text)

        if self.agent.model is None:
            self.reload_agent(force=False)

        state_changed, stop = self.pre_parse_question()
        if state_changed:
            self.reload_agent(force=state_changed)
            return False
        if stop:
            return True

        tries = 0
        while tries < self.config.retry_settings["max_tries"]:
            try:
                stream = not self.state.is_quiet and not self.state.are_tools_enabled
                text = self.user_input.question_text
                if text.strip() == "":
                    break
                if not self.state.are_tools_enabled:
                    text = str(self.agent.memory.chat_memory) + "\n" + text
                text = text.lstrip()

                response = self.agent.ask_question(text=text, stream=stream)
                self.answer_text = self.write_response(agent_name=self.config.agent_name, stream=stream, agent_response=response, is_quiet=self.state.is_quiet)
                self.add_text_to_history(self.config.agent_name, self.answer_text)
                if self.state.is_stopped:
                    break
                self.response.respond(self.answer_text)
                self.response.wait_for_audio_process()
                self.user_input.question_text = ""
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

    @staticmethod
    def write_response(is_quiet: bool, agent_name: str, stream: bool, agent_response) -> str:
        response: List[str] = []
        if stream:
            if not is_quiet:
                print(f"{agent_name}: ", end="")
            for chunk in agent_response:
                txt = response_to_str(response=chunk, is_quiet=is_quiet)
                print(txt, end="", flush=True)
                response.append(txt.strip())
            print("")
        else:
            txt = response_to_str(response=agent_response, is_quiet=is_quiet)
            response.append(txt)
            print(txt if is_quiet else f"{agent_name}: {txt}")

        return " ".join(response)


def response_to_str(response, is_quiet: bool) -> str:
    if isinstance(response, BaseMessage):
        return response.content
    if isinstance(response, AddableDict):
        if "output" not in response:
            if "steps" in response and not is_quiet:
                return "\nThinking..."
            else:
                return ""
    return response["output"] if "output" in response else str(response)
