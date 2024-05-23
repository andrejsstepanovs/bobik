#!/usr/bin/env python
# -*- coding: utf-8 -*-

# get rid of deprecation warning stdout.
import warnings ; warnings.warn = lambda *args,**kwargs: None
from app.app import App


if __name__ == "__main__":
    app = App()
    app.load_config_and_state()
    app.load_options()
    app.load_state_change_parser()

    loop, quiet, first_question = app.process_arguments()
    stdin_input = app.stdin_input()

    if quiet:
        app.state.is_quiet = quiet

    app.load_manager()
    if not loop:
        app.manager.reload_agent()

    app.start(loop, first_question + stdin_input)
