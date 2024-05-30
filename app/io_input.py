import asyncio
import logging
import threading
import os
from .alt import AltKeyDoublePressDetector
from .config import Configuration
from .state import ApplicationState
from .transcript import Transcript
from .pkg.beep import BeepGenerator
from .my_print import print_text
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


async def listen_to_input(config: Configuration, state: ApplicationState, transcript_collector: Transcript, callback):
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
            print_text(state=state, text="\033[93m" + "Listening..." + "\033[0m")

            async def on_message(self, result, **kwargs):
                sentence: str = result.channel.alternatives[0].transcript

                if not result.speech_final:
                    if len(sentence.strip()) > 0:
                        print_text(state=state, text=f"{config.user_name}: \033[91m {sentence} ... \033[0m")
                    transcript_collector.add_section(sentence)
                else:
                    transcript_collector.add_section(sentence)
                    full_sentence: str = transcript_collector.retrieve_transcript()
                    if len(full_sentence.strip()) > 0:
                        full_sentence = full_sentence.strip()
                        print_text(state=state, text=f"{config.user_name}: \033[32;1m {full_sentence} \033[0m")
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

    async def ask_input(self):
        if self.state.input_model_options.provider != "text":
            if self.state.is_hotkey_enabled:
                keypress_count = 2
                print_text(state=self.state, text=f"Double-tap {keypress_count} times and start talking")
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
            await listen_to_input(
                config=self.config,
                state=self.state,
                transcript_collector=self.transcript_collector,
                callback=self.set,
            )
        else:
            text: str = input(f"{self.config.user_name}: ")
            self.set(text)

    def set(self, text: str):
        self.question_text = text

    def get(self) -> str:
        return self.question_text
