from cyrus import Environment, vprint
import asyncio

class Transition:
    def __init__(self, source, destination, condition, label=None):
        self.source = source
        self.destination = destination
        self.condition = condition
        if label:
            self.label = label
        else:
            self.label = ""
        global env
        env = Environment.getInstance()

    def __str__(self):
        return f"Transition from {self.source} to {self.destination} with condition {self.condition}"
    
    async def check(self):
        vprint(f"Checking transition from {self.source.name} to {self.destination.name}")
        if callable(self.condition):
            result = self.condition()
            if asyncio.iscoroutine(result):
                return await result
            else:
                return result
        elif hasattr(self.condition, "run"):
            result = self.condition.run()
            if asyncio.iscoroutine(result):
                return await result
            else:
                return result
        else:
            return self.condition

    def run(self):
        env.flow["current_state"] = self.destination
