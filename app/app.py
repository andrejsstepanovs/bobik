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

        self.settings: Settings = self._load_settings(config_file)
        self.config: Configuration = Configuration(settings=self.settings)
        self.state: ApplicationState = ApplicationState(config=self.config)
        self.pre_parser: StateTransitionParser = StateTransitionParser(config=self.config, state=self.state)

    def _load_settings(self, config_file: str = None) -> Settings:
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

    def print_help(self):
        print("Usage: run.py [--quit] [pre-parser commands] [question]")
        print("")
        print("Available pre-parser commands:")
        print("  Switch between agent and normal mode.")
        print("  With agent:")
        for phrase in self.config.phrases["with_tools"]:
            print(f"    - {phrase}")
        print("")
        print("  No agent:")
        for phrase in self.config.phrases["no_tools"]:
            print(f"    - {phrase}")
        print("  ")
        print("  Quit:")
        for phrase in self.config.phrases["exit"]:
            print(f"    - {phrase}")
        print("")
        print("  Select model by typing its name.")
        print("  Available models:")

        settings: Settings = self.config.settings
        providers_with_api_keys = {
            "google": "google",
            "mistral": "mistral",
            "groq": "groq",
            "openai": "openai",
            "openai_custom": ("openai_custom", "openai_custom"),
            "lm_studio": "openai_custom",
            "ollama": None
        }

        for model_name, model_config in settings.models.items():
            if not model_config.model:
                continue
            provider_key = providers_with_api_keys.get(model_config.provider)
            if provider_key is None:
                continue
            if isinstance(provider_key, tuple):
                api_key, url_key = provider_key
                if self.config.api_keys.get(api_key) is None or self.config.urls.get(url_key) is None:
                    continue
            elif self.config.api_keys.get(provider_key) is None:
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
        print("  Available pre-parser enrichers:")
        for enricher in self.pre_parser.enrichers:
            print(f"   - {enricher.name()}: {enricher.description()}")
            print(f"        phrases: {', '.join(enricher.phrases())}")

        print("")
        print("  Available agent tools:")
        tool_loader = ToolLoader(config=self.config, state=self.state)
        for name in tool_loader.available_tool_names():
            print(f"   - {name}")

        print("")

        print("  Examples:")
        print("  - python run.py once quit .. What is the capital of France")
        print("  - python run.py once quit llm speak What is the capital of France")
        print("  - echo \"what is capital of France?\" | python run.py once quiet llm speak")
        print("  - echo \"What is capital of France? Answer with 1 word.\" | python run.py once quiet llm")
        print("  - echo \"What is capital of France? Answer with 1 word.\" | python run.py once quiet llm > France.txt")
        print("  - cat file.py | python run.py once quiet code add comments to the code. Answer only with code. > file.py")
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

    def _pre_parse_questions(self, questions: list[str]) -> list[str]:
        cleaned_questions: list[str] = list[str]()
        for question in questions:
            commands, question_part = self.pre_parser.split(question)
            found_phrases, found = self.pre_parser.change_state(commands=commands)
            if found:
                print_text(state=self.state, text=f"found_phrases: {', '.join(found_phrases)}")
                new_question = question
                for phrase in found_phrases:
                    new_question = new_question.replace(phrase, "").strip()
                cleaned_questions.append(new_question.strip())
            else:
                cleaned_questions.append(question_part)

        return cleaned_questions

    def process_arguments(self, args: list[str]):
        if "--help" in args:
            self.print_help()
            quit(0)

    def conversation(self, questions: list[str] = None):
        """Start the main loop and print or speak multiple conversation answers."""
        if self.manager is None:
            self.load_manager()
        questions = self._pre_parse_questions(questions=questions)
        try:
            asyncio.run(self.manager.main_loop(questions))
        except KeyboardInterrupt:
            print_text(state=self.state, text="Exiting...")

    async def answer(self, questions: List[str]) -> str:
        """Ask a question and return the answer."""
        try:
            if self.manager is None:
                self.load_manager()
            for question in questions:
                self.manager.answer_text = ""
                await self.manager.question_answer(question=question)
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
