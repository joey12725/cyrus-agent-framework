import os
import configparser
import random
import uuid
import datetime
from cyrus import Agent, Environment, vprint

class Function:
    pass

class generate(Function):
    def __init__(self, model, prompt):
        self.model = model
        self.prompt = prompt
    def run(self):
        pass

class predict(Function):
    def __init__(self, model, data):
        self.model = model
        self.data = data

class is_called(Function):
    def __init__(self, function):
        self.function = function
        self.env = Environment.getInstance()
    def run(self):
        return bool(self.env.function_status.get(self.function, False))

class returns(Function):
    def __init__(self, function, value):
        self.function = function
        self.value = value
        self.env = Environment.getInstance()
    def run(self):
        if self.value == "*":
            return self.env.function_status.get(self.function) == "completed"
        return self.env.variables.get('value') == self.value and self.env.function_status.get(self.function) == "completed"

class turn(Function):
    def __init__(self, turn):
        self.turn = turn
        self.env = Environment.getInstance()
    def run(self):
        if random.random() < 0.1:
            vprint("thread:", str(self.env.messages["current_thread"]))
        return self.turn == self.env.messages["current_thread"].turn()

class and_(Function):
    def __init__(self, condition1, condition2):
        self.condition1 = condition1
        self.condition2 = condition2
    def run(self):
        return self.condition1 and self.condition2

class or_(Function):
    def __init__(self, condition1, condition2):
        self.condition1 = condition1
        self.condition2 = condition2
    def run(self):
        return self.condition1 or self.condition2

class not_(Function):
    def __init__(self, condition):
        self.condition = condition
    def run(self):
        return not self.condition

class equals(Function):
    def __init__(self, value1, value2):
        self.value1 = value1
        self.value2 = value2
    def run(self):
        return self.value1 == self.value2

class not_equals(Function):
    def __init__(self, value1, value2):
        self.value1 = value1
        self.value2 = value2
    def run(self):
        return self.value1 != self.value2

class greater_than(Function):
    def __init__(self, value1, value2):
        self.value1 = value1
        self.value2 = value2
    def run(self):
        return self.value1 > self.value2

class less_than(Function):
    def __init__(self, value1, value2):
        self.value1 = value1
        self.value2 = value2
    def run(self):
        return self.value1 < self.value2
    
class greater_than_or_equals(Function):
    def __init__(self, value1, value2):
        self.value1 = value1
        self.value2 = value2
    def run(self):
        return self.value1 >= self.value2

class less_than_or_equals(Function):
    def __init__(self, value1, value2):
        self.value1 = value1
        self.value2 = value2
    def run(self):
        return self.value1 <= self.value2

class add(Function):
    def __init__(self, value1, value2):
        self.value1 = value1
        self.value2 = value2
    def run(self):
        return self.value1 + self.value2

class subtract(Function):
    def __init__(self, value1, value2):
        self.value1 = value1
        self.value2 = value2
    def run(self):
        return self.value1 - self.value2

class multiply(Function):
    def __init__(self, value1, value2):
        self.value1 = value1
        self.value2 = value2
    def run(self):
        return self.value1 * self.value2

class divide(Function):
    def __init__(self, value1, value2):
        self.value1 = value1
        self.value2 = value2
    def run(self):
        if self.value2 != 0:  # Avoid division by zero
            return self.value1 / self.value2
        else:
            return 'Error: Division by zero'

class mod(Function):
    def __init__(self, value1, value2):
        self.value1 = value1
        self.value2 = value2
    def run(self):
        return self.value1 % self.value2

class in_(Function):
    def __init__(self, value, list_):
        self.value = value
        self.list = list_
    def run(self):
        return self.value in self.list

class not_in_(Function):
    def __init__(self, value, list_):
        self.value = value
        self.list = list_
    def run(self):
        return self.value not in self.list

class index(Function):
    def __init__(self, dict_, key):
        self.dict = dict_
        self.key = key
    def run(self):
        return self.dict[self.key]