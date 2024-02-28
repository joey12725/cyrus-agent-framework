import configparser
import os
from types import SimpleNamespace

class DynamicAttrDict:
    def __getattr__(self, name):
        if name not in self.__dict__:
            self.__dict__[name] = DynamicAttrDict()
        return self.__dict__[name]

    def __setattr__(self, name, value):
        self.__dict__[name] = value

    def __delattr__(self, name):
        if name in self.__dict__:
            del self.__dict__[name]

    def __contains__(self, name):
        return name in self.__dict__

    def __iter__(self):
        return iter(self.__dict__)

    def __bool__(self):
        return bool(self.__dict__)
    
    def __str__(self, indent=0):
        result = []
        for key, value in self.__dict__.items():
            if isinstance(value, DynamicAttrDict):
                result.append('  ' * indent + str(key))
                result.append(value.__str__(indent + 1))
            else:
                result.append('  ' * indent + f'{key}: {value}')
        return '\n'.join(result)
    
    def show(self, indent=1):
        for key, value in self.__dict__.items():
            if isinstance(value, DynamicAttrDict):
                print('  ' * indent + str(key))
                value.show(indent + 1)
            else:
                print('  ' * indent + f'{key}: {value}')

    def set_value(self, name, value):
        self.__dict__[name] = value

    def get_index(self, name):
        if name not in self.__dict__:
            self.__dict__[name] = DynamicAttrDict()
        return self.__dict__[name]

class Environment:

    _instance = None

    @staticmethod
    def getInstance():
        if Environment._instance == None:
            Environment()
        return Environment._instance

    def __init__(self):
        if Environment._instance != None:
            raise Exception("This class is a singleton!")
        else:
            Environment._instance = self
        self.variables = DynamicAttrDict()
        self.function_status = DynamicAttrDict()
        self.flow = DynamicAttrDict()
        self.messages = DynamicAttrDict()
        self.functions = []
        self.messages.step = 0
        if os.path.exists(os.path.join(os.getcwd(), "config.ini")):
            self.configfile = configparser.ConfigParser()
            self.configfile.read(os.path.join(os.getcwd(), "config.ini"))
            self.config = DynamicAttrDict()
            self.config.memory_mode = self.configfile["Settings"]["memory_mode"].replace("\"","")
            self.config.verbose = True if self.configfile["Settings"]["verbose"].replace("\"","") == "true" or self.config["Settings"]["verbose"].replace("\"","") == "True" else False
            self.export_env = True if self.configfile["Settings"]["export_env"].replace("\"","") == "true" or self.config["Settings"]["export_env"].replace("\"","") == "True" else False
            self.config.token_limit = int(self.configfile["Settings"]["token_limit"].replace("\"",""))
        else:
            raise(Exception("config.ini not found"))

    def clear(self):
        # Explicitly clear or reset all managed attributes
        self.variables = DynamicAttrDict()
        self.function_status = DynamicAttrDict()
        self.messages = DynamicAttrDict()
        #if self.functions exists
        if hasattr(self, 'functions'):
            for function in self.functions:
                self.function_status.set_value(function, False)
        
        # Re-read configuration if necessary
        if os.path.exists(os.path.join(os.getcwd(), "config.ini")):
            self.configfile.read(os.path.join(os.getcwd(), "config.ini"))
            self.config.memory_mode = self.configfile["Settings"]["memory_mode"].replace("\"","")
            self.config.verbose = True if self.configfile["Settings"]["verbose"].replace("\"","") == "true" or self.config["Settings"]["verbose"].replace("\"","") == "True" else False
            self.export_env = True if self.configfile["Settings"]["export_env"].replace("\"","") == "true" or self.config["Settings"]["export_env"].replace("\"","") == "True" else False
            self.config.token_limit = int(self.configfile["Settings"]["token_limit"].replace("\"",""))
        else:
            print("config.ini not found, unable to re-read configuration.")


        # Clear any user-added attributes by iterating over __dict__
        # Be cautious to not remove essential attributes
        essential_attrs = {'_instance', 'variables', 'function_status', 'messages', 'functions', 'configfile', 'config'}
        user_attrs = [attr for attr in self.__dict__ if attr not in essential_attrs]
        for attr in user_attrs:
            delattr(self, attr)

        # Reset step count if it's specifically managed
        if hasattr(self, 'messages') and hasattr(self.messages, 'step'):
            self.messages.step = 0

        # Ensure _instance is updated to reflect the reset state
        Environment._instance = self



    def __str__(self):
        print(self.name, self.value)

    def increment_step(self):
        self.messages.step += 1
        self.value = False
        for function in self.function_status:
            if self.function_status.get_index(function) != "in progress":
                self.function_status.set_value(function, False)
    