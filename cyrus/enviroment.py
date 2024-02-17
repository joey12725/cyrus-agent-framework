class environment():
    def __init__(self, name, value):
        self.name = name
        self.value = value
        self.step = 0

    def __str__(self):
        print(self.name, self.value)