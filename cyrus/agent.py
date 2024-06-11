import json
import os
import sys
import time
import importlib.util
import inspect
import asyncio
import base64
from openai import OpenAI
from abc import ABC, abstractmethod
from cyrus import Environment, Message, Thread, vprint

class Agent(ABC):
    @abstractmethod
    def generate_message(self, prompt, images=[]):
        pass

    @abstractmethod
    def terminate(self, remove_files=False):
        pass

    @abstractmethod
    async def load_thread(self, thread):
        pass

    @abstractmethod
    def __init__(self, agent_config): 
        pass

    @classmethod
    async def create(cls, agent_config_file):
        agent_config_file = os.path.join(os.getcwd(), "agents", agent_config_file + ".agent")
        cls.validate_agent_file(agent_config_file)
        # Load agent config file as JSON
        with open(agent_config_file, 'r') as file:
            agent_config = json.load(file)
        platform = agent_config['platform']
        if platform == "openai-assistant":
            agent = OAIAgent(agent_config)
            await agent.init()
            return agent
        elif platform == "bedrock-agent":
            return BedrockAgent(agent_config)
        elif platform == "gemini":
            print("Coming Soon ;)")
        else:
            raise Exception(f"Invalid platform: {platform}")

    async def get_response(self, prompt, images=[]):
        return await self.generate_message(prompt, images)

    @classmethod
    def cot(cls, context=None, prompts=[]):
        if context is None:
            for prompt in prompts:
                ret = cls.get_response(prompt)
            return ret
        else:
            if len(prompts) == 0:
                prompts = ["Reflect on the quality of your last message. Generate a detailed evaluation that identifies what went well and what could have been done differently to achieve an improved outcome. Consider the added context: " + str(context)]
            else:
                ret = cls.get_response("CONTEXT: " + str(context) + " " + prompts[0])
            for prompt in prompts[1:]:
                ret = cls.get_response(prompt)
            return ret
    
    @classmethod
    def reflect(cls, context=None):
        return cls.cot(context=context)

    @classmethod
    def call_function(cls, function, args):
        function_file = os.path.join(os.getcwd(), "functions", function + ".py")

        if not os.path.exists(function_file):
            raise FileNotFoundError(f"The file {function_file} does not exist.")

        spec = importlib.util.spec_from_file_location(function, function_file)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        if function not in dir(module):
            raise NameError(f"The function {function} does not exist in the file {function_file}.")

        func = getattr(module, function)

        vprint(f"Function {function} called with arguments: {args}")
        func_args = inspect.getfullargspec(func).args
        for arg in args:
            if arg not in func_args:
                raise TypeError(f"The function {function} does not accept a parameter named {arg}.")
        
        env = Environment.getInstance()
        env.function_status[function] = "in progress"
        vprint("flag set to in progress")
        ret = func(**args)
        env.function_status[function] = "completed"
        vprint(f"Function {function} returned: {ret}")
        vprint("flag set to completed")
        return ret

    @classmethod
    def validate_function_file(cls, function_file):
        # Check if the extension is .function
        if function_file.split(".")[1] != "function":
            raise Exception(f"Invalid file extension: {function_file.split('.')[1]}")
        # Check if the file is a JSON
        with open(function_file, 'r') as file:
            try:
                function_config = json.load(file)
                function_config = {"type": "function", "function": function_config}
            except json.JSONDecodeError:
                raise Exception(f"Invalid formatting (JSON DECODE ERROR): {function_file}")

        # Check if the file has the required properties
        required_properties = ["type", "function"]
        for property in required_properties:
            if property not in function_config:
                raise Exception(f"Missing property: {property}")      

    @classmethod
    def validate_agent_file(cls, agent_config_file):
        # Check if the extension is .agent
        if agent_config_file.split(".")[1] != "agent":
            raise Exception(f"Invalid file extension: {agent_config_file.split('.')[1]}")
        # Check if the file is a JSON
        with open(agent_config_file, 'r') as file:
            try:
                agent_config = json.load(file)
            except json.JSONDecodeError:
                raise Exception(f"Invalid JSON file: {agent_config_file}")

        if "platform" not in agent_config:
            raise Exception("Missing property: platform")
        
        if agent_config['platform'] not in ["openai-assistant", "bedrock-agent", "gemini"]:
            raise Exception(f"Invalid platform: {agent_config['platform']}")
        
        if agent_config['platform'] == "openai-assistant":
            required_properties = ["name", "role", "system_prompt", "model", "tools", "functions", "files"]
            for property in required_properties:
                if property in ["name", "role", "system_prompt", "model"] and property not in agent_config:
                    raise Exception(f"Missing property: {property}")
                if property in ["tools", "functions", "files"] and property not in agent_config:
                    agent_config[property] = []
        
            # Check if the tools are valid
            for tool in agent_config['tools']:
                if tool not in ["code interpreter", "retrieval"]:
                    raise Exception(f"Invalid tool: {tool}")

    def __str__(self):
        return f"Agent: {self.name}, Platform: {self.platform}, Role: {self.role}, Model: {self.model}, Tools: {self.tools}, Functions: {self.functions}, Files: {self.files}"

