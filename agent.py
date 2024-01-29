#a class for AI agents
import json
import os
from openai import OpenAI


class Agent:
    def __init__(self, agent_config_file):
        self.validate_agent_file(agent_config_file)
        with open(agent_config_file, 'r') as agent_config_file:
            agent_config = json.load(agent_config_file)
        self.name = agent_config['name']
        self.role = agent_config['role']
        self.system_prompt = agent_config['system_prompt']
        self.model = agent_config['model']

        self.tools = []
        for tool in agent_config['tools']:
            self.tools += {"type": tool}

        self.client = OpenAI.Client(api_key=os.getenv("OPENAI_API_KEY"))   

        #need to fix the indexing here
        self.functions = {}
        for function in agent_config['functions']:
            function_name = function['name']
            file_path = os.path.join(os.getcwd(), "functions", function_name + ".json")

            with open(file_path, 'r') as file:
                self.functions[function_name] = json.load(file)
                # Navigating through the nested dictionary to get the properties keys which are the function parameters
                self.functions[function_name]['args'] = list(function['parameters']['properties'].keys())
            
        for file in agent_config['files']:
            if file not in [x["filename"] for x in self.client.files.list()]: #if the file doesn't exist
                upload = self.client.files.create(
                    file=open(os.getcwd()+"docs/"+file, "rb"),
                    purpose='assistants'
                ) 
                self.files[file] = upload.id
            else:
                self.files[file] = [x["id"] for x in self.client.files.list() if x["filename"] == file][0]
        
        self.assistant = self.client.beta.assistants.create(
            instructions=self.system_prompt,
            model=self.model,
            tools=self.tools + self.functions,
            file_ids=self.files
        )

        self.thread = self.client.beta.threads.create()["id"]

    def validate_agent_file(self, agent_config_file):
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

        #check if the file has the required properties
        required_properties = ["name", "role", "system_prompt", "model", "tools", "functions", "files"]
        for property in required_properties:
            if property not in agent_config:
                raise Exception(f"Missing property: {property}")
                return False
        #check if the tools are valid
        for tool in agent_config['tools']:
            if tool not in ["code interpreter", "retrieval"]:
                raise Exception(f"Invalid tool: {tool}")
                return False

    def validate_function_file(self, function_file):
        pass

    def get_response(self, prompt):
        pass
    
    def reflect(self):
        pass

    def terminate(self):
        self.client.beta.threads.delete(self.thread)

    def call_function(self, function, args):
        pass

    def __str__ (self):
        return f"Agent: {self.name}, Role: {self.role}, Model: {self.model}, Tools: {self.tools}, Functions: {self.functions}, Files: {self.files}"

ceo = Agent(r"agent-config-files\CEO.agent")
print(str(ceo))