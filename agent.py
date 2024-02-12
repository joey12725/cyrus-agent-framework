#a class for AI agents
import json
import os
from openai import OpenAI
import sys
import time

#set api key eviroment variable (REMOVE BEFORE NEXT COMMIT)
os.environ["OPENAI_API_KEY"] = "REDACTED_OPENAI_KEY"

class Agent:
    def __init__(self, agent_config_file):
        self.validate_agent_file(agent_config_file)
        with open(agent_config_file, 'r') as agent_config_file:
            agent_config = json.load(agent_config_file)
        self.name = agent_config['name']
        self.role = agent_config['role']
        self.system_prompt = agent_config['system_prompt']
        self.model = agent_config['model']
        self.files = {}
        self.tools = []
        for tool in agent_config['tools']:
            self.tools.append({"type": tool})

        self.client = OpenAI()

        #need to fix the indexing here
        self.functions = {}
        for function in agent_config['functions']:
            file_path = os.path.join(os.getcwd(), "functions", function + ".function")

            with open(file_path, 'r') as file:
                self.validate_function_file(file_path)
                function_data = json.load(file)
                parameters_keys = list(function_data['function']['parameters']['properties'].keys())
                self.functions[function] = function_data
                self.functions[function]['args'] = parameters_keys
            
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
        
        self.assistant = self.client.beta.assistants.create(
            instructions=self.system_prompt,
            model=self.model,
            tools=self.tools + list(self.functions.values()),
            file_ids=list(self.files.values())
        )

        self.thread = self.client.beta.threads.create()

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
        #check if the extension is .function
        if function_file.split(".")[1] != "function":
            raise Exception(f"Invalid file extension: {function_file.split('.')[1]}")
            return False
        #check if the file is a json
        with open(function_file, 'r') as function_file:
            try:
                function_config = json.load(function_file)
            except json.JSONDecodeError:
                raise Exception(f"Invalid JSON file: {function_file}")

        #check if the file has the required properties
        required_properties = ["type", "function"]
        for property in required_properties:
            if property not in function_config:
                raise Exception(f"Missing property: {property}")
            
    def get_response(self, prompt):
        self.thread = self.client.beta.threads.messages.create(
            thread_id=self.thread.id,
            role="user",
            content=prompt
        )

        run = self.client.beta.threads.runs.create(
            thread_id=self.thread.id,
            assistant_id=self.assistant.id,
            instructions=self.system_prompt
        )

        while run.status != "complete":

            if run.status == "requires_action":
                print("Run requires action")
                run = self.client.beta.threads.runs.submit_tool_outputs(
                    thread_id=self.thread.id,
                    run_id=run.id,
                    tool_outputs={"response": "hello world!"}
                )

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

        return messages
    
    def reflect(self):
        pass

    def terminate(self, remove_files=False):
        self.client.beta.threads.delete(self.thread)

        if remove_files:
            for file in self.files:
                pass

    def call_function(self, function, args):
        pass

    def __str__ (self):
        return f"Agent: {self.name}, Role: {self.role}, Model: {self.model}, Tools: {self.tools}, Functions: {self.functions}, Files: {self.files}"

ceo = Agent(r"agent-config-files\CEO.agent")
print(str(ceo))
print(ceo.get_response("Hi!"))
ceo.terminate()