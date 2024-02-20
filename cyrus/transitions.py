class Transition():
    def __init__(self, source, destination, condition):
        self.source = source
        self.destination = destination
        self.condition = condition
    def __str__(self):
        return f"Transition from {self.source} to {self.destination} with condition {self.condition}"
    def check_condition(self):
        return self.condition