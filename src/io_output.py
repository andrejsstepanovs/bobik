import shutil
import subprocess
import requests
import json
import threading
from typing import List
import urllib.parse
from .config import Configuration
from .state import ApplicationState
from .parsers import print_text
from .alt import AltKeyDoublePressDetector
from langchain_core.messages import BaseMessage
from langchain_core.runnables.utils import AddableDict
from colorama import Fore, Style, init as colorama_init

colorama_init()


class TextToSpeech:
    def __init__(self, config: Configuration, state: ApplicationState):
        self.audio_process = None
        self.key_press_handler: AltKeyDoublePressDetector = None
        self.config = config
        self.state = state

    @staticmethod
    def _is_installed(lib_name: str) -> bool:
        lib: str = shutil.which(lib_name)
        return lib is not None

    def write_response(self, stream: bool, agent_response) -> str:
        response: List[str] = []

        if stream:
            if not self.state.is_quiet:
                print(f"{Fore.MAGENTA}{self.config.agent_name}:{Style.RESET_ALL} ", end="")
            for chunk in agent_response:
                txt = self._response_to_str(response=chunk, is_quiet=self.state.is_quiet)
                print(txt, end="", flush=True)
                response.append(txt)
            print("")
        else:
            txt = self._response_to_str(response=agent_response, is_quiet=self.state.is_quiet)
            response.append(txt)
            print(txt if self.state.is_quiet else f"{self.config.agent_name}: {txt}")

        return "".join(response) if stream else " ".join(response)

    def _response_to_str(self, response, is_quiet: bool) -> str:
        if isinstance(response, BaseMessage):
            return response.content
        if isinstance(response, AddableDict):
            if "output" not in response:
                if "steps" in response and not is_quiet:
                    return "\nThinking..."
                else:
                    return ""
        return self._get_response_string(response)

    def _get_response_string(self, response):
        if not isinstance(response, str):
            try:
                if isinstance(response, dict) and "output" in response:
                    return str(response["output"])
                else:
                    response_dict = json.loads(response)
                    if isinstance(response_dict, dict) and "output" in response_dict:
                        return str(response_dict["output"])
                    else:
                        return response
            except json.JSONDecodeError:
                return response
        else:
            return str(response)

    def respond(self, text: str):
        if self.state.output_model != "text":
            self._speak(text)
            self._wait_for_audio_process()

    def _speak(self, text: str):
        if self.state.output_model_options.provider == "deepgram":
            if self.config.api_keys["deepgram"] is None:
                raise ValueError("Deepgram API key not found.")

            if not self._is_installed("ffplay"):
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
            listener_thread = threading.Thread(target=self._start_listener)
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
                                print_text(self.state, text=f"Tap Alt {self.config.keypress_count_stop_listening} times to stop playback.")
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

    def _start_listener(self):
        from pynput import keyboard
        listener = keyboard.Listener(on_press=self.key_press_handler.handle_key_press)
        self.key_press_handler.listener = listener
        listener.start()
        listener.join()

    def _wait_for_audio_process(self):
        if self.audio_process:
            self.audio_process.wait()
        if self.key_press_handler:
            self.key_press_handler.stop_handler()
            if self.key_press_handler.listener:
                self.key_press_handler.listener.stop()
