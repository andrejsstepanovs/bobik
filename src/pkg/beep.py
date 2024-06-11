import numpy as np
import simpleaudio as sa


class BeepGenerator:
    def __init__(self, frequency: int = 130, sample_rate: int = 44100, channels: int = 2):
        self.frequency: int = frequency
        self.sample_rate: int = sample_rate
        self.channels: int = channels

    def generate_beep(self) -> np.ndarray:
        time = np.linspace(0, 0.1, int(self.sample_rate * 0.1), False)
        sine_wave = np.sin(self.frequency * time * 2 * np.pi)
        normalized_audio = (sine_wave * (2**15 - 1) / np.max(np.abs(sine_wave))).astype(np.int16)

        return normalized_audio

    def play_beep(self) -> None:
        sa.play_buffer(self.generate_beep(), self.channels, 2, self.sample_rate)
