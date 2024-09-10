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
from .settings import Settings
from langchain_core.exceptions import OutputParserException
from colorama import Fore, Style, init as colorama_init

colorama_init()


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
        self.loop_iterations = 0

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
        self._last_question: str = ""

    def reload_agent(self, force: bool = False) -> LargeLanguageModelAgent:
        if self.current_state_hash != self.state.get_hash() or force:
            self.current_state_hash = self.state.get_hash()
            print_text(state=self.state, text="Loading LLM...")
            self.agent.reload()
        return self.agent

    def clear_memory(self):
        self.agent.get_memory().clear()
        self.agent.load_memory(force=True)
        self.agent.initialize_prompt()

    async def main_loop(self, questions: list[str] = None, print_questions: bool = False):
        async def answer(question: str = None):
            if print_questions:
                print(f"{self.config.user_name}: {Fore.YELLOW}{Style.BRIGHT}{question}{Style.RESET_ALL}")
            stop = await self.question_answer(question=question)
            return stop or self.state.is_stopped

        while True:
            if questions is not None:
                for question in questions:
                    if await answer(question):
                        return
                questions = None
            elif await answer():
                return

    async def question_answer(self, question: str = None) -> bool:
        if self._last_question != "" or question != "":
            self._print_status()

        if question:
            self.user_input.set(question)
        else:
            await self.user_input.ask_input()

        self._last_question = self.user_input.get()

        if self.user_input.get() == "help":
            self.print_help()
            return False

        if await self._tasks(question):
            return False

        clean_questions, found = self.pre_parse_questions(questions=[self.user_input.get()])
        if found:
            if self.state.is_stopped:
                return True
            self.reload_agent()
            return False

        question = clean_questions[0]
        if self.parser.is_empty(question):
            return False

        tool_call_response = self._manual_tool_call(query=question)
        if tool_call_response != "":
            self.response.respond(tool_call_response)
            self.history.save(self.config.agent_name, tool_call_response)
            return False

        was_changed, enriched_text = self.parser.enrich(text=question)
        self.user_input.set(enriched_text)
        who = self.config.user_name if not was_changed else "Pre-parser"
        self.history.save(who, self.user_input.get())

        if self.agent.model is None:
            self.reload_agent(force=False)

        tries = 0
        while tries < self.config.retry_settings["max_tries"]:
            try:
                text = f"{self.config.user_name}: {self.user_input.get()}"
                if not self.state.are_tools_enabled:
                    text = self.history.get_messages() + "\n\n" + text

                self._process(question=text.lstrip())

                self.history.save(self.config.agent_name, self.answer_text)
                if self.state.is_stopped:
                    return True

                self.user_input.set("")
                break
            except KeyboardInterrupt:
                if not self.state.is_quiet:
                    print("OK...")
                break
            except OutputParserException:
                print_text(state=self.state, text="Output parser exception.")
                self.response.respond("Agent failed parsing answer. Please try different model.")
                break
            except Exception as e:
                tr = traceback.format_exc()
                print_text(state=self.state, text=f"Exception: {e.__class__.__name__} > {tr}")
                sleep_sec = self.config.retry_settings["sleep_seconds_between_tries"]
                print_text(state=self.state, text=f"Sleep and try again after: {sleep_sec} sec")
                tries += 1
                time.sleep(sleep_sec)

    def _process(self, question: str = "") -> str:
        stream = not self.state.is_quiet and not self.state.are_tools_enabled

        response = self.agent.ask_question(text=question, stream=stream)
        self.answer_text = self.response.write_response(stream=stream, agent_response=response)

        self.response.respond(self.answer_text)

    def _manual_tool_call(self, query: str = None) -> str:
        parts = query.split(" ")
        if len(parts) == 0 or len(parts) > 2:
            return ""

        param = parts[1] if len(parts) == 2 else None
        tool_name, tool_call_response = self.tool_loader.call_tool(name=parts[0], param=param)
        if tool_name != "" and tool_call_response != "":
            print_text(state=self.state, text=f"Manual tool call: {tool_name}")
            self.response.write_response(stream=False, agent_response=tool_call_response)
        return tool_call_response

    async def _tasks(self, task_name: str = None) -> bool:
        if task_name not in self.config.settings.tasks:
            return False

        def print_status(status: str):
            color = Fore.CYAN
            color_bold = Fore.CYAN + Style.BRIGHT
            reset = Style.RESET_ALL
            txt = f"{color}-> Task{reset} '{color_bold}{task_name}{reset}' {color}{status}{reset}"
            print_text(state=self.state, text=txt)

        last_model = self.state.llm_model
        last_is_agent =self.state.are_tools_enabled
        last_is_quiet =self.state.is_quiet

        print_status("started")
        questions = self.config.settings.tasks[task_name]
        questions.insert(0, "quiet")

        for question in questions:
            print(question)
            await self.question_answer(question=question)
        print_status("finished")

        self.state.llm_model = last_model
        self.state.are_tools_enabled = last_is_agent
        self.state.is_quiet = last_is_quiet
        self.reload_agent()

        return True

    def _print_status(self):
        self.loop_iterations += 1
        if self.state.is_quiet:
            return

        yellow = Fore.YELLOW
        red_bold_underline = Fore.RED + Style.BRIGHT + "\033[4m"
        reset = Style.RESET_ALL
        blue = Fore.BLUE

        mode = "simple"
        if self.state.are_tools_enabled:
            mode = f"{blue}agent{reset}"
        formatted_string = (
            f"{self.loop_iterations}) {yellow}{self.state.input_model}{reset} → "
            f"{mode} {red_bold_underline}{self.state.llm_model}{reset} ({self.state.llm_model_options.model}) → "
            f"{yellow}{self.state.output_model}{reset}"
        )
        print_text(state=self.state, text=formatted_string)

    def pre_parse_questions(self, questions: list[str]) -> tuple[list[str], bool]:
        cleaned_questions: list[str] = list[str]()
        something_found = False
        for question in questions:
            found_phrases, found = self.parser.change_state(commands=question)
            if not found:
                cleaned_questions.append(question)
                continue

            something_found = True
            print_text(state=self.state, text=f"found_phrases: {', '.join(found_phrases)}")
            new_question = question.replace(" ".join(found_phrases), "").strip()
            if new_question:
                cleaned_questions.append(new_question)

        return cleaned_questions, something_found

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
            "anthropic": "anthropic",
            "mistral": "mistral",
            "groq": "groq",
            "openai": "openai",
            "openai_custom": ("openai_custom", "openai_custom"),
            "lm_studio": "openai_custom",
            "ollama": "1"
        }

        for model_name, model_config in settings.models.items():
            if not model_config.model:
                continue
            provider_key = providers_with_api_keys.get(model_config.provider)
            if provider_key is None and model_config.provider != "ollama":
                continue
            if isinstance(provider_key, tuple):
                api_key, url_key = provider_key
                if self.config.api_keys.get(api_key) is None or self.config.urls.get(url_key) is None:
                    continue
            elif self.config.api_keys.get(provider_key) is None and model_config.provider != "ollama":
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
        for enricher in self.parser.enrichers:
            print(f"   - {enricher.name()}: {enricher.description()}")
            print(f"        phrases: {', '.join(enricher.phrases())}")

        print("")
        print("  Available agent tools:")
        tool_loader = ToolLoader(config=self.config, state=self.state)
        for name in tool_loader.available_tool_names():
            print(f"   - {name}")

        print("")
        print("  Available tasks:")
        for name, commands in self.config.settings.tasks.items():
            print(f"   - {name}:")
            for command in commands:
                print(f"     - {command}")

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
