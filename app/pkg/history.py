class ConversationHistory:
    def __init__(self):
        self.history = []

    def add_message(self, message):
        self.history.append(message)

    def get_history(self):
        return self.history

    def clear_history(self):
        self.history = []

    def size(self):
        return len(self.history)

    def __str__(self):
        return "\n".join(self.history)