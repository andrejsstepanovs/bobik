import asyncio
import yaml
import os
import sys
from dotenv import load_dotenv
from typing import List
from .manager import ConversationManager
from .io_output import TextToSpeech
from .my_print import print_text
from .config import Configuration, Settings
from .llm_provider import LanguageModelProvider
from .state import ApplicationState
from .transcript import Transcript
from .tool_loader import ToolLoader
from .pkg.beep import BeepGenerator
from .llm_agent import LargeLanguageModelAgent
from .parsers import StateTransitionParser

load_dotenv()


class App:
    def __init__(self, config_file: str = None):
        self.manager: ConversationManager = None
        self.llm_provider: LanguageModelProvider = None
        self.llm_agent: LargeLanguageModelAgent = None
        self.tool_provider: ToolLoader = None

        self.settings: Settings = self.load_settings(config_file)
        self.config: Configuration = Configuration(settings=self.settings)
        self.state: ApplicationState = ApplicationState(config=self.config)
        self.pre_parser: StateTransitionParser = StateTransitionParser(config=self.config, state=self.state)

    def load_settings(self, config_file: str = None) -> Settings:
        env_name = "BOBIK_CONFIG_FILE"
        if config_file is None:
            config_file: str = os.getenv(env_name)

        if not config_file:
            raise Exception(f"{env_name} environment variable not set. Check `examples/`.")

        with open(config_file, "r") as stream:
            try:
                raw_config: dict = yaml.safe_load(stream)
                return Settings(**raw_config)
            except yaml.YAMLError as exc:
                print(f"Failed to load {config_file}. Not valid yaml file. {exc}")
                exit(1)
            except Exception as e:
                print(f"Failed to load {config_file}. Not valid. {e}")
                exit(1)

    def load_agent(self):
        self.manager.reload_agent()

    def load_manager(self):
        self.llm_provider = LanguageModelProvider(config=self.config, state=self.state)
        self.tool_provider = ToolLoader(config=self.config, state=self.state)
        self.llm_agent = LargeLanguageModelAgent(
            config=self.config,
            provider=self.llm_provider,
            state=self.state,
            function_provider=self.tool_provider
        )
        self.manager = ConversationManager(
            parser=self.pre_parser,
            config=self.config,
            state=self.state,
            provider=self.llm_provider,
            tool_loader=self.tool_provider,
            agent=self.llm_agent,
            response=TextToSpeech(config=self.config, state=self.state),
            collector=Transcript(),
            beep=BeepGenerator(),
        )
        return self.manager

    def get_manager(self) -> ConversationManager:
        if self.manager is None:
            self.load_manager()
        return self.manager

    def conversation(self, questions: list[str] = None):
        """Start the main loop and print or speak multiple conversation answers."""
        questions, found = self.get_manager().pre_parse_questions(questions=questions)
        try:
            asyncio.run(self.get_manager().main_loop(questions))
        except KeyboardInterrupt:
            print_text(state=self.state, text="Exiting...")

    async def answer(self, questions: List[str]) -> str:
        """Ask a question and return the answer."""
        try:
            for question in questions:
                self.get_manager().answer_text = ""
                await self.get_manager().question_answer(question=question)
            return self.get_manager().answer_text
        except KeyboardInterrupt:
            if not self.state.is_quiet:
                print("Exiting...")
            quit(0)

    @staticmethod
    def stdin_input() -> str:
        piped_input: List[str] = []
        stdin_input: str = ""

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
