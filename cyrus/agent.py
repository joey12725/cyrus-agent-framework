#a class for AI agents
import json
import os
from openai import OpenAI
import sys
import time
import importlib.util
import inspect
from cyrus import Environment
from abc import ABC, abstractmethod
#set api key eviroment variable (REMOVE BEFORE NEXT COMMIT)
os.environ["OPENAI_API_KEY"] = "REDACTED_OPENAI_KEY"

class Agent(ABC):
    @abstractmethod
    def generate_message(cls, prompt):
        pass

    @abstractmethod
    def terminate(cls, remove_files=False):
        pass

    @abstractmethod
    def load_thread(cls, thread):
        pass

    @abstractmethod
    def __init__(): 
        pass

    @classmethod
    def create(cls, agent_config_file):
        agent_config_file = os.path.join(os.getcwd(), "agents", agent_config_file  + ".agent")
        cls.validate_agent_file(agent_config_file)
        #load agent config file as json
        with open(agent_config_file, 'r') as agent_config_file:
            agent_config = json.load(agent_config_file)
        platform = agent_config['platform']
        if platform == "openai-assistant":
            ret = OAIAssistantAgent(agent_config)
            ret.__init__(agent_config)
            return ret
        elif platform == "bedrock-agent":
            print("Coming Soon ;)")
        elif platform == "gemini":
            print("Coming Soon ;)")
        else:
            raise Exception(f"Invalid platform: {platform}")

    def get_response(self, prompt):
        return self.generate_message(prompt)
        

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

        func_args = inspect.getfullargspec(func).args
        for arg in args:
            if arg not in func_args:
                raise TypeError(f"The function {function} does not accept a parameter named {arg}.")
        env.function_status.set_value(function, "in progress")
        ret = func(**args)
        env.function_status.set_value(function, "completed")
        return ret

    @classmethod
    def validate_function_file(cls, function_file):

        #check if the extension is .function
        if function_file.split(".")[1] != "function":
            raise Exception(f"Invalid file extension: {function_file.split('.')[1]}")
            return False
        #check if the file is a json
        with open(function_file, 'r') as function_file:
            try:
                function_config = json.load(function_file)
                function_config = {"type": "function", "function": function_config}
            except json.JSONDecodeError:
                raise Exception(f"Invalid formatting (JSON DECODE ERROR): {function_file}")

        #check if the file has the required properties
        required_properties = ["type", "function"]
        for property in required_properties:
            if property not in function_config:
                raise Exception(f"Missing property: {property}")      
 
    @classmethod
    def validate_agent_file(cls, agent_config_file):
        #check if the extension is .agent
        if agent_config_file.split(".")[1] != "agent":
            raise Exception(f"Invalid file extension: {agent_config_file.split('.')[1]}")
            return False
        #check if the file is a json
        with open(agent_config_file, 'r') as agent_config_file:
            try:
                agent_config = json.load(agent_config_file)
            except json.JSONDecodeError:
                raise Exception(f"Invalid JSON file: {agent_config_file}")
                return False

        if "platform" not in agent_config:
            raise Exception("Missing property: platform")
        
        if agent_config['platform'] not in ["openai-assistant"]:
            raise Exception(f"Invalid platform: {agent_config['platform']}")
        
        if agent_config['platform'] == "openai-assistant":
            required_properties = ["name", "role", "system_prompt", "model", "tools", "functions", "files"]
            for property in required_properties :
                if property in ["name", "role", "system_prompt", "model"] and property not in agent_config:
                    raise Exception(f"Missing property: {property}")
                if property in ["tools", "functions", "files"] and property not in agent_config:
                    agent_config[property] = []
        
            #check if the tools are valid
            for tool in agent_config['tools']:
                if tool not in ["code interpreter", "retrieval"]:
                    raise Exception(f"Invalid tool: {tool}")
                
    def __str__(cls):
        return f"Agent: {cls.name}, Platform: {cls.platform}, Role: {cls.role}, Model: {cls.model}, Tools: {cls.tools}, Functions: {cls.functions}, Files: {cls.files}"

