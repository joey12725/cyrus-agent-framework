from cyrus import Agent, Environment, vprint
import os
import configparser
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
        while not env.flow['kill_state']:
            for transition in state.transitions:
                if await transition.check():
                    vprint(f"Transitioning from {transition.source.name} to {transition.destination.name} since condition is met")
                    env.flow['kill_state'] = True
                    env.flow['current_state'] = transition.destination
                    return True
                else:
                    vprint(f"Transition condition not met for {transition.source.name} to {transition.destination.name}")
            await asyncio.sleep(0.1)
        return False

    async def run(self):
        env.flow['kill_state'] = False
        current_state = env.flow['current_state']

        while True:
            vprint(f"Starting state: {current_state.name}")
            env.flow['kill_state'] = False
            actions_task = asyncio.create_task(self.run_state_actions(current_state))
            transitions_task = asyncio.create_task(self.check_transitions(current_state))

            done, pending = await asyncio.wait(
                [actions_task, transitions_task],
                return_when=asyncio.FIRST_COMPLETED,
            )

            if transitions_task in done:
                if transitions_task.result():
                    vprint(f"State changed, terminating state: {current_state.name}")
                    env.flow['kill_state'] = True
                    current_state = env.flow['current_state']
                    for task in pending:
                        task.cancel()
                    continue
            elif env.flow['kill_state']:
                    vprint(f"State actions terminated, transitioning using alternate method")
                    current_state = env.flow['current_state']
                    continue

            if actions_task in done:
                if current_state == env.flow['current_state']:
                    vprint(f"State actions completed for {current_state.name}")
                    for task in pending:
                        task.cancel()
                    break
                else:
                    vprint(f"State changed, terminating state: {current_state.name}")
                    env.flow['kill_state'] = True
                    current_state = env.flow['current_state']
                    for task in pending:
                        task.cancel()
                    continue

            # Check transitions after state actions complete
            if not transitions_task.result():
                vprint("Checking transitions after state actions completed")
                if await self.check_transitions(current_state):
                    vprint(f"Transitioning after state actions completed from {current_state.name} to {env.flow['current_state'].name}")
                    current_state = env.flow['current_state']
                    continue

            break
