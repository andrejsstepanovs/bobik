import numpy as np
from ..beep import BeepGenerator


def test_initialization():
    # Test default values
    beeper = BeepGenerator()
    assert beeper.frequency == 130
    assert beeper.sample_rate == 44100

    # Test custom values
    beeper = BeepGenerator(500, 88200)
    assert beeper.frequency == 500
    assert beeper.sample_rate == 88200

def test_generate_beep():
    beeper = BeepGenerator()
    beep = beeper.generate_beep()

    # Test if output is a numpy array of int16 values
    assert isinstance(beep, np.ndarray)
    assert beep.dtype == np.int16

    # Test length of the beep based on sample rate and time (0.1 seconds)
    assert len(beep) == 4410