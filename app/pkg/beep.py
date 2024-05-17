import numpy as np
import simpleaudio as sa


class BeepGenerator:
    def __init__(self):
        self.frequency = 130  
        self.sample_rate = 44100

    def generate_beep(self):
        time = np.linspace(0, 0.1, int(self.sample_rate * 0.1), False)
        sine_wave = np.sin(self.frequency * time * 2 * np.pi)
        normalized_audio = sine_wave * (2**15 - 1) / np.max(np.abs(sine_wave))
        normalized_audio = normalized_audio.astype(np.int16)

        return normalized_audio

    def play_beep(self):
        audio = self.generate_beep()
        sa.play_buffer(audio, 1, 2, self.sample_rate)
