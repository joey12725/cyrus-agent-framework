import os
import configparser
from cyrus import * #, Enviroment

class State():

    def __init__(self, name, transitions, actions):
        self.name = name
        self.transitions = transitions
        self.actions = actions

    def run_actions(self):
        for action in self.actions:
            action.run()
    
    def get_agents(self):
        #get all the agents in actions in the state and sets self.agent[role] = Agent(os.path.join(os.getcwd(), "agents", agent + ".agent"))
        self.agents = {}

    def check_transitions(self):
        pass
    
    def check_if_statements(self):
        pass

    def run_actions(self, action):
        pass