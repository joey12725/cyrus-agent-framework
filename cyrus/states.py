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
        for action in self.actions:
            if type(action) in [reflect, talks_to]:
                self.agents[action.role] = action

    def check_transitions(self): #note: this implementation means that transitions are ordered by priority such that the first transition that is true is the one that is run
        for transition in self.transitions:
            if transition.check():
                transition.run()
                break
                return True
        return False
    
    def check_if_statements(self):
        pass

    def run_actions(self, action):
        pass