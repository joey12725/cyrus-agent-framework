from cyrus import Agent, Environment
import os 
import configparser
import threading
import time
import matplotlib.pyplot as plt
import networkx as nx

class cFlow():

    def getInstance(states=[], start_state=None, transitions=[]):
        if cFlow.instance == None:
            cFlow.instance = cFlow(states, start_state, transitions)
        return cFlow.instance

    def __init__(self, states, start_state, transitions):
        self.states = states
        self.start_state = start_state
        self.transitions = transitions
        global env
        env = Environment.getInstance()
        env.flow.current_state = start_state
        #self.env = Environment()
        config = configparser.ConfigParser()
        config.read(os.path.join(os.getcwd(), "config.ini"))

    def run(self):
        def watch_state(self):
            current_state = self.env.flow.current_state
            while True:
                if self.env.flow.current_state != current_state:
                    env.flow.kill_state = True
                    return
                time.sleep(0.1)
        def run_state(self):
            if self.env.flow.current_state:
                self.env.flow.current_state.run()
            time.sleep(1/60)  # Sleep for a short time to reduce CPU usage
            
        watch_thread = threading.Thread(target=self.watch_state)
        run_thread = threading.Thread(target=self.run_state)

        watch_thread.start()
        run_thread.start()

        watch_thread.join()

        if not watch_thread.is_alive():
            run_thread.join() 
    
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
        nodes = [state.name for state in self.states]
        edges = [(transition.source, transition.destination) for transition in self.transitions]

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