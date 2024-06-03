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

    async def main_loop(self, questions: list[str] = None, print_questions: bool = False):
        async def answer(question: str = None):
            if print_questions:
                print(f"{self.config.user_name}: \033[32;1m {question} \033[0m")
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
        self._print_status()

        if question:
            self.user_input.set(question)
        else:
            await self.user_input.ask_input()

        if await self._tasks(question):
            return False

        commands, question = self.parser.split(self.user_input.get())

        if self.parser.must_exit(question=commands):
            return True

        if self.parser.must_clear_memory(question=commands):
            self.clear_memory()
            return False

        found_phrases, found = self.parser.change_state(commands=commands)
        if found:
            self.reload_agent(force=True)
            return False

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
                    text = str(self.agent.memory.chat_memory) + "\n\n" + text
                text = text.lstrip()
                self._process(question=text)
                self.user_input.set("")
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

    def _process(self, question: str = ""):
        stream = not self.state.is_quiet and not self.state.are_tools_enabled

        response = self.agent.ask_question(text=question, stream=stream)
        self.answer_text = self.response.write_response(stream=stream, agent_response=response)

        self.history.save(self.config.agent_name, self.answer_text)
        if self.state.is_stopped:
            return

        self.response.respond(self.answer_text)

    def _manual_tool_call(self, query: str = None) -> str:
        parts = query.split(" ")
        if len(parts) == 0 or len(parts) > 2:
            return ""

        tool_name, tool_call_response = self.tool_loader.call_tool(name=parts[0], param=parts[1] if len(parts) == 2 else None)
        if tool_name != "" and tool_call_response != "":
            print_text(state=self.state, text=f"Manual tool call: {tool_name}")
            self.response.write_response(stream=False, agent_response=tool_call_response)
        return tool_call_response

    async def _tasks(self, task_name: str = None) -> bool:
        if task_name not in self.config.settings.tasks:
            return False
        def print_status(status: str):
            color = "\033[96m"
            color_bold = "\033[96;1m"
            reset = "\033[0m"
            txt = f"{color}-> Task{reset} '{color_bold}{task_name}{reset}' {color}{status}{reset}"
            print_text(state=self.state, text=txt)

        print_status("started")
        await self.main_loop(questions=self.config.settings.tasks[task_name] + ["quit"], print_questions=True)
        print_status("finished")
        return True

    def _print_status(self):
        self.loop_iterations += 1
        if self.state.is_quiet:
            return

        yellow = "\033[93m"
        red_bold_underline = "\033[91;1;4m"
        reset = "\033[0m"
        blue = "\033[94m"

        mode = "simple"
        if self.state.are_tools_enabled:
            mode = f"{blue}agent{reset}"
        formatted_string = (
            f"{self.loop_iterations}) {yellow}{self.state.input_model}{reset} → "
            f"{mode} {red_bold_underline}{self.state.llm_model}{reset} ({self.state.llm_model_options.model}) → "
            f"{yellow}{self.state.output_model}{reset}"
        )
        print_text(state=self.state, text=formatted_string)