class OAIAssistantAgent(Agent):
    def __init__(self, agent_config):
        global env
        env = Environment.getInstance()
        self.name = agent_config['name']
        self.role = agent_config['role']
        self.system_prompt = agent_config['system_prompt']
        self.model = agent_config['model']
        self.files = {}
        self.tools = []
        self.agent_filename = agent_config['role'] + ".agent"
        if "tools" in agent_config:
            for tool in agent_config['tools']:
                self.tools.append({"type": tool})

        self.client = OpenAI()

        self.functions = {}

        for f in agent_config['functions']:
            env.function_status.set_value(f, False) 
        if "functions" in agent_config:
            for function in agent_config['functions']:
                file_path = os.path.join(os.getcwd(), "functions", function + ".function")
                with open(file_path, 'r') as file:
                    self.validate_function_file(file_path)
                    function_data = json.load(file)
                    function_data = {"type": "function", "function": function_data}
                    parameters_keys = list(function_data['function']['parameters']['properties'].keys())
                    self.functions[function] = function_data
                    self.functions["args"] = {}
                    self.functions["args"][function] = parameters_keys
        if "files" in agent_config:    
            for file in agent_config['files']:
                existing_files = self.client.files.list()
                if file not in [x.filename for x in existing_files]: #if the file doesn't exist
                    upload = self.client.files.create(
                        file=open(os.path.join(os.getcwd(), "docs", file), "rb"),
                        purpose='assistants'
                    ) 
                    self.files[file] = upload.id
                    print(f"Uploaded {file} to OpenAI")
                else:
                    self.files[file] = [x.id for x in existing_files if x.filename == file][0]
                    print(f"{file} already exists in OpenAI")

        filtered_functions = {k: v for k, v in self.functions.items() if k != "args"}

        self.assistant = self.client.beta.assistants.create(
            instructions=self.system_prompt,
            model=self.model,
            tools = self.tools + list(filtered_functions.values()),
            file_ids=list(self.files.values())
        )

        self.thread = self.client.beta.threads.create()
    
    
    def generate_message(self, prompt):

        self.client.beta.threads.messages.create(
            thread_id=self.thread.id,
            role="user",
            content=prompt
        )

        run = self.client.beta.threads.runs.create(
            thread_id=self.thread.id,
            assistant_id=self.assistant.id,
            instructions=self.system_prompt
        )

        while run.status != "completed":

            if run.status == "requires_action":
                args = [json.loads(run.required_action.submit_tool_outputs.tool_calls[x].function.arguments) for x in range(len(run.required_action.submit_tool_outputs.tool_calls))]
                functions = [run.required_action.submit_tool_outputs.tool_calls[x].function.name for x in range(len(run.required_action.submit_tool_outputs.tool_calls))]
                tool_call_id = [run.required_action.submit_tool_outputs.tool_calls[x].id for x in range(len(run.required_action.submit_tool_outputs.tool_calls))]
                run = self.client.beta.threads.runs.submit_tool_outputs(
                    thread_id=self.thread.id,
                    run_id=run.id,
                    tool_outputs= [ { "tool_call_id": tool_call_id[x],
                                      "output": self.call_function(functions[x], args[x]) } for x in range(len(run.required_action.submit_tool_outputs.tool_calls))] )

            if run.status == "expired":
                raise Exception("Run expired")
        
            if run.status == "cancelling":
                print("Run cancelling")
            
            if run.status == "cancelled":
                print("Run cancelled")
                sys.exit()
                
            if run.status == "failed":
                raise Exception("Run failed")
            
            run = self.client.beta.threads.runs.retrieve(
                thread_id=self.thread.id,
                run_id=run.id
                )
    
            time.sleep(.5)
        
        messages = self.client.beta.threads.messages.list(
            thread_id=self.thread.id
        )
        env.increment_step()
        for thread_message in messages.data:
            if thread_message.role == 'assistant':
                for content in thread_message.content:
                    try:
                        return(content.text.value)
                    except:
                        pass
    

    def terminate(self, remove_files=False):
        self.client.beta.threads.delete(self.thread.id)
        self.client.beta.assistants.delete(self.assistant.id)
        if remove_files:
            for file in self.files.values():
                self.client.beta.assistants.files.delete(
                    assistant_id=self.assistant.id,
                    file_id=self.files[file]
                )

        return f"Agent: {self.name}, Role: {self.role}, Model: {self.model}, Tools: {self.tools}, Functions: {self.functions}, Files: {self.files}"

    def load_thread(self, local_thread, user_agent = "user", assistant_agent = "assistant", role_map = None):
        openai_thread = self.client.beta.threads.create()
        if len(local_thread.messages) > 0:
            for message in local_thread.messages:
                if (message.sender != user_agent and message.recipient != assistant_agent) or (message.sender != assistant_agent and message.recipient != user_agent) and role_map is None:
                    raise Exception(f"Provided agent aliases do not match the sender and recipient of the messages in the local thread. The sender and recipient of the first message in the local thread are {message.sender} and {message.recipient} respectively, while the provided aliases are {user_agent} and {assistant_agent}.")
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
            openai_message = OpenAI.Message.create(
                thread_id=openai_thread.id,
                role=role,  # Implement this function based on your logic
                content=local_message.content,
                # Include file_ids if you have attachments
            )

        self.thread = openai_thread  # Use self.thread instead of cls.thread
        return