from app.state import ApplicationState


def print_text(state: ApplicationState, text: str, separator=' ', end_character='\n'):
    if not state.is_quiet:
        print(text, sep=separator, end=end_character)
