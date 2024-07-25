#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
# get rid of deprecation warning stdout.
import warnings ; warnings.warn = lambda *args,**kwargs: None
warnings.filterwarnings("ignore", category=DeprecationWarning)
from src.app import App

# if bobik installed as submodule
# sys.path.append("bobik")
# from bobik.src.app import App


def main() -> None:
    app: App = App()

    input_question = sys.argv[1:]

    question: str = " ".join(input_question) + app.stdin_input()
    app.conversation(questions=[question])

    # example of programmatic use
    # app.tool_provider.add_tool(mytool())
    # answer: str = app.answer(questions=["llm gpt4o", "refactor following code file /full/path/to/file.py"])
    # app.get_manager().clear_memory()

if __name__ == "__main__":
    main()

