import os
import sys
import configparser
from cyrus import Agent, State, Environment
from colorama import Fore, Style
from rich.console import Console
from rich.markdown import Markdown
import importlib.util
import json

class Action(State):
    def __init__(self):
        global env 
        env= Environment.getInstance()
        self.console = Console()

class talks_to(Action):
    def __init__(self, agent1, agent2, context="", load_memory=False, until = False):
        super().__init__()
        self.context = context
        self.until = until
        if agent1 == "user" and agent2 == "user":
            raise Exception("Both agents cannot be user")
        
        if agent1 == "user" or agent2 == "user":
            self.conversation_type = "user"
        elif agent2 == "self": 
            self.conversation_type = "self"
            agent2 = agent1
        else:
            self.conversation_type = "agent"

        if env.config.memory_mode == "ephemeral" and env.messages.step == 0:
            if self.conversation_type == "user":
                non_user_agent = agent1 if agent1 != "user" else agent2
                user_speaks_first = True if agent1 == "user" else False
                agent = Agent(os.path.join(os.getcwd(), "agents", non_user_agent.agent_filename))
                self.agent = agent
            else:
                agent1 = Agent(os.path.join(os.getcwd(), "agents", agent1.agent_filename))
                agent2 = Agent(os.path.join(os.getcwd(), "agents", agent2.agent_filename))
                self.agent1 = agent1
                self.agent2 = agent2
        
        

    def run(self):
        if self.conversation_type == "user":
            self.step_conversation_user(self.agent)
        else:
            self.step_conversation_agent(self.agent1, self.agent2, context=self.context)

    def render_markdown(self, text):
        """Render Markdown text to the terminal."""
        markdown = Markdown(text)
        self.console.print(markdown)
    
    def step_conversation_user(self, agent, context="", user_speaks_first=True):
        if not user_speaks_first:
            if context != "":
                response = agent.get_response("Initiatate a conversation with context:" + str(context))
                self.render_markdown(f"**{agent.name}:**\n" + response)
            else:
                response = agent.get_response("Initiatate a conversation")
                self.render_markdown(f"**{agent.name}:**\n" + response)
            env.messages.step += 1

        prompt_user = "**User:**"
        self.render_markdown(prompt_user)
        if env.messages.step == 0 and context != "" and user_speaks_first:
            user_input = "CONTEXT: " + str(context) + "\n USER: " + input()
        else:
            user_input = input()
        response = agent.get_response(user_input)
        self.render_markdown(f"**{agent.name}:**\n" + response)
        env.messages.step += 1
        self.check_transitions()
        self.check_if_statements()
        if not self.until:
            return self.step_conversation_user(agent)
        else:
            return
    
    def step_conversation_agent(self, agent1, agent2, context=""):
        if context != "":
            response = agent1.get_response("Initiatate a conversation with context:" + str(context))
        else:
            response = agent1.get_response("Initiatate a conversation")
        
        response = agent2.get_response(response)
        env.messages.step += 1
        self.check_transitions()
        self.check_if_statements()

        if env.config.verbose:
            self.render_markdown(f"**{agent1.name}:**\n" + response)

        if not self.until:
            return self.step_conversation_agent(agent1, agent2)
        else:
            return
        
    def __str__(self):
        if self.conversation_type == "user":
            return f"{self.agent} talks to the user"
        if self.conversation_type == "agent":
            return f"{self.agent1.name} talks to {self.agent2.name}"
        if self.conversation_type == "self":
            return f"{self.agent1.name} talks to itself"

class reflect(Action):
    def __init__(self, agent, context=""):
        self.agent = agent
        self.context = context
    
    def run(self, context=""):
        if not context:
            self.agent.reflect()
        else:
            self.agent.reflect(context=context)
        return

class call(Action):
    def __init__(self, function_name, args_dict):
        super().__init__()
        self.function_name = function_name
        self.args_dict = args_dict
    def __str__(self):
        return f"Call function {self.function_name} with args {json.dumps(self.args_dict)}"
    def run(self, ):
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
            return function(**self.args_dict)
        except Exception as e:
            raise RuntimeError(f"Failed to run function {self.function_name}. Error: {str(e)}")
class let(Action):
    def __init__(self, variable, value):
        super().__init__()
        self.variable = variable
        self.value = value

    def run(self):
        # This basically converts x.y.z.a=5 to env.variables.new_index("x").new_index("y").new_index("z").set_value("a", 5)
        # more secure and flexible than using the value of the variable directly (specifically if you have a field key stored in a variable)
        def recursive_set(dynamic_attr_dict, keys, value):
            if len(keys) == 1:
                dynamic_attr_dict.set_value(keys[0], value)
            else:
                new_dynamic_attr_dict = dynamic_attr_dict.new_index(keys[0])
                recursive_set(new_dynamic_attr_dict, keys[1:], value)
        keys = self.variable.split(".")
        recursive_set(env.variables, keys, self.value)
    def __str__(self):
        return f"Set {self.variable} to {self.value}"
    
class println(Action):
    def __init__(self, message):
        self.message = message

    def __str__(self):
        return f"Prints {self.message}"
    
    def run(self):
        print(str(self.message))

#not sure how to hand the iterator to the objects
class loop(Action):
    def __init__(self, list, iterator, actions):
        self.list = list
        self.iterator = iterator
        self.actions = actions
    def run(self):
        for item in self.list:
            self.iterator = item
            for action in self.actions:
                action.run()
    def __str__(self):
        return f"Loop through {self.list} with {self.iterator} and do {[str(action) for action in self.actions]}"

"""
class if_statement(Action):
    def __init__(self, condition, actions):
        self.condition = condition
        self.actions = actions
    
    def run(self):
        if self.condition:
            for action in self.actions:
                action.run()
        else:
            pass
    

    def __str__(self):
        return f"If {str(self.condition)} then {[str(action) for action in self.actions]}"
"""
class go_to(Action):
    def __init__(self, state, context=""):
        super().__init__()
        self.state = state
        self.context = context
        env.messages.use_context = False
    def run(self):
        env.current_state = self.state
        if self.context:
            env.messages.use_context = True
            env.messages.context = self.context
        return
    def __str__(self):
        return f"Go to {self.state}"
    

            
class terminate(Action):
    def __init__(self):
        env= Environment.getInstance()
    def run(self):
        sys.exit()
