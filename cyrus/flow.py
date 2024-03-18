from cyrus import Agent, Environment, vprint
import os 
import configparser
import threading
import time
import matplotlib.pyplot as plt
import networkx as nx

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

    def watch_state(self):
        current_state = env.flow.current_state
        while True:
            if env.flow.current_state != current_state:
                env.flow.kill_state = True
                vprint(f"state changed to {env.flow.current_state.name}, killing current state")
                return
            time.sleep(0.1)

    def run_state(self):
        env.flow.kill_state = False
        current_state = env.flow.current_state
        current_state.run()
        vprint("state finished running with no transitions met, killing current state")
        env.flow.kill_state = True
        return


    def run(self):
        #with the current state, run the state and watch for a change in state
        #if the state changes, kill the current state and run the new current state
        #if the state does not change, kill the current state and return
        env.flow.kill_state = False
        current_state = env.flow.current_state
        state_thread = threading.Thread(target=self.run_state)
        watch_thread = threading.Thread(target=self.watch_state)
        state_thread.start()
        watch_thread.start()
        state_thread.join()
        watch_thread.join()
        if env.flow.kill_state:
            env.flow.current_state = env.flow.current_state.next_state
            env.flow.halt_state = False
            self.run()
        
    
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