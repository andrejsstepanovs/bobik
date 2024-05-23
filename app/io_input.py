import asyncio
import logging
import pyperclip
import os
if os.name == 'nt':
    from pyreadline import Readline
else:
    import readline

from deepgram import (
    DeepgramClient,
    DeepgramClientOptions,
    LiveTranscriptionEvents,
    LiveOptions,
    Microphone,
)
from app.alt import AltKeyDoublePressDetector
from app.config import Configuration
from app.state import ApplicationState
from app.transcript import Transcript
from app.pkg.beep import BeepGenerator
from app.my_print import print_text


async def listen_to_input(config: Configuration, state: ApplicationState, transcript_collector: Transcript, callback):
    if state.input_model_options["provider"] == "deepgram":
        if config.deepgram_settings["api_key"] is None:
            raise Exception("Deepgram API key not set")

        if os.name == 'nt':
            raise Exception("Deepgram Windows audio input is not supported.")

        transcription_complete = asyncio.Event()
        try:
            client_config = DeepgramClientOptions(options={"keepalive": "true"}, verbose=logging.ERROR)
            deepgram_client: DeepgramClient = DeepgramClient(api_key=config.deepgram_settings["api_key"], config=client_config)

            deepgram_connection = deepgram_client.listen.asynclive.v("1")
            print_text(state=state, text="\033[93m" + "Listening..." + "\033[0m")

            async def on_message(self, result, **kwargs):
                sentence = result.channel.alternatives[0].transcript

                if not result.speech_final:
                    if len(sentence.strip()) > 0:
                        print_text(state=state, text=f"{config.user_name}: \033[91m {sentence} ... \033[0m")
                    transcript_collector.add_section(sentence)
                else:
                    transcript_collector.add_section(sentence)
                    full_sentence = transcript_collector.retrieve_transcript()
                    if len(full_sentence.strip()) > 0:
                        full_sentence = full_sentence.strip()
                        print_text(state=state, text=f"{config.user_name}: \033[32;1m {full_sentence} \033[0m")
                        callback(full_sentence)
                        transcript_collector.initialize()
                        transcription_complete.set()

            deepgram_connection.on(LiveTranscriptionEvents.Transcript, on_message)

            options = LiveOptions(
                model=state.input_model_options["model"],
                punctuate=state.input_model_options["punctuate"],
                language=state.input_model_options["language"],
                encoding=state.input_model_options["encoding"],
                channels=state.input_model_options["channels"],
                sample_rate=state.input_model_options["sample_rate"],
                endpointing=state.input_model_options["endpointing"],
                smart_format=state.input_model_options["smart_format"],
            )

            await deepgram_connection.start(options)

            microphone = Microphone(deepgram_connection.send)
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

    async def get_input(self):
        if self.state.input_model_options["provider"] != "text":
            if self.state.is_hotkey_enabled:
                print_text(state=self.state, text="Double-tap 2 times and start talking")
                if self.state.output_model == "deepgram":
                    print_text(state=self.state, text="And same to stop long playback.")

                detector = AltKeyDoublePressDetector(app_state=self.state)
                detector.start_key_listener()

            self.beep.play_beep()
            await listen_to_input(
                config=self.config,
                state=self.state,
                transcript_collector=self.transcript_collector,
                callback=self.handle_full_sentence,
            )
        else:
            text = input(f"{self.config.user_name}: ")
            split_text = text.split(":")
            if len(split_text) > 1:
                print("###", )
                clipboard_content = pyperclip.paste()
                if clipboard_content != "" and text != clipboard_content and split_text[1].strip() in clipboard_content:
                    text = f"{text[0]}. Use clipboard."

            self.handle_full_sentence(text)

    def handle_full_sentence(self, text):
        self.question_text = text
