#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
# get rid of deprecation warning stdout.
import warnings ; warnings.warn = lambda *args,**kwargs: None
from app.app import App

warnings.warn = lambda *args, **kwargs: None

if __name__ == "__main__":
    app: App = App()
    app.load_config_and_state()
    app.load_options()
    app.load_state_change_parser()

    loop: bool = app.process_arguments(sys.argv[1:])[0]
    quiet: bool = app.process_arguments(sys.argv[1:])[1]
    first_question: str = app.process_arguments(sys.argv[1:])[2]
    stdin_input: str = app.stdin_input()

    if quiet:
        app.state.is_quiet = quiet

    app.load_manager()
    app.manager.reload_agent()

    app.start(loop=loop, question=first_question + stdin_input)
