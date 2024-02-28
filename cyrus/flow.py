from cyrus import Agent #, Enviroment
import os 
import configparser
class cFlow():

    def getInstance():
        if cFlow.instance == None:
            cFlow.instance = cFlow()
        return cFlow.instance

    def __init__(self, states, start_state):
        self.states = states
        self.start_state = start_state
        self.current_state = start_state
        #self.env = Environment()
        config = configparser.ConfigParser()
        config.read(os.path.join(os.getcwd(), "config.ini"))

    def run(self):
        pass

    def run_transition(self, transition):
        pass
    
    def terminate(self):
        pass

    def validate_config_file(self, config_file):
        pass

    def show():
        pass