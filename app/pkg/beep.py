import numpy as np
import simpleaudio as sa


class BeepGenerator:
    def __init__(self):
        self.frequency: int = 130
        self.sample_rate: int = 44100

    def generate_beep(self) -> np.ndarray:
        time: np.ndarray = np.linspace(0, 0.1, int(self.sample_rate * 0.1), False)
        sine_wave: np.ndarray = np.sin(self.frequency * time * 2 * np.pi)
        normalized_audio: np.ndarray = sine_wave * (2**15 - 1) / np.max(np.abs(sine_wave))
        normalized_audio: np.ndarray = normalized_audio.astype(np.int16)

        return normalized_audio

    def play_beep(self) -> None:
        audio: np.ndarray = self.generate_beep()
        sa.play_buffer(audio, 1, 2, self.sample_rate)
