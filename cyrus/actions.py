import os
import sys
import configparser
from cyrus import Agent, State, Environment, cFlow, render_markdown, vprint, Thread
from colorama import Fore, Style
from rich.console import Console
from rich.markdown import Markdown
import importlib.util
import json
import asyncio

class Action:
    def __init__(self):
        global env 
        env = Environment.getInstance()
        global flow
        flow = cFlow.getInstance()
        self.console = Console()
        self.agents = []

class talks_to(Action):
    def __init__(self, agent1, agent2, state=None, context="", load_memory=False, until=False, new_conversation=True):
        super().__init__()
        self.context = context
        self.until = until
        self.state = state
        self.new_conversation = new_conversation
        if agent1 == "user" and agent2 == "user":
            raise Exception("Both agents cannot be user")
        
        if agent1 == "user" or agent2 == "user":
            self.conversation_type = "user"
        elif agent2 == "self": 
            self.conversation_type = "self"
            agent2 = agent1
        else:
            self.conversation_type = "agent"

        if env.config['memory_mode'] == "ephemeral" and new_conversation:
            if self.conversation_type == "user":
                non_user_agent = agent1 if agent1 != "user" else agent2
                user_speaks_first = True if agent1 == "user" else False
                agent = non_user_agent
                self.agent = agent
            else:
                self.agent1 = agent1
                self.agent2 = agent2
        elif env.config['memory_mode'] == "state-persistent" and new_conversation:
            if self.conversation_type == "user":
                non_user_agent = agent1 if agent1 != "user" else agent2
                user_speaks_first = True if agent1 == "user" else False
                agent = non_user_agent
                self.agent = agent
            else:
                self.agent1 = agent1
                self.agent2 = agent2
        elif env.config['memory_mode'] == "agent-persistent" and new_conversation:
            if self.conversation_type == "user":
                non_user_agent = agent1 if agent1 != "user" else agent2
                user_speaks_first = True if agent1 == "user" else False
                agent = non_user_agent
                self.agent = agent
            else:
                self.agent1 = agent1
                self.agent2 = agent2

    async def run(self):
        if env.config['memory_mode'] in ["ephemeral", "state-persistent", "agent-persistent"] and self.new_conversation:
            if self.conversation_type == "user":
                await self.load_thread(self.agent, Thread())
            else:
                await self.load_thread(self.agent1, Thread())
                await self.load_thread(self.agent2, Thread())
                
        if self.conversation_type == "user":
            await self.step_conversation_user(self.agent)
        else:
            await self.step_conversation_agent(self.agent1, self.agent2, context=self.context)

    async def load_thread(self, agent, thread):
        await agent.load_thread(thread)

    async def step_conversation_user(self, agent, context="", user_speaks_first=True):
        if env.flow['kill_state']:
            return

        if 'step' not in env.messages:
            env.messages['step'] = 0

        if not user_speaks_first:
            if context != "":
                response = await agent.get_response("Initiate a conversation with context:" + str(context))
                render_markdown(f"**{agent.name}:**\n" + response)
            else:
                response = await agent.get_response("Initiate a conversation")
                render_markdown(f"**{agent.name}:**\n" + response)

        prompt_user = "**User:**"
        render_markdown(prompt_user)
        if env.messages['step'] == 0 and context != "" and user_speaks_first:
            user_input = "CONTEXT: " + str(context) + "\n USER: " + input()
        else:
            user_input = input()
        if user_speaks_first:
            member1 = "user"
            member2 = agent.name
        else:
            member1 = agent.name
            member2 = "user"
        env.increment_step(sender=member1, recipient=member2, message=user_input, new_conversation=self.new_conversation)
        self.new_conversation = False
        user_input = str(user_input)
        response = await agent.get_response(user_input)
        render_markdown(f"**{agent.name}:**\n" + response)
        env.increment_step(sender=member2, recipient=member1, message=user_input, new_conversation=self.new_conversation)
        if not self.until:
            return await self.step_conversation_user(agent)
        else:
            return
    
    async def step_conversation_agent(self, agent1, agent2, context=""):
        if env.flow['kill_state']:
            return
        is_thread = isinstance(env.messages['current_thread'], Thread)
        correct_members = agent1.name in env.messages['current_thread'].members and agent2.name in env.messages['current_thread'].members
        no_members = env.messages['current_thread'].members == []
        if not is_thread or (not correct_members and not no_members):
            env.messages['current_thread'] = Thread()
            vprint("creating new thread")
        self.thread = env.messages['current_thread']
        if self.thread.turn() == 0 or self.new_conversation:
            if context != "":
                response = await agent1.get_response("Initiate a conversation with context:" + str(context))
            else:
                response = await agent1.get_response("Initiate a conversation")
        else:
            response = self.thread.messages[-1].content
            response = await agent1.get_response(response)

        env.increment_step(sender=agent2.name, recipient=agent1.name, message=response, new_conversation=self.new_conversation, state=self.state)
        self.new_conversation = False
        vprint(f"**{agent1.name}:**\n" + response)
        response = await agent2.get_response(response)
        env.increment_step(sender=agent1.name, recipient=agent2.name, message=response, state=self.state)
        vprint(f"**{agent2.name}:**\n" + response)

        if not self.until and not env.flow['kill_state']:
            return await self.step_conversation_agent(agent1, agent2)
        else:
            return
        
    def __str__(self):
        if self.conversation_type == "user":
            return f"{self.agent.name} talks to the user"
        if self.conversation_type == "agent":
            return f"{self.agent1.name} talks to {self.agent2.name}"
        if self.conversation_type == "self":
            return f"{self.agent1.name} talks to itself"

