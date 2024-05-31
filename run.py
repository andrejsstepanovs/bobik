#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
# get rid of deprecation warning stdout.
import warnings ; warnings.warn = lambda *args,**kwargs: None
warnings.filterwarnings("ignore", category=DeprecationWarning)
from app.app import App


def main() -> None:
    app: App = App()

    input_question = sys.argv[1:]
    app.process_arguments(input_question)

    question: str = " ".join(input_question) + app.stdin_input()
    app.conversation(questions=[question])

    # example of programmatic use
    # app.tool_provider.add_tool(mytool())
    # answer = app.answer(questions=["agent", "code", "refactor following code", "CODE"])
    # app.manager.clear_memory()

if __name__ == "__main__":
    main()
