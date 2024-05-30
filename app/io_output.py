import shutil
import subprocess
import requests
import threading
from pynput import keyboard
import urllib.parse
from .config import Configuration
from .state import ApplicationState
from .parsers import print_text
from .alt import AltKeyDoublePressDetector


class TextToSpeech:
    def __init__(self, config: Configuration, state: ApplicationState):
        self.audio_process = None
        self.key_press_handler: AltKeyDoublePressDetector = None
        self.config = config
        self.state = state

    @staticmethod
    def is_installed(lib_name: str) -> bool:
        lib: str = shutil.which(lib_name)
        return lib is not None

    def respond(self, text: str):
        if self.state.output_model != "text":
            self.speak(text)

    def speak(self, text: str):
        if self.state.output_model_options.provider == "deepgram":
            if self.config.api_keys["deepgram"] is None:
                raise ValueError("Deepgram API key not found.")

            if not self.is_installed("ffplay"):
                raise ValueError("ffplay not found, necessary to stream audio.")

            try:
                self.audio_process = subprocess.Popen(
                    ["ffplay", "-autoexit", "-", "-nodisp"],
                    stdin=subprocess.PIPE,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
            except Exception as e:
                print(f"Error starting ffplay: {e}")
                return

            if self.audio_process is None:
                print("Failed to start ffplay")
                return

            self.key_press_handler: AltKeyDoublePressDetector = AltKeyDoublePressDetector(
                threading_type=threading.Event(),
                state=self.state,
                keypress_count=self.config.keypress_count_stop_listening,
                audio_process=self.audio_process,
            )

            # Start the keyboard listener in a separate thread
            listener_thread = threading.Thread(target=self.start_listener)
            listener_thread.daemon = True  # Set as daemon thread, so it exits when main thread finishes
            listener_thread.start()

            try:
                stream_started = False
                headers: dict = {
                    "Authorization": f"Token {self.config.api_keys['deepgram']}",
                    "Content-Type": "application/json"
                }
                # Call Deepgram API to get audio stream.
                url: str = self.config.urls['deepgram']+"speak?" + urllib.parse.urlencode({
                    "model": self.state.output_model_options.model,
                    "performance": self.state.output_model_options.performance,
                    "encoding": self.state.output_model_options.encoding,
                    "sample_rate": self.state.output_model_options.sample_rate,
                })

                with requests.post(url, stream=True, headers=headers, json={"text": text}) as r:
                    for chunk in r.iter_content(chunk_size=1024):
                        if chunk:
                            if self.audio_process is not None:
                                self.audio_process.stdin.write(chunk)
                                self.audio_process.stdin.flush()
                            if not stream_started:
                                stream_started = True
                                print_text(self.state, text="Double-tap Alt to stop playback.")
                            if self.key_press_handler.threading.is_set():
                                break
                if self.audio_process is not None and self.audio_process.stdin:
                    self.audio_process.stdin.close()

                # Wait for the process to finish
                if self.audio_process is not None:
                    self.audio_process.wait()
            except BrokenPipeError:
                """when abruptly stopped, we get pipe error exception. We ignore it."""
                ...
            except Exception as e:
                print('Exception in response:', e.__class__.__name__)
                raise e

    def start_listener(self):
        listener = keyboard.Listener(on_press=self.key_press_handler.handle_key_press)
        self.key_press_handler.listener = listener
        listener.start()
        listener.join()

    def terminate_audio_process(self):
        if self.audio_process:
            self.audio_process.terminate()
            print_text(self.state, text="Audio process terminated!")

    def wait_for_audio_process(self):
        if self.audio_process:
            self.audio_process.wait()
        if self.key_press_handler:
            self.key_press_handler.stop_handler()
            if self.key_press_handler.listener:
                self.key_press_handler.listener.stop()