class reflect(Action):
    def __init__(self, agent, context=""):
        self.agent = agent
        self.context = context
    
    async def run(self, context=""):
        if not context:
            await self.agent.reflect()
        else:
            await self.agent.reflect(context=context)
        return

class call(Action):
    def __init__(self, function_name, args_dict):
        super().__init__()
        self.function_name = function_name
        self.args_dict = args_dict

    def __str__(self):
        return f"Call function {self.function_name} with args {json.dumps(self.args_dict)}"

    async def run(self):
        cwd = os.getcwd()
        function_path = os.path.join(cwd, 'functions', f'{self.function_name}.py')

        if not os.path.exists(function_path):
            raise FileNotFoundError(f"Function {self.function_name} does not exist.")

        spec = importlib.util.spec_from_file_location(self.function_name, function_path)
        function_module = importlib.util.module_from_spec(spec)
        try:
            spec.loader.exec_module(function_module)
        except Exception as e:
            raise ImportError(f"Failed to load module {self.function_name}.py. Error: {str(e)}")

        try:
            function = getattr(function_module, self.function_name)
        except AttributeError:
            raise AttributeError(f"Function {self.function_name} not found in {self.function_name}.py.")
        try:
            return await function(**self.args_dict)
        except Exception as e:
            raise RuntimeError(f"Failed to run function {self.function_name}. Error: {str(e)}")

class let(Action):
    def __init__(self, variable, value):
        super().__init__()
        self.variable = variable
        self.value = value

    async def run(self):
        keys = self.variable.split(".")
        current_dict = env.variables
        for key in keys[:-1]:
            if key not in current_dict:
                current_dict[key] = {}
            current_dict = current_dict[key]
        current_dict[keys[-1]] = self.value

    def __str__(self):
        return f"Set {self.variable} to {self.value}"
    
class println(Action):
    def __init__(self, message):
        self.message = message

    def __str__(self):
        return f"Prints {self.message}"
    
    async def run(self):
        print(str(self.message))

class loop(Action):
    def __init__(self, lst, iterator, actions):
        self.lst = lst
        self.iterator = iterator
        self.actions = actions

    async def run(self):
        for item in self.lst:
            if env.flow['kill_state']:
                return
            env.variables[self.iterator] = item
            for action in self.actions:
                await action.run()

    def __str__(self):
        return f"Loop through {self.lst} with {self.iterator} and do {[str(action) for action in self.actions]}"

class go_to(Action):
    def __init__(self, state, context=""):
        super().__init__()
        self.state = state
        self.context = context
        env.messages['use_context'] = False

    async def run(self):
        env.flow['current_state'] = self.state
        if self.context:
            env.messages['use_context'] = True
            env.messages['context'] = self.context
        return

    def __str__(self):
        return f"Go to {self.state}"
              
class terminate(Action):
    def __init__(self):
        env = Environment.getInstance()

    async def run(self):
        sys.exit()
