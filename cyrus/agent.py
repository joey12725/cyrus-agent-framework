import json
import os
import importlib.util
import inspect
import asyncio
import base64
from openai import OpenAI
from abc import ABC, abstractmethod
from cyrus import Environment, Message, Thread, vprint
import boto3
import logging
import random

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
        global env
        env = Environment.getInstance()
        agent_config_file = os.path.join(env.config["project_directory"], "agents", agent_config_file + ".agent")
        cls.validate_agent_file(agent_config_file)
        # Load agent config file as JSON
        with open(agent_config_file, 'r') as file:
            agent_config = json.load(file)
        platform = agent_config['platform']
        if platform == "openai":
            agent = OAIAgent(agent_config)
            return agent
        elif platform == "bedrock":
            return BedrockAgent(agent_config)
        elif platform == "gemini":
            print("Coming Soon ;)")
        elif platform == "perplexity":
            agent = PerplexityAgent(agent_config)
            return agent
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
    def call_function(cls, function, args):
        env = Environment.getInstance()
        function_file = os.path.join(env.config["project_directory"], "functions", function + ".py")

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
        ret = func(**args)
        env.function_status[function] = "completed"
        return str(ret)

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
        
        if "profile_picture" not in agent_config:
            #random file path from cyrus-agent-framework\front-end\resources\images
            agent_config["profile_picture"] = random.choice(os.listdir(os.path.join(os.getcwd(), "resources", "profile_images")))
            #write out the profile picture to the agent file
            with open(agent_config_file, 'w') as file:
                json.dump(agent_config, file, indent=4)
            
        
        if agent_config['platform'] not in ["openai", "bedrock", "gemini", "perplexity"]:
            raise Exception(f"Invalid platform: {agent_config['platform']}")
        
        if agent_config['platform'] == "openai":
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
        return f"Agent: {self.name}"

class OAIAgent(Agent):
    def __init__(self, agent_config):
        self.platform = "openai"
        global env
        env = Environment.getInstance()
        self.name = agent_config['name']
        self.role = agent_config['role']
        self.system_prompt = agent_config['system_prompt']
        self.model = agent_config['model']
        self.function_names = agent_config.get('functions', [])
        self.use_memory = agent_config.get('use_memory', False)
        self.use_rerank_memory = agent_config.get('use_rerank_memory', False)
        self.use_rerank_documents = agent_config.get('use_rerank_documents', False)
        self.thread = [{"role": "system", "content": self.system_prompt}]
        self.function_definitions = self.load_function_definitions(self.function_names)
        self.function_definitions = [{"type": "function", "function": x}  for x in self.function_definitions]
        self.client = OpenAI(api_key=env.config["API_Keys"]["openai"])
        self.documents = agent_config.get('documents', [])

    
    def load_function_definitions(self, function_names):
        function_definitions = []
        for function_name in function_names:
            function_file = os.path.join(env.config["project_directory"], "functions", function_name + ".function")
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
        if self.function_definitions:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=self.thread,
                tools=self.function_definitions,
                tool_choice="auto"
            )
        else:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=self.thread
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
                    "content": [{"text": str(function_result)}],
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
        return 
    
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

class PerplexityAgent(OAIAgent):
    def __init__(self, agent_config):
        self.platform = "perplexity"
        global env
        env = Environment.getInstance()
        self.name = agent_config['name']
        self.role = agent_config['role']
        self.system_prompt = agent_config['system_prompt']
        self.model = agent_config['model']
        self.function_names = agent_config.get('functions', [])
        self.thread = [{"role": "system", "content": self.system_prompt}]
        self.function_definitions = self.load_function_definitions(self.function_names)
        self.use_memory = agent_config.get('use_memory', False)
        self.use_rerank_memory = agent_config.get('use_rerank_memory', False)
        self.use_rerank_documents = agent_config.get('use_rerank_documents', False)
        self.function_definitions = [{"type": "function", "function": x}  for x in self.function_definitions]
        self.client =  OpenAI(api_key=env.config["API_Keys"]["perplexity"], base_url="https://api.perplexity.ai")
        self.documents = agent_config.get('documents', [])
