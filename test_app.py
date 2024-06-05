#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
# get rid of deprecation warning stdout.
import warnings ; warnings.warn = lambda *args,**kwargs: None
warnings.filterwarnings("ignore", category=DeprecationWarning)

import asyncio
import unittest
from unittest.mock import patch
from app.app import App


class TestApp(unittest.TestCase):
    def setUp(self):
        self.app = App()

    def test_conversation(self):
        test_cases = [
            (["groq", "llm", "Capital city of France"], ["Paris"]),
        ]

        for questions, expected in test_cases:
            with patch('builtins.input', return_value=' '.join(questions)):
                self.app.process_arguments(questions)
                response = asyncio.run(self.app.answer(questions=questions))
                for expected_output in expected:
                    self.assertIn(expected_output, response)

if __name__ == '__main__':
    unittest.main()
