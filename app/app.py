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
        self.state_change_parser: StateTransitionParser = StateTransitionParser(config=self.config, state=self.state)

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
            parser=self.state_change_parser,
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

    def print_help(self):
        print("Usage: run.py [--once or --quit] [--quiet] [pre-parser commands] [question]")
        print("")
        print("Available pre-parser commands:")
        print("  Switch between agent and normal mode.")
        print("  With agent:")
        for phrase in self.config["with_tools_phrases"]:
            print(f"    - {phrase}")
        print("")
        print("  No agent:")
        for phrase in self.config["no_tools_phrases"]:
            print(f"    - {phrase}")
        print("  ")
        print("  Quit:")
        for phrase in self.config.phrases["exit"]:
            print(f"    - {phrase}")
        print("")
        print("  Select model by typing its name.")
        print("  Available models:")

        settings: Settings = self.config.settings
        for model_name, model_config in settings.models.items():
            if model_config.model is None or model_config.model == "":
                continue
            if model_config.provider == "google" and self.config.api_keys["google"] is None:
                continue
            if model_config.provider == "mistral" and self.config.api_keys["mistral"] is None:
                continue
            if model_config.provider == "groq" and self.config.api_keys["groq"] is None:
                continue
            if model_config.provider == "openai" and self.config.api_keys["openai"] is None:
                continue
            if model_config.provider == "openai_custom" and (self.config.api_keys["custom_provider"] is None or self.config.urls["openai_custom"] is None):
                continue
            if model_config.provider == "lm_studio" and self.config.urls["openai_custom"] is None:
                continue
            if model_config.provider == "ollama":
                continue
            print(f"    - {model_name} ({model_config.provider} / {model_config.model})")
        print("")
        print("  Available Input methods:")
        for model_name, model_config in settings.io_input.items():
            if model_config.provider == "deepgram_settings" and self.config.api_keys["deepgram"] is None:
                continue
            print(f"    - {model_name} ({model_config.provider} / {model_config.model})")
        print("")
        print("  Available Output methods:")
        for model_name, model_config in self.config.settings.io_output.items():
            if model_config.provider == "deepgram_settings" and self.config.api_keys["deepgram"] is None:
                continue
            print(f"    - {model_name} ({model_config.provider} / {model_config.model}")
        print("")
        print("  Examples:")
        print("  - python run.py --once --quit What is the capital of France")
        print("  - python run.py --once --quit llm speak What is the capital of France")
        print("  - echo \"what is capital of France?\" | python run.py --once --quiet llm speak")
        print("  - echo \"What is capital of France? Answer with 1 word.\" | python run.py --once --quiet llm")
        print("  - echo \"What is capital of France? Answer with 1 word.\" | python run.py --once --quiet llm > France.txt")
        print("  - cat file.py | python run.py --once --quiet code add comments to the code. Answer only with code. > file.py")
        print("  - # example of model switching")
        print("  - python run.py")
        print("  - > Tell me a story.")
        print("  - > gpt3")
        print("  - > summarize the story")
        print("  - > quit")
        print("  - # example of model and agent switching")
        print("  - python run.py llm groq")
        print("  - > Tell me a story.")
        print("  - > gpt3")
        print("  - > agent")
        print("  - > summarize the story")
        print("  - > quit")

    def process_arguments(self, initial_arg_phrases: list[str]) -> tuple[bool, bool, str]:
        first_question: str = ""
        args_len: int = len(initial_arg_phrases)
        loop: bool = True
        quiet: bool = False

        i = 0
        while i < args_len:
            if initial_arg_phrases[i] in ["--once", "--quit"]:
                loop = False
            elif initial_arg_phrases[i] == "--help":
                self.print_help()
                quit(0)
            elif initial_arg_phrases[i] == "--quiet":
                quiet = True
                self.state.is_quiet = quiet
            else:
                found, must_exit = self.state_change_parser.quick_state_change(initial_arg_phrases[i].strip())
                if not found:
                    break
            i += 1

        if i < args_len:
            first_question = ' '.join(initial_arg_phrases[i:]).strip()

        return loop, quiet, first_question

    def conversation(self, loop: bool = False, question: str = ""):
        """Start the main loop and print or speak multiple conversation answers."""
        first_questions: List[str] = []
        if question != "":
            first_questions = [question]
        try:
            if self.manager is None:
                self.load_manager()
            asyncio.run(self.manager.main_loop(first_questions))
        except KeyboardInterrupt:
            print_text(state=self.state, text="Exiting...")

    def one_shot(self, question: str = ""):
        """Print or speak answer."""
        first_questions: List[str] = []
        if question != "":
            first_questions = [question]
        try:
            if self.manager is None:
                self.load_manager()
            asyncio.run(self.manager.question_answer(first_questions))
        except KeyboardInterrupt:
            print_text(state=self.state, text="Exiting...")

    async def answer(self, questions: List[str]) -> str:
        """Ask a question and return the answer."""
        try:
            if self.manager is None:
                self.load_manager()
            self.manager.answer_text = ""
            await self.manager.question_answer(questions)
            return self.manager.answer_text
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
