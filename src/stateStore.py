class StateStore:
    def __init__(self):
        self.store = {}

    def read(self, key):
        state = self.store.get(key)
        if state is None:
            raise ValueError("Not found.")
        return state

    def save(self, key, state):
        self.store[key] = state
