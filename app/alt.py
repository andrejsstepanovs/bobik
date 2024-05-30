import threading
import time
from pynput.keyboard import Listener, Key
from .my_print import print_text
from .state import ApplicationState


class AltKeyDoublePressDetector:
    def __init__(
            self,
            state: ApplicationState,
            threading_type,  # threading.Lock() or threading.Event()
            keypress_count: int = 3,
            timeout_duration: float = 0.5,
            audio_process=None,
    ):
        self.state = state
        self.keypress_count = keypress_count
        self.timeout_duration = timeout_duration
        self.last_press_time = 0.0
        self.consecutive_presses = 0
        self.threading = threading_type
        self.listener = None
        self.audio_process = audio_process

    def handle_key_press(self, key: Key):
        if key in {Key.alt_l, Key.alt_r}:
            if type(self.threading) == threading.Lock:
                with self.threading:
                    self._process_keypress()
            else:
                self._process_keypress()
        else:
            self.consecutive_presses = 0

    def _process_keypress(self):
        current_time = time.time()
        if current_time - self.last_press_time < self.timeout_duration:
            self.consecutive_presses += 1
            if self.consecutive_presses == self.keypress_count:
                print_text(state=self.state, text="Consecutive Alt presses detected.")
                self.stop_handler()
        else:
            self.consecutive_presses = 1
        self.last_press_time = current_time

    def stop_handler(self):
        if self.audio_process:
            self.audio_process.terminate()
        if self.listener:
            self.listener.stop()

    def start_key_listener(self):
        if isinstance(self.threading, threading.Event):
            self.threading.set()

        self.listener = Listener(on_press=self.handle_key_press)
        self.listener.start()
        self.listener.join()
