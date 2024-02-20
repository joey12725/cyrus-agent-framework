import os
import configparser
from cyrus import Agent, Enviroment
class Function(): 
        class generate():
            def __init__(self, model, prompt):
                self.model = model
                self.prompt = prompt
        class predict():
            def __init__(self, model, data):
                self.model = model
                self.data = data
        class is_called():
            def __init__(self, function):
                self.function = function
        class returns():
            def __init__(self, function, value):
                self.function = function
                self.value = value
        class turn():
            def __init__(self, turn):
                self.turn = turn
        class and_():
            def __init__(self, condition, condition):
                self.condition = condition
        class or_():
            def __init__(self, condition, condition):
                self.condition = condition
        class not_():
            def __init__(self, condition):
                self.condition = condition
        class equals():
            def __init__(self, value, value):
                self.value = value
        class not_equals():
            def __init__(self, value, value):
                self.value = value
        class greater_than():
            def __init__(self, value, value):
                self.value = value
        class less_than():
            def __init__(self, value, value):
                self.value = value
        class greater_than_or_equals():
            def __init__(self, value, value):
                self.value = value
        class less_than_or_equals():
            def __init__(self, value, value):
                self.value = value
        class add():
            def __init__(self, value, value):
                self.value = value
        class subtract():
            def __init__(self, value, value):
                self.value = value
        class multiply():
            def __init__(self, value, value):
                self.value = value
        class divide():
            def __init__(self, value, value):
                self.value = value
        class mod():
            def __init__(self, value, value):
                self.value = value
        class in_():
            def __init__(self, value, list):
                self.value = value
                self.list = list
        class not_in_():
            def __init__(self, value, list):
                self.value = value
                self.list = list
        class index():
            def __init__(self, dict, key):
                self.dict = dict
                self.key = key