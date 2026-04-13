class FakeCollection:
    def __init__(self):
        self.data = []

    def insert_one(self, doc):
        self.data.append(doc)

    def delete_many(self, _filter):
        self.data = []

    def find(self):
        return self.data
