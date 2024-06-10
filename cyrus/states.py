import os
import configparser
from cyrus import *  # , Enviroment
import threading
from time import sleep

class State:
    def __init__(self, name, actions):
        self.name = name
        self.actions = actions
        global env
        env = Environment.getInstance()
        env.flow["kill_state"] = False
        global flow
        flow = cFlow.getInstance()
        self.transitions = [transition for transition in flow.transitions if transition.source == self]
    
    def update_transitions(self):
        self.transitions = [transition for transition in flow.transitions if transition.source == self]

    async def run(self):
        vprint(f"self.actions: {self.actions}")
        for action in self.actions:
            vprint(f"Running action: {str(action)}")
            await action.run()
        return True
