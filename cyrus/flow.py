from cyrus import Agent, Environment, vprint
import os
import configparser
import concurrent.futures
import threading
import time
import matplotlib.pyplot as plt
import networkx as nx
import asyncio

class cFlow:
    instance = None

    @staticmethod
    def getInstance(states=[], start_state=None, transitions=[]):
        if cFlow.instance is None:
            cFlow.instance = cFlow(states, start_state, transitions)
        if not cFlow.instance.states and states:
            cFlow.instance.states = states
            vprint("updated states")
        if not cFlow.instance.start_state and start_state:
            cFlow.instance.start_state = start_state
            env.flow['current_state'] = start_state
            vprint("updated start_state")
        if not cFlow.instance.transitions and transitions:
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
        env.flow['current_state'] = start_state
        config = configparser.ConfigParser()
        config.read(os.path.join(os.getcwd(), "config.ini"))
        vprint("initialized flow")

    async def run_state_actions(self, state):
        vprint(f"Running state actions: {state.name}")
        await state.run()

    async def check_transitions(self, state):
        vprint(f"Checking transitions for state: {state.name}")
        while not env.flow['kill_state']:
            for transition in state.transitions:
                if await transition.check():
                    vprint(f"Transitioning from {transition.source.name} to {transition.destination.name} since condition is met")
                    env.flow['kill_state'] = True
                    env.flow['current_state'] = transition.destination
                    return
            await asyncio.sleep(0.1)

    async def run(self):
        env.flow['kill_state'] = False
        current_state = env.flow['current_state']

        while True:
            vprint(f"Starting state: {current_state.name}")
            actions_task = asyncio.create_task(self.run_state_actions(current_state))
            transitions_task = asyncio.create_task(self.check_transitions(current_state))

            done, pending = await asyncio.wait(
                [actions_task, transitions_task],
                return_when=asyncio.FIRST_COMPLETED,
            )

            if actions_task in done:
                vprint(f"State actions completed: {current_state.name}")
            if transitions_task in done:
                vprint(f"State changed, terminating state: {current_state.name}")
                env.flow['kill_state'] = False
                current_state = env.flow['current_state']

    def terminate(self):
        pass

    def validate_config_file(self):
        path_to_config = os.path.join(os.getcwd(), "config.ini")
        if not os.path.exists(path_to_config):
            raise Exception("Config file not found")
        config = configparser.ConfigParser()
        config.read(path_to_config)
        required_settings = ["memory_mode", "token_limit", "verbose", "export_env"]
        for setting in required_settings:
            if setting not in config["Settings"]:
                raise Exception(f"{setting} not found in config file")

    def show(self):
        nodes = [state.name for state in self.states] + ["Start"]
        edges = [(transition.source.name, transition.destination.name) for transition in self.transitions] + [("Start", self.start_state.name)]
        
        G = nx.DiGraph()
        G.add_nodes_from(nodes)
        G.add_edges_from(edges)

        pos = nx.spring_layout(G)
        nx.draw(G, pos, with_labels=True, node_color='skyblue', node_size=700, edge_color='k', linewidths=1, font_size=15, arrows=True)

        plt.show()
