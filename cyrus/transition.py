from cyrus import Environment

class Transition():
    def __init__(self, source, destination, condition):
        self.source = source
        self.destination = destination
        self.condition = condition
        global env
        env = Environment.getInstance()

    def __str__(self):
        return f"Transition from {self.source} to {self.destination} with condition {self.condition}"
    def check(self):
        #if it is callable
        if callable(self.condition):
            return self.condition()
        else:
            return bool(self.condition)
    def run(self):
        env.flow.current_state = self.destination