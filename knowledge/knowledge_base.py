class KnowledgeBase:

    def __init__(self):
        self.data = {
            "gravity": "Gravity is a force that attracts objects with mass.",
            "fever": "Fever is a temporary rise in body temperature."
        }

    def search(self, keyword):

        for key in self.data:
            if key in keyword:
                return self.data[key]

        return None