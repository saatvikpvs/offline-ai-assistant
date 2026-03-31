class MemoryStore:

    def __init__(self):
        self.memory = []

    def add(self, item):
        self.memory.append(item)

    def get_all(self):
        return self.memory