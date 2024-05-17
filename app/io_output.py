import shutil
import subprocess
import requests
import app
import threading
from pynput import keyboard
from pynput.keyboard import Key
import time
import urllib.parse
from app.config import Configuration
from app.state import ApplicationState
from app.parsers import print_text


class KeyPressHandler:
    def __init__(self, audio_process):
        self.audio_process = audio_process
        self.stop_event = threading.Event()
        self.listener = None
        self.last_ctrl_press_time = 0

    def handle_double_ctrl(self, key):
        if key == Key.alt_l or key == Key.alt_r:
            current_time = time.time()
            if current_time - self.last_ctrl_press_time < 0.5:
                self.stop_handler()
                return False  # Stop the listener
            self.last_ctrl_press_time = current_time

    def stop_handler(self):
        self.stop_event.set()
        if self.audio_process:
            self.audio_process.terminate()  # Stop the audio playback
        if self.listener:
            self.listener.stop()  # Stop the listener


class TextToSpeech:
    def __init__(self, config: Configuration, state: ApplicationState):
        self.audio_process = None
        self.key_press_handler = None
        self.config = config
        self.state = state

    @staticmethod
    def is_installed(lib_name: str) -> bool:
        lib = shutil.which(lib_name)
        return lib is not None

    def respond(self, text: str):
        if self.state.output_model != "text":
            self.speak(text)

    def speak(self, text: str):
        if self.state.output_model_options["provider"] == "deepgram":
            if self.config.deepgram_settings["api_key"] is None:
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

            self.key_press_handler = KeyPressHandler(audio_process=self.audio_process)

            # Start the keyboard listener in a separate thread
            listener_thread = threading.Thread(target=self.start_listener)
            listener_thread.daemon = True  # Set as daemon thread, so it exits when main thread finishes
            listener_thread.start()

            try:
                stream_started = False
                headers = {
                    "Authorization": f"Token {self.config.deepgram_settings['api_key']}",
                    "Content-Type": "application/json"
                }
                # Call Deepgram API to get audio stream.
                url = self.config.deepgram_settings['url']+"speak?" + urllib.parse.urlencode({
                    "model": self.state.output_model_options["model"],
                    "performance": self.state.output_model_options["performance"],
                    "encoding": self.state.output_model_options["encoding"],
                    "sample_rate": self.state.output_model_options["sample_rate"],
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
                            if self.key_press_handler.stop_event.is_set():
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
        listener = keyboard.Listener(on_press=self.key_press_handler.handle_double_ctrl)
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
