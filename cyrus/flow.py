from cyrus import Agent, Environment, vprint
import os 
import configparser
import concurrent.futures
import threading
import time
import matplotlib.pyplot as plt
import networkx as nx
from time import sleep

class cFlow():

    instance = None
    def getInstance(states=[], start_state=None, transitions=[]):
        if cFlow.instance == None:
            cFlow.instance = cFlow(states, start_state, transitions)
        if cFlow.instance.states == [] and states != []:
            cFlow.instance.states = states
            vprint("updated states")
        if cFlow.instance.start_state == None and start_state != None:
            cFlow.instance.start_state = start_state
            env.flow.current_state = start_state
            vprint("updated start_state")
        if cFlow.instance.transitions == [] and transitions != []:
            cFlow.instance.transitions = transitions
            for state in cFlow.instance.states:
                state.update_transitions()
            vprint("updated transitions")
        return cFlow.instance

    def __init__(self, states, start_state, transitions):
        self.states = states
        self.start_state = start_state
        self.transitions = transitions
        global env
        env = Environment.getInstance()
        env.flow.current_state = start_state
        config = configparser.ConfigParser()
        config.read(os.path.join(os.getcwd(), "config.ini"))
        vprint("initialized flow")

    def run_state_actions(self, state):
        vprint(f"Running state actions: {state.name}")
        state.run()

    def check_transitions(self, state):
        vprint(f"Checking transitions for state: {state.name}")
        while not env.flow.kill_state:
            for transition in state.transitions:
                if transition.check():
                    vprint(f"Transitioning from {transition.source.name} to {transition.destination.name} since condition is met")
                    env.flow.kill_state = True
                    env.flow.current_state = transition.destination
                    return
            time.sleep(0.1)

    def run(self):
        env.flow.kill_state = False
        current_state = env.flow.current_state

        with concurrent.futures.ThreadPoolExecutor() as executor:
            while True:
                vprint(f"Starting state: {current_state.name}")
                actions_future = executor.submit(self.run_state_actions, current_state)
                transitions_future = executor.submit(self.check_transitions, current_state)

                while not env.flow.kill_state and not actions_future.done():
                    time.sleep(0.1)
                vprint(f"env.flow.kill_state: {env.flow.kill_state}, actions_future.done(): {actions_future.done()}")
                if env.flow.kill_state:
                    vprint(f"State changed, terminating state: {current_state.name}")
                    sleep(9)
                    env.flow.kill_state = False
                    current_state = env.flow.current_state
                else:
                    vprint(f"State actions completed: {current_state.name}")
                    transitions_future.result()  # Wait for transitions to complete
                    current_state = env.flow.current_state
    
    def terminate(self):
        pass

    def validate_config_file(self):
        path_to_config = os.path.join(os.getcwd(), "config.ini")
        if not os.path.exists(path_to_config):
            raise Exception("Config file not found")
        config = configparser.ConfigParser()
        config.read(path_to_config)
        if "Settings" not in config:
            raise Exception("Settings section not found in config file")
        if "memory_mode" not in config["Settings"]:
            raise Exception("memory_mode not found in config file")
        if "token_limit" not in config["Settings"]:
            raise Exception("token_limit not found in config file")
        if "verbose" not in config["Settings"]:
            raise Exception("verbose not found in config file")
        if "export_env" not in config["Settings"]:
            raise Exception("export_env not found in config file")

    def show(self):
        nodes = [state.name for state in self.states] + ["Start"]
        edges = [(transition.source.name, transition.destination.name) for transition in self.transitions] + [("Start", self.start_state.name)]
        # Create a directed graph
        G = nx.DiGraph()

        # Add nodes to the graph
        G.add_nodes_from(nodes)

        # Add edges to the graph
        G.add_edges_from(edges)

        # Draw the graph
        pos = nx.spring_layout(G)  # positions for all nodes
        nx.draw(G, pos, with_labels=True, node_color='skyblue', node_size=700, edge_color='k', linewidths=1, font_size=15, arrows=True)

        # Show the graph
        plt.show()
