from .state import ApplicationState


def print_text(state: ApplicationState, text: str, separator: str = ' ', end_character: str = '\n'):
    if not state.is_quiet:
        print(text, sep=separator, end=end_character)
