import os
import configparser
from cyrus import * #, Enviroment
import threading


class State():
    def __init__(self, name, transitions, actions):
        self.name = name
        self.transitions = transitions
        self.actions = actions
        
    def run(self):
        def run_actions():
            for action in self.actions:
                if self.stop_actions:
                    break
                action.run()

        def check_transitions(self):
            while not self.stop_transitions:
                for transition in self.transitions:
                    if transition.check():
                        self.stop_actions = True
                        self.stop_transitions = True
                        self.next_state = transition.next_state
                        return True

        # Start a thread to run actions
        actions_thread = threading.Thread(target=run_actions)
        actions_thread.start()

        # Start another thread to check transitions
        transitions_thread = threading.Thread(target=check_transitions)
        transitions_thread.start()

        # Wait for the actions thread to finish
        actions_thread.join()

        self.stop_transitions = True
 