class BedrockAgent(Agent):
        
    def __init__(self, agent_config):
        MODEL_CAPABILITIES = {
            "amazon.titan-text-express-v1": {"system_prompt": False, "tool_use": False},
            "amazon.titan-text-lite-v1": {"system_prompt": False, "tool_use": False},
            "amazon.titan-text-premier-v1:0": {"system_prompt": False, "tool_use": False},
            "anthropic.claude-v2": {"system_prompt": True, "tool_use": False},
            "anthropic.claude-v2:1": {"system_prompt": True, "tool_use": False},
            "anthropic.claude-3-sonnet-20240229-v1:0": {"system_prompt": True, "tool_use": True},
            "anthropic.claude-3-haiku-20240307-v1:0": {"system_prompt": True, "tool_use": True},
            "anthropic.claude-3-opus-20240229-v1:0": {"system_prompt": True, "tool_use": True},
            "anthropic.claude-instant-v1": {"system_prompt": True, "tool_use": False},
            "cohere.command-r-v1:0": {"system_prompt": True, "tool_use": True},
            "cohere.command-r-plus-v1:0": {"system_prompt": True, "tool_use": True},
            "meta.llama2-13b-chat-v1": {"system_prompt": True, "tool_use": False},
            "meta.llama2-70b-chat-v1": {"system_prompt": True, "tool_use": False},
            "mistral.mistral-7b-instruct-v0:2": {"system_prompt": False, "tool_use": False},
            "mistral.mixtral-8x7b-instruct-v0:1": {"system_prompt": False, "tool_use": False},
            "mistral.mistral-large-2402-v1:0": {"system_prompt": True, "tool_use": True},
            "mistral.mistral-small-2402-v1:0": {"system_prompt": True, "tool_use": False},
            "ai21.j2-mid-v1": {"system_prompt": False, "tool_use": False},
            "ai21.j2-ultra-v1": {"system_prompt": False, "tool_use": False}
            }
        self.platform = "bedrock"
        global env
        env = Environment.getInstance()
        self.name = agent_config['name']
        self.role = agent_config['role']
        self.system_prompt = agent_config['system_prompt'] if MODEL_CAPABILITIES.get(agent_config['model'], {}).get("system_prompt", False) else None
        self.model = agent_config['model']
        self.function_names = agent_config.get('functions', []) if MODEL_CAPABILITIES.get(agent_config['model'], {}).get("tool_use", False) else []
        self.thread = []
        self.function_definitions = self.load_function_definitions(self.function_names)
        self.use_memory = agent_config.get('use_memory', False)
        self.use_rerank_memory = agent_config.get('use_rerank_memory', False)
        self.use_rerank_documents = agent_config.get('use_rerank_documents', False)
        self.function_definitions = [self.translate_function_definition(x) for x in self.function_definitions]
        access_key_id = str(env.config["API_Keys"]["aws_access_key_id"])
        secret_access_key = str(env.config["API_Keys"]["aws_secret_access_key"])
        self.documents = agent_config.get('documents', [])
        self.session = boto3.Session(
            aws_access_key_id=access_key_id,
            aws_secret_access_key=secret_access_key,
            region_name="us-east-1"
        )
        self.client = self.session.client(service_name='bedrock-runtime')
        capabilities = MODEL_CAPABILITIES.get(self.model, {})
        if not capabilities.get("system_prompt", False):
            logging.warning(f"System prompts are not supported for the model {self.model}.")
            self.system_prompt = None
            self.thread = [msg for msg in self.thread if msg["role"] != "system"]
        if not capabilities.get("tool_use", False):
            logging.warning(f"Tool use is not supported for the model {self.model}.")
            self.function_definitions = []

    def translate_function_definition(self, source):
        target = {
            "toolSpec": {
                "name": source["name"],
                "description": source["description"],
                "inputSchema": {
                    "json": {
                        "type": "object",
                        "properties": source["parameters"]["properties"],
                        "required": source["parameters"]["required"]
                    }
                }
            }
        }
        return target

    def load_function_definitions(self, function_names):
        function_definitions = []
        for function_name in function_names:
            function_file = os.path.join(env.config["project_directory"], "functions", function_name + ".function")
            self.validate_function_file(function_file)
            with open(function_file, 'r') as file:
                function_definition = json.load(file)
                function_definitions.append(function_definition)
        return function_definitions

    async def generate_message(self, prompt, images=[]):
        content = [{"text": prompt}]
        if images:
            for image_data in images:
                image_base64 = base64.b64encode(image_data).decode('utf-8')
                content.append({"image_url": {"url": f"data:image/jpeg;base64,{image_base64}"}})

        self.thread.append({"role": "user", "content": content})
        try:
            tools = [{"toolSpec": f['toolSpec']} for f in self.function_definitions]

            if self.function_definitions and not self.system_prompt:
                response = self.client.converse(
                    modelId=self.model,
                    messages=self.thread,
                    toolConfig={"tools": tools}
                )
            elif self.function_definitions and self.system_prompt:
                response = self.client.converse(
                    modelId=self.model,
                    messages=self.thread,
                    toolConfig={"tools": tools},
                    system=[{"text": self.system_prompt}]
                )
            elif not self.function_definitions and self.system_prompt:
                response = self.client.converse(
                    modelId=self.model,
                    messages=self.thread,
                    system=[{"text": self.system_prompt}]
                )
            else:
                response = self.client.converse(
                    modelId=self.model,
                    messages=self.thread
                )   
        except self.client.exceptions.ClientError as e:
            logging.error(f"Error communicating with Bedrock: {e}")
            return f"Error: {str(e)}"

        output_message = response['output']['message']
        #self.thread.append(output_message)

        stop_reason = response['stopReason']

        if stop_reason == 'tool_use':
            tool_requests = response['output']['message']['content']
            tool_text_response = [response['output']['message']['content'][i]['text'] for i in range(len(tool_requests)) if 'text' in tool_requests[i]][0] if len([response['output']['message']['content'][i]['text'] for i in range(len(tool_requests)) if 'text' in tool_requests[i]]) > 0 else "..."
            self.thread.append({"role": "assistant", "content": tool_requests})
            for tool_request in tool_requests:
                if 'toolUse' in tool_request:
                    tool = tool_request['toolUse']
                    logging.info("Requesting tool %s. Request: %s", tool['name'], tool['toolUseId'])

                    if tool['name'] in [f['toolSpec']['name'] for f in self.function_definitions]:
                        tool_result = {}
                        try:
                            function_name = tool['name']
                            function_args = tool['input']
                            function_result = self.call_function(function_name, function_args)
                            tool_result = {
                                "toolUseId": tool['toolUseId'],
                                "content": [{"text": str(function_result)}]
                            }
                        except Exception as err:
                            tool_result = {
                                "toolUseId": tool['toolUseId'],
                                "content": [{"text": err.args[0]}],
                                "status": 'error'
                            }

                        tool_result_message = {
                            "role": "user",
                            "content": [
                                {
                                    "toolResult": tool_result
                                }
                            ]
                        }
                        self.thread.append(tool_result_message)
                        try:
                            response = self.client.converse(
                                modelId=self.model,
                                messages=self.thread,
                                toolConfig={"tools": tools}
                            )
                        except self.client.exceptions.ClientError as e:
                            logging.error(f"Error communicating with Bedrock: {e}")
                            return f"Error: {str(e)}"

                        output_message = response['output']['message']

        result = "\n".join([c['text'] for c in output_message['content']])
        self.thread.append({"role": "assistant", "content": [{"text": f"{result}"}]})
        if stop_reason == 'tool_use':
            return f"{tool_text_response}\n{result}"
        else:
            return result
    async def terminate(self, remove_files=False):
        # Placeholder for any termination logic if needed
        return

    async def load_thread(self, local_thread, user_agent="user", assistant_agent="assistant", role_map=None):
       
        bedrock_thread = []
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
        # Iterate over local messages and create them in the Bedrock thread
        for local_message in local_thread.messages:
            sender = local_message.sender
            role = role_map[sender]
            bedrock_thread.append({"role": role, "content": [{"text": local_message.content}]})

        self.thread = bedrock_thread
        return