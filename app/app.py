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
from app.settings import Settings
from app.transcript import Transcript
from app.tool_loader import ToolLoader
from app.pkg.beep import BeepGenerator
from app.llm_agent import LargeLanguageModelAgent
from app.parsers import StateTransitionParser

load_dotenv()


class App:
    def __init__(self, config_file: str = ""):
        self.config_file = config_file
        self.manager = None
        self.settings = None
        self.state_change_parser = None
        self.llm_provider = None
        self.llm_agent = None
        self.tool_provider = None
        self.config = None
        self.state = None

    def load_config_and_state(self):
        self.settings = self.load_options()
        self.config = Configuration(settings=self.settings)
        self.state = ApplicationState(config=self.config)

    def load_options(self) -> Settings:
        if self.config_file:
            os.environ["COMPUTER_CONFIG_FILE"] = self.config_file

        config_path = os.getenv("COMPUTER_CONFIG_FILE")
        if config_path is None:
            raise Exception("COMPUTER_CONFIG_FILE environment variable not set. Check `my_config.yaml.example` file.")

        if not os.path.exists(config_path):
            raise Exception(f"{config_path} file not found")

        return self.load_settings(config_path)

    def load_settings(self, file_path: str) -> Settings:
        with open(file_path, "r") as stream:
            try:
                raw_config = yaml.safe_load(stream)
                return Settings(**raw_config)
            except yaml.YAMLError as exc:
                print(f"Failed to load {file_path}. Not valid yaml file. {exc}")
                exit(1)
            except Exception as e:
                print(f"Failed to load {file_path}. Not valid. {e}")
                exit(1)

    def load_state_change_parser(self):
        self.state_change_parser = StateTransitionParser(config=self.config, state=self.state)

    def load_agent(self):
        self.manager.reload_agent()

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
        for phrase in self.config.with_tools_phrases:
            print(f"    - {phrase}")
        print("")
        print("  No agent:")
        for phrase in self.config.no_tools_phrases:
            print(f"    - {phrase}")
        print("  ")
        print("  Quit:")
        for phrase in self.config.exit_phrases:
            print(f"    - {phrase}")
        print("")
        print("  Select model by typing its name.")
        print("  Available models:")

        settings: Settings = self.config.settings
        for model_name, model_config in settings.models.items():
            if model_config.model is None or model_config.model == "":
                continue
            if model_config.provider == "google" and self.config.google_settings["api_key"] is None:
                continue
            if model_config.provider == "mistral" and self.config.mistral_settings["api_key"] is None:
                continue
            if model_config.provider == "groq" and self.config.groq_settings["api_key"] is None:
                continue
            if model_config.provider == "openai" and self.config.openai_settings["api_key"] is None:
                continue
            if model_config.provider == "openai_custom" and (self.config.openai_settings["api_key"] is None or self.config.custom_provider_settings["base_url"] is None):
                continue
            if model_config.provider == "lm_studio" and self.config.lmstudio_provider_settings["base_url"] is None:
                continue
            if model_config.provider == "ollama" and self.config.ollama_settings["enabled"]:
                continue
            print(f"    - {model_name} ({model_config.provider} / {model_config.model})")
        print("")
        print("  Available Input methods:")
        for model_name, model_config in settings.io_input.items():
            if model_config.provider == "deepgram_settings" and self.config.deepgram_settings["api_key"] is None:
                continue
            print(f"    - {model_name} ({model_config.provider} / {model_config.model})")
        print("")
        print("  Available Output methods:")
        for model_name, model_config in self.config.settings.io_output.items():
            if model_config.provider == "deepgram_settings" and self.config.deepgram_settings["api_key"] is None:
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
        first_question = ""
        args_len = len(initial_arg_phrases)
        loop = True
        quiet = False
        if args_len > 0:
            i = 0
            """It is important to use these flags before any following command parameters!"""
            for phrase in initial_arg_phrases:
                if phrase == "--once" or phrase == "--quit":
                    loop = False
                    i += 1
                elif phrase == "--help":
                    self.print_help()
                    quit(0)
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
        if question == "":
            first_questions = []
        else:
            first_questions = [question]
        try:
            if loop:
                asyncio.run(self.manager.main_loop(first_questions))
            else:
                asyncio.run(self.manager.question_answer(first_questions))

        except KeyboardInterrupt:
            if not self.state.is_quiet:
                print("Exiting...")
            quit(0)

    async def question(self, questions: list[str]) -> str:
        try:
            self.manager.answer_text = ""
            await self.manager.question_answer(questions)
            return self.manager.answer_text
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
