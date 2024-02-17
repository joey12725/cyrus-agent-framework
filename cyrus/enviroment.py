class environment():
    def __init__(self, name, value):
        self.name = name
        self.value = value

    def __str__(self):
        print(self.name, self.value)