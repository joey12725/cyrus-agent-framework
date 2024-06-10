from cyrus import Environment, vprint
import asyncio

class Transition:
    def __init__(self, source, destination, condition):
        self.source = source
        self.destination = destination
        self.condition = condition
        global env
        env = Environment.getInstance()

    def __str__(self):
        return f"Transition from {self.source} to {self.destination} with condition {self.condition}"
    
    async def check(self):
        if callable(self.condition):
            result = self.condition()
            if asyncio.iscoroutine(result):
                return await result
            else:
                return result
        elif hasattr(self.condition, "run"):
            return await self.condition.run()
        else:
            return bool(self.condition)

    def run(self):
        env.flow["current_state"] = self.destination
