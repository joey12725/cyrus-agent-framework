import os
import configparser
from cyrus import * #, Enviroment
import threading


class State():
    def __init__(self, name, actions):
        self.name = name
        self.actions = actions
        global env
        env = Environment.getInstance()
        env.flow.kill_state = False
        global flow
        flow = cFlow.getInstance()
        self.transitions = [transition for transition in flow.transitions if transition.source == self]
    
    def update_transitions(self):
        self.transitions = [transition for transition in flow.transitions if transition.source == self]

    def run_actions(self):
            for action in self.actions:
                if env.flow.kill_state:
                    break
                action.run()

    def check_transitions(self):
        vprint(f"Checking transitions for state {self.name}")
        while not env.flow.kill_state:
            for transition in self.transitions:
                vprint(f"Checking transition from {transition.source.name} to {transition.destination.name}")
                if transition.check():
                    env.flow.kill_state = True
                    env.flow.kill_state = True
                    env.flow.halt_state = True
                    self.next_state = transition.destination
                    return True
                    
    def run(self):

        # Start a thread to run actions
        actions_thread = threading.Thread(target=self.run_actions)
        actions_thread.start()

        # Start another thread to check transitions
        transitions_thread = threading.Thread(target=self.check_transitions)
        transitions_thread.start()

        # Wait for the actions thread to finish
        actions_thread.join()

        env.flow.kill_state = True
 
