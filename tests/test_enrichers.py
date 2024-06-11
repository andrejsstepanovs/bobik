import unittest
import os
from typing import List
from src.state import ApplicationState
from src.enrichers import check_text_for_phrases
from src.config import Configuration
from src.settings import Settings
from src.app import App


class TestCheckTextForPhrases(unittest.TestCase):
    def setUp(self):
        current_dir = os.getcwd()
        script_dir = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(script_dir, '..', 'docs', 'examples', '1_minimal_groq', 'my_config.yaml')

        settings: Settings = App().load_settings(file_path)
        config: Configuration = Configuration(settings)

        self.state = ApplicationState(config)
        self.state.is_quiet = False

    def test_phrase_detected(self):
        cases = [
            {"question": "aaa bbb ccc", "phrases": ["ddd"], "contains": True, "expected": False},
            {"question": "aaa bbb ccc", "phrases": ["bbb"], "contains": True, "expected": True},
            {"question": "aaa bbb ccc", "phrases": ["aaa"], "contains": True, "expected": True},
            {"question": "aaa bbb ccc", "phrases": ["ccc"], "contains": True, "expected": True},
            {"question": "aaa bbb ccc", "phrases": ["ccc"], "contains": False, "expected": False},
            {"question": "aaa bbb ccc", "phrases": ["bbb"], "contains": False, "expected": False},
            {"question": "aaa bbb ccc", "phrases": ["aaa"], "contains": False, "expected": True},
            {"question": "aaa bbb ccc", "phrases": ["ddd"], "contains": False, "expected": False},
        ]
        for case in cases:
            phrase_found, found = check_text_for_phrases(state=self.state, question=case["question"], phrases=case["phrases"], contains=case["contains"])
            self.assertEqual(found, case["expected"])


if __name__ == '__main__':
    unittest.main()
