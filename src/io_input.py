import asyncio
import logging
import threading
import pyperclip
import os
from .alt import AltKeyDoublePressDetector
from .config import Configuration
from .state import ApplicationState
from .transcript import Transcript
from .pkg.beep import BeepGenerator
from .my_print import print_text
import sys
from colorama import Fore, Style, init as colorama_init
from deepgram import (
    DeepgramClient,
    DeepgramClientOptions,
    LiveTranscriptionEvents,
    LiveOptions,
    Microphone,
)
if os.name == 'nt':
    from pyreadline import Readline
else:
    import readline

colorama_init()

async def _listen_to_input(config: Configuration, state: ApplicationState, transcript_collector: Transcript, callback):
    if state.input_model_options.provider == "deepgram":
        if config.api_keys["deepgram"] is None:
            raise Exception("Deepgram API key not set")

        if os.name == 'nt':
            raise Exception("Deepgram Windows audio input is not supported.")

        transcription_complete: asyncio.Event = asyncio.Event()
        try:
            client_config = DeepgramClientOptions(options={"keepalive": "true"}, verbose=logging.ERROR)
            deepgram_client: DeepgramClient = DeepgramClient(api_key=config.api_keys["deepgram"], config=client_config)

            deepgram_connection = deepgram_client.listen.asynclive.v("1")
            print_text(state=state, text=f"{Fore.YELLOW}Listening...{Style.RESET_ALL}")

            async def on_message(self, result, **kwargs):
                sentence: str = result.channel.alternatives[0].transcript

                if not result.speech_final:
                    if len(sentence.strip()) > 0:
                        print_text(state=state, text=f"{config.user_name}: {Fore.RED}{sentence} ...{Style.RESET_ALL}")
                    transcript_collector.add_section(sentence)
                else:
                    transcript_collector.add_section(sentence)
                    full_sentence: str = transcript_collector.retrieve_transcript()
                    if len(full_sentence.strip()) > 0:
                        full_sentence = full_sentence.strip()
                        print_text(state=state, text=f"{config.user_name}: {Fore.GREEN}{Style.BRIGHT}{full_sentence}{Style.RESET_ALL}")
                        callback(full_sentence)
                        transcript_collector.clear_transcript()
                        transcription_complete.set()

            deepgram_connection.on(LiveTranscriptionEvents.Transcript, on_message)

            options: LiveOptions = LiveOptions(
                model=state.input_model_options.model,
                punctuate=state.input_model_options.punctuate,
                language=state.input_model_options.language,
                encoding=state.input_model_options.encoding,
                channels=state.input_model_options.channels,
                sample_rate=state.input_model_options.sample_rate,
                endpointing=str(state.input_model_options.endpointing),
                smart_format=state.input_model_options.smart_format,
            )

            await deepgram_connection.start(options)

            microphone: Microphone = Microphone(deepgram_connection.send)
            microphone.start()

            await transcription_complete.wait()

            microphone.finish()

            await deepgram_connection.finish()
        except Exception as e:
            print(f"Could not open socket: {e}")
            return
    else:
        raise Exception("Unknown provider given")


class UserInput:
    def __init__(self, config: Configuration, state: ApplicationState, transcript_collector: Transcript, beep: BeepGenerator):
        self.config = config
        self.state = state
        self.transcript_collector = transcript_collector
        self.beep = beep
        self.question_text = ""
        self._ignore_next_questions: int = None

    async def ask_input(self):
        if self.state.input_model_options.provider != "text":
            if self.state.is_hotkey_enabled:
                print_text(state=self.state, text=f"Tap Alt key {self.config.keypress_count_start_talking} times and start talking")
                if self.state.output_model == "deepgram":
                    print_text(state=self.state, text="And same to stop long playback.")

                detector: AltKeyDoublePressDetector = AltKeyDoublePressDetector(
                    threading_type=threading.Lock(),
                    state=self.state,
                    keypress_count=self.config.keypress_count_start_talking,
                )
                detector.start_key_listener()

            self.beep.play_beep()
            self.transcript_collector.clear_transcript()
            await _listen_to_input(
                config=self.config,
                state=self.state,
                transcript_collector=self.transcript_collector,
                callback=self.set,
            )
        else:
            if self._ignore_next_questions is not None:
                self._ignore_next_questions -= 1
                if self._ignore_next_questions > 1:
                    input("")
                    sys.stdout.write("\033[F")  # Cursor up one line
                    self.set("")
                    return
                else:
                    self._ignore_next_questions = None

            print(f"{Fore.YELLOW}{self.config.user_name}:{Fore.RESET} ", end="")
            text: str = input()

            try:
                # Check if clipboard content exists and appended it to the question.
                clipboard = pyperclip.paste()
                if len(clipboard) > 0:
                    clipboard_parts = clipboard.split(os.linesep)
                    if len(clipboard_parts) > 1:
                        if text.endswith(clipboard_parts[0]):
                            if self._ignore_next_questions is None:
                                self._ignore_next_questions = len(clipboard_parts)
                            for line in clipboard_parts[1:]:
                                print(line)
                                text += f"{os.linesep}{line}"
            except pyperclip.PyperclipException:
                pass

            self.set(text)

    def set(self, text: str):
        self.question_text = text

    def get(self) -> str:
        return self.question_text
