#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
# get rid of deprecation warning stdout.
import warnings ; warnings.warn = lambda *args,**kwargs: None
warnings.filterwarnings("ignore", category=DeprecationWarning)
from app.app import App


def main() -> None:
    app: App = App()
    loop, quiet, first_question = app.process_arguments(sys.argv[1:])
    if quiet:
        app.state.is_quiet = quiet

    question: str = first_question + app.stdin_input()
    if loop:
        app.conversation(question=question)
    else:
        app.one_shot(question=question)

    # example of programmatic use
    # app.tool_provider.add_tool(mytool())
    # answer = app.answer(questions=["agent", "code", "refactor following code", "CODE"])
    # app.manager.clear_memory()

if __name__ == "__main__":
    main()
