import threading
import time
from pynput import keyboard
from app.my_print import print_text
from app.state import ApplicationState


class AltKeyDoublePressDetector:
    def __init__(self, app_state: ApplicationState, timeout_duration=0.5):  # 0.5 seconds timeout
        self.app_state = app_state
        self.timeout_duration = timeout_duration
        self.last_press_time = 0
        self.thread_lock = threading.Lock()
        self.key_listener = None

    def handle_key_press(self, key):
        if key == keyboard.Key.alt_l or key == keyboard.Key.alt_r:
            with self.thread_lock:
                current_time = time.time()
                if current_time - self.last_press_time < self.timeout_duration:
                    print_text(state=self.app_state, text="Consecutive Alt presses detected! Stopping listener.")
                    self.key_listener.stop()
                self.last_press_time = current_time

    def start_key_listener(self):
        self.key_listener = keyboard.Listener(on_press=self.handle_key_press)
        self.key_listener.start()
        self.key_listener.join()
