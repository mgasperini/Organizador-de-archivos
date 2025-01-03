class HistoryManager:
    def __init__(self, path = None):
        self.history = [path] if path else []
        self.history_index = 0

    def update_history(self, path):
        """Actualizar el historial de navegación."""
        print(self.history)
        if self.history_index < len(self.history) - 1:
            self.history = self.history[:self.history_index + 1]

        if not self.history or self.history[-1] != path:
            self.history.append(path)
            self.history_index = len(self.history) - 1

    def get_previous_path(self):
        if self.history_index > 0:
            self.history_index -= 1
            return self.history[self.history_index]
        return None

    def get_next_path(self):
        if self.history_index < len(self.history) - 1:
            self.history_index += 1
            return self.history[self.history_index]
        return None
