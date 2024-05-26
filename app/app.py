import asyncio
import yaml
import sys
import os
from dotenv import load_dotenv
from app.manager import ConversationManager
from app.io_output import TextToSpeech
from app.config import Configuration
from app.llm_provider import LanguageModelProvider
from app.state import ApplicationState
from app.transcript import Transcript
from app.tool_loader import ToolLoader
from app.pkg.beep import BeepGenerator
from app.llm_agent import LargeLanguageModelAgent
from app.parsers import StateTransitionParser
from app.pkg.history import ConversationHistory

load_dotenv()


class App:
    def __init__(self, config_file: str = ""):
        self.config_file = config_file
        self.manager = None
        self.options = None
        self.state_change_parser = None
        self.llm_provider = None
        self.llm_agent = None
        self.tool_provider = None
        self.config = None
        self.state = None
        self.history = ConversationHistory()

    def load_config_and_state(self):
        self.options = self.load_options()
        self.config = Configuration(settings=self.options)
        self.state = ApplicationState(config=self.config)

    def load_options(self) -> dict:
        if self.config_file:
            os.environ["COMPUTER_CONFIG_FILE"] = self.config_file

        config_path = os.getenv("COMPUTER_CONFIG_FILE")
        if config_path is None:
            raise Exception("COMPUTER_CONFIG_FILE environment variable not set. Check `my_config.yaml.example` file.")

        if not os.path.exists(config_path):
            raise Exception(f"{config_path} file not found")

        with open(config_path, "r") as file:
            options = yaml.safe_load(file)

        return options

    def load_state_change_parser(self):
        self.state_change_parser = StateTransitionParser(config=self.config, state=self.state)

    def load_manager(self):
        self.llm_provider = LanguageModelProvider(config=self.config, state=self.state)
        self.tool_provider = ToolLoader(config=self.config, state=self.state)

        self.llm_agent = LargeLanguageModelAgent(
            config=self.config,
            llm_provider=self.llm_provider,
            state=self.state,
            function_provider=self.tool_provider
        )

        self.manager = ConversationManager(
            parser=self.state_change_parser,
            config=self.config,
            state=self.state,
            history=self.history,
            provider=self.llm_provider,
            tool_loader=self.tool_provider,
            agent=self.llm_agent,
            response=TextToSpeech(config=self.config, state=self.state),
            collector=Transcript(),
            beep=BeepGenerator(),
        )
        return self.manager

    def process_arguments(self) -> tuple[bool, bool, str]:
        first_question = ""
        initial_arg_phrases = sys.argv[1:]
        args_len = len(initial_arg_phrases)
        loop = True
        quiet = False
        if args_len > 0:
            i = 0
            """It is important to use these flags before any following command parameters!"""
            for phrase in initial_arg_phrases:
                if phrase == "--once":
                    loop = False
                    i += 1
                elif phrase == "--quiet":
                    quiet = True
                    self.state.is_quiet = quiet
                    i += 1
                else:
                    break

            for phrase in initial_arg_phrases[i:]:
                found, must_exit = self.state_change_parser.quick_state_change(phrase.strip())
                if not found:
                    break
                i += 1

            if i > 0 and not quiet:
                print(f"Got {i} args:", initial_arg_phrases[:i])

            if len(initial_arg_phrases[i:]) > 0:
                first_question = initial_arg_phrases[i:]
                if isinstance(first_question, list):
                    first_question = ' '.join(map(str, first_question))
                first_question = first_question.strip()

        return loop, quiet, first_question

    def start(self, loop: bool = False, question: str = ""):
        try:
            if loop:
                asyncio.run(self.manager.main_loop(question))
            else:
                asyncio.run(self.manager.question_answer(question))

        except KeyboardInterrupt:
            if not self.state.is_quiet:
                print("Exiting...")
            quit(0)

    def stdin_input(self) -> str:
        piped_input = []

        if sys.stdin is not None and not sys.stdin.isatty():
            for line in sys.stdin:
                piped_input.append(line)
            sys.stdin.close()
            sys.stdin = open("/dev/tty")

        stdin_input = ""
        if piped_input:
            stdin_input = "".join(piped_input)
            if stdin_input:
                stdin_input = "\n\n" + stdin_input

        return stdin_input