class OAIAgent(Agent):
    def __init__(self, agent_config):
        global env
        env = Environment.getInstance()
        self.name = agent_config['name']
        self.role = agent_config['role']
        self.system_prompt = agent_config['system_prompt']
        self.model = agent_config['model']
        self.function_names = agent_config.get('functions', [])
        self.client = OpenAI()
        self.thread = [{"role": "system", "content": self.system_prompt}]
        self.function_definitions = self.load_function_definitions(self.function_names)
        self.function_definitions = [{"type": "function", "function": x}  for x in self.function_definitions]

    async def init(self):
        # Placeholder for any initialization logic if needed
        pass

    def load_function_definitions(self, function_names):
        function_definitions = []
        for function_name in function_names:
            function_file = os.path.join(os.getcwd(), "functions", function_name + ".function")
            self.validate_function_file(function_file)
            with open(function_file, 'r') as file:
                function_definition = json.load(file)
                function_definitions.append(function_definition)
        return function_definitions

    async def generate_message(self, prompt, images=[]):
        content = [{"role": "user", "content": prompt}]
        if images:
            for image_data in images:
                image_base64 = base64.b64encode(image_data).decode('utf-8')
                content.append({"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"}})
        
        self.thread.append({"role": "user", "content": prompt})

        response = self.client.chat.completions.create(
            model=self.model,
            messages=self.thread,
            tools=self.function_definitions,
            tool_choice="auto"
        )

        if response.choices[0].message.content:
            result = response.choices[0].message.content
        else:
            result = f""
        self.thread.append(response.choices[0].message)
        # Handle function calling
        if response.choices[0].finish_reason == "tool_calls":
            function_call = response.choices[0].message.tool_calls[0]
            function_name = function_call.function.name
            function_args = json.loads(function_call.function.arguments)
            function_result = self.call_function(function_name, function_args)
            tool_call_id = function_call.id
            # Append function result to the thread and call the model again
            self.thread.append(
                {
                    "tool_call_id": tool_call_id,
                    "role": "tool",
                    "name": function_name,
                    "content": function_result,
                }
            )
            response = self.client.chat.completions.create(
                model=self.model,
                messages=self.thread
            )
            if response.choices[0].message.content:
                result += "\n" + response.choices[0].message.content
        self.thread.append({"role": "assistant", "content": result})
        return result

    async def terminate(self, remove_files=False):
        # Placeholder for any termination logic if needed
        return f"Agent: {self.name}, Role: {self.role}, Model: {self.model}, Tools: {self.tools}, Functions: {self.functions}, Files: {self.files}"

    async def load_thread(self, local_thread, user_agent="user", assistant_agent="assistant", role_map=None):
        openai_thread = [{"role": "system", "content": self.system_prompt}]
        if len(local_thread.messages) > 0:
            for message in local_thread.messages:
                if (message.sender != user_agent and message.recipient != assistant_agent) or (message.sender != assistant_agent and message.recipient != user_agent) and role_map is None:
                    raise Exception(f"Provided agent aliases do not match the sender and recipient of the messages in the local thread. The sender and recipient of the first message in the local thread are {message.sender} and {message.recipient} respectively, while the provided aliases are {role_map.keys()}.")
                if role_map is not None:
                    for key, value in role_map.items():
                        if key not in [message.sender, message.recipient]:
                            raise Exception(f"Provided agent aliases do not match the sender and recipient of the messages in the local thread. The sender and recipient of the first message in the local thread are {message.sender} and {message.recipient} respectively, while the provided aliases are {role_map.keys()}.")
                        if value not in ["user", "assistant"]:
                            raise Exception(f"Invalid role: {value}, agent must be mapped must be either 'user' or 'assistant'")
                role_map = {user_agent: 'user', assistant_agent: 'assistant'}
        if not role_map:
            role_map = {user_agent: 'user', assistant_agent: 'assistant'}
        # Iterate over local messages and create them in the OpenAI thread
        for local_message in local_thread.messages:
            sender = local_message.sender
            role = role_map[sender]
            openai_thread.append({"role": role, "content": local_message.content})

        self.thread = openai_thread
        return
