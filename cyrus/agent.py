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
import boto3
import tempfile
import uuid
import zipfile
import subprocess
import venv
import shutil
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
        cls.platform = platform
        if platform == "openai-assistant":
            ret = OAIAssistantAgent(agent_config)
            ret.__init__(agent_config)
            return ret
        elif platform == "bedrock-agent":
            ret = BedrockAgent(agent_config)
            ret.__init__(agent_config)
            return ret
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
        
        if agent_config['platform'] not in ["openai-assistant", "bedrock-agent", "gemini"]:
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
                    elements = {
                        "type": None,
                        "function": {
                            "name": None,
                            "parameters": ["type", "properties", "required"],
                            "description": None
                        }
                    }
                    for key in elements["function"]["parameters"].copy():
                        if key not in function_data["function"]["parameters"]:
                            del elements["function"]["parameters"][key]
                    for key in function_data["function"].copy():
                        if key not in elements["function"]:
                            del function_data["function"][key]
                    for key in function_data.copy():
                        if key not in elements:
                            del function_data[key]
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
    

class BedrockAgent(Agent):
    def __init__(self, agent_config):

        self.name = agent_config['name']
        self.role = agent_config['role']
        self.system_prompt = agent_config['system_prompt']
        self.model = agent_config['model']
        
        self.lambda_client = boto3.client('lambda')
        self.iam_client = boto3.client('iam')
        self.function_arns = {}

        for function_file in agent_config.get('functions', []):
            function_path = os.path.join(os.getcwd(), "functions", function_file + ".function")
            with open(function_path, 'r') as file:
                function_data = json.load(file)

            # Add an 'id' field to the function data if it doesn't exist
            if 'id' not in function_data:
                function_data['id'] = str(uuid.uuid4())
                with open(function_path, 'w') as file:
                    json.dump(function_data, file)

            function_name = f"{function_file}-{function_data['id']}"
            
            # Create a new IAM role for the Lambda function
            role_name = f"{function_name}-role"
            try:
                response = self.iam_client.create_role(
                    RoleName=role_name,
                    AssumeRolePolicyDocument=json.dumps({
                        "Version": "2012-10-17",
                        "Statement": [
                            {
                                "Effect": "Allow",
                                "Principal": {
                                    "Service": "lambda.amazonaws.com"
                                },
                                "Action": "sts:AssumeRole"
                            }
                        ]
                    })
                )
                role_arn = response['Role']['Arn']
                
                # Attach necessary permissions to the role
                self.iam_client.attach_role_policy(
                    RoleName=role_name,
                    PolicyArn="arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
                )
            except self.iam_client.exceptions.EntityAlreadyExistsException:
                # If the role already exists, retrieve its ARN
                response = self.iam_client.get_role(RoleName=role_name)
                role_arn = response['Role']['Arn']
            
            # Create a Lambda layer if dependencies are specified
            layer_arn = None
            if 'dependencies' in function_data:
                layer_name = f"{function_name}-layer"
                layer_zip = self._create_layer_package(function_data['dependencies'])
                try:
                    response = self.lambda_client.publish_layer_version(
                        LayerName=layer_name,
                        Content={
                            'ZipFile': layer_zip
                        },
                        CompatibleRuntimes=['python3.8']  # Specify the appropriate runtime
                    )
                    layer_arn = response['LayerVersionArn']
                except self.lambda_client.exceptions.ResourceConflictException:
                    # If the layer already exists, retrieve its ARN
                    response = self.lambda_client.list_layer_versions(LayerName=layer_name)
                    layer_arn = response['LayerVersions'][0]['LayerVersionArn']

            try:
                # Check if the Lambda function already exists
                response = self.lambda_client.get_function(FunctionName=function_name)
                function_arn = response['Configuration']['FunctionArn']
                self.function_arns[function_file] = function_arn
            except self.lambda_client.exceptions.ResourceNotFoundException:
                # Create the Lambda function if it doesn't exist
                kwargs = {
                    'FunctionName': function_name,
                    'Runtime': 'python3.8',  # Specify the appropriate runtime
                    'Role': role_arn,
                    'Handler': f"{function_file}.lambda_handler",
                    'Code': {
                        'ZipFile': self._create_deployment_package(function_file)
                    }
                }
                if layer_arn:
                    kwargs['Layers'] = [layer_arn]
                response = self.lambda_client.create_function(**kwargs)
                function_arn = response['FunctionArn']
                self.function_arns[function_file] = function_arn

            # Create the OpenAPI schema for the Lambda function
            openapi_schema = {
                "openapi": "3.0.0",
                "info": {
                    "title": function_data["name"],
                    "version": "1.0.0",
                    "description": function_data["description"]
                },
                "paths": {
                    "/": {
                        "post": {
                            "summary": f"Invoke the {function_data['name']} Lambda function",
                            "operationId": f"{function_data['name']}_invoke",
                            "requestBody": {
                                "content": {
                                    "application/json": {
                                        "schema": function_data["parameters"]
                                    }
                                },
                                "required": True
                            },
                            "responses": {
                                "200": {
                                    "description": "Successful response",
                                    "content": {
                                        "application/json": {
                                            "schema": {
                                                "$ref": "#/components/schemas/Response"
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                },
                "components": {
                    "schemas": {
                        "Response": {
                            "type": "object",
                            "properties": {
                                "statusCode": {
                                    "type": "integer"
                                },
                                "body": {
                                    "type": "object"
                                }
                            }
                        }
                    }
                }
            }

            # Update the Lambda function configuration with the OpenAPI schema
            response = self.lambda_client.update_function_configuration(
                FunctionName=function_name,
                Description=function_data["description"],
                Handler=f"{function_file}.lambda_handler",
                Runtime="python3.8",
                Environment={
                    "Variables": {
                        "OPENAPI_SCHEMA": json.dumps(openapi_schema)
                    }
                }
            )

        self.knowledge_base_ids = {}
        self.bedrock_client = boto3.client('bedrock-agent')

        for document_file in agent_config.get('documents', []):
            document_path = os.path.join(os.getcwd(), "documents", document_file)
            with open(document_path, 'r') as file:
                document_content = file.read()

            knowledge_base_name = f"{self.name}-{document_file}-kb"
            
        try:
            # Check if the knowledge base already exists
            response = self.bedrock_client.list_knowledge_bases()
            existing_knowledge_bases = response['knowledgeBaseSummaries']
            knowledge_base_exists = False
            if existing_knowledge_bases:
                for kb in existing_knowledge_bases:
                    if kb['Name'] == knowledge_base_name:
                        knowledge_base_id = kb['Id']
                        knowledge_base_exists = True
                        break
            
            if not knowledge_base_exists:
                # Create a new knowledge base
                response = self.bedrock_client.create_knowledge_base(
                    name=knowledge_base_name,
                    description=f"Knowledge base for {document_file}",
                    roleArn=role_arn,
                    knowledgeBaseConfiguration= { 
                        "type": "VECTOR",
                        "vectorKnowledgeBaseConfiguration": { 
                            "embeddingModelArn": "[PROVISION]"
                        },
                    },
                    storageConfiguration={ 
                        "opensearchServerlessConfiguration": { 
                            "collectionArn": "[PROVISION]",
                            "fieldMapping": { 
                                "metadataField": "metadata",
                                "textField": "text",
                                "vectorField": "vector",
                            },
                            "vectorIndexName": document_file
                        }
                    }
                )
                
                # Wait for the knowledge base to be created
                while True:
                    response = self.bedrock_client.get_knowledge_base(
                        Id=knowledge_base_id
                    )
                    if response['Status'] == 'Active':
                        break
                    time.sleep(1)
                
                # Add the document content to the knowledge base
                response = self.bedrock_client.create_content(
                    KnowledgeBaseId=knowledge_base_id,
                    Name=document_file,
                    ContentType='PLAIN_TEXT',
                    Content=document_content
                )
            
            self.knowledge_base_ids[document_file] = knowledge_base_id

        except self.bedrock_client.exceptions.ResourceNotFoundException:
            # Handle the case when the knowledge base doesn't exist
            print(f"Knowledge base {knowledge_base_name} not found.")

        except self.bedrock_client.exceptions.ConflictException:
            # Handle the case when the knowledge base already exists
            print(f"Knowledge base {knowledge_base_name} already exists.")


        # Create the Bedrock agent
        try:
            response = self.bedrock_client.create_agent(
                Name=self.name,
                Description=self.system_prompt,
                LongDescription=self.system_prompt,
                BotType='BEDROCK',
                IdleSessionTTLInSeconds=300,
                PrivacyPolicy='none',
                InstancePolicy={
                    'OriginRestrictions': [{
                        'URIs': ['*']
                    }]
                },
                DataPrivacy={
                    'ChildDirected': False
                },
                StartingIntent={
                    'IntentName': 'Default'
                },
                EnabledLocales=['en_US']
            )
            self.agent_id = response['Id']

            # Attach Lambda functions to the agent
            for function_name, function_arn in self.function_arns.items():
                response = self.bedrock_client.create_function_association(
                    FunctionName=function_name,
                    FunctionARN=function_arn,
                    SkillId=self.agent_id
                )

            # Attach knowledge bases to the agent
            for document_file, knowledge_base_id in self.knowledge_base_ids.items():
                response = self.bedrock_client.associate_knowledge_base(
                    BotId=self.agent_id,
                    BotVersion='DRAFT',
                    KnowledgeBaseId=knowledge_base_id
                )

            # Build the agent
            response = self.bedrock_client.build_agent(
                BotId=self.agent_id,
                BotVersion='DRAFT'
            )

            # Wait for the agent to be built
            while True:
                response = self.bedrock_client.describe_agent(
                    BotId=self.agent_id,
                    BotVersion='DRAFT'
                )
                if response['Status'] == 'Available':
                    break
                time.sleep(1)

            # Assign the agent to self.agent
            self.agent = response['Bot']

        except self.bedrock_client.exceptions.ConflictException:
            # Handle the case when the agent already exists
            print(f"Agent {self.name} already exists.")

        except self.bedrock_client.exceptions.ServiceQuotaExceededException:
            # Handle the case when the service quota is exceeded
            print("Service quota exceeded. Please check your AWS account limits.")
    
    def generate_message(self, prompt, session_id=None):

        if session_id is None:
            session_id = str(uuid.uuid4())  # Generate a new session ID if not provided

        try:
            response = self.bedrock_client.post_text(
                botId=self.agent_id,
                botAliasId=self.agent['botAliasId'],
                localeId='en_US',
                sessionId=session_id,
                text=prompt
            )

            message = response['message']
            session_state = response['sessionState']

            # Process the response and session state as needed
            # ...

            return message

        except self.bedrock_client.exceptions.NotFoundException:
            raise Exception(f"Agent '{self.name}' not found.")

        except self.bedrock_client.exceptions.BadRequestException as e:
            raise Exception(f"Invalid request: {str(e)}")

        except self.bedrock_client.exceptions.InternalServerException as e:
            raise Exception(f"Internal server error: {str(e)}")

    def terminate(self, remove_files=False):
        print("Terminating Bedrock agent... (eventually)")
    
    def load_thread(self, thread):
        print("Loading thread into Bedrock agent... (eventually)")

    def _create_layer_package(self, dependencies):

        # Create a temporary directory for the virtual environment
        temp_dir = tempfile.mkdtemp()

        # Create virtual environment
        venv_dir = os.path.join(temp_dir, "venv")
        subprocess.run(["python3", "-m", "venv", venv_dir], check=True)

        # Install dependencies using pip from the virtual environment
        pip_executable = os.path.join(venv_dir, "bin", "pip")  # Use "Scripts\\pip.exe" on Windows
        
        for dependency in dependencies:
            try:
                subprocess.run([pip_executable, "install", dependency], check=True, stderr=subprocess.PIPE)
            except subprocess.CalledProcessError as e:
                print(f"Failed to install {dependency}: {e.stderr.decode()}")

        # Prepare directory for Lambda Layer
        layer_name = str(uuid.uuid4())
        layer_dir = os.path.join(temp_dir, layer_name)
        os.makedirs(layer_dir, exist_ok=True)
        site_packages_dir = os.path.join(venv_dir, "lib", os.listdir(os.path.join(venv_dir, "lib"))[0], "site-packages")
        shutil.copytree(site_packages_dir, os.path.join(layer_dir, "python"))

        # Determine the correct path for saving the zip file
        zip_file_name = f"{layer_name}_layer.zip"
        layer_zip_path = os.path.join(os.path.dirname(__file__), zip_file_name)  # Adjust the path as needed

        # Create zip file
        shutil.make_archive(base_name=layer_name, format="zip", root_dir=temp_dir, base_dir=layer_name)

        # Move the zip file to the desired location
        shutil.move(f"{layer_name}.zip", layer_zip_path)

        
        with open(layer_zip_path, "rb") as layer_zip:
            layer_content = layer_zip.read()

        # Clean up
        shutil.rmtree(temp_dir)

        return layer_content
    
    def _create_deployment_package(self, function_file):
        # Create a temporary directory for the deployment package
        temp_dir = tempfile.mkdtemp()

        # Copy the function file to the temporary directory
        shutil.copy(os.path.join(os.getcwd(), "functions", function_file + ".py"), temp_dir)

        # Create the deployment package zip file
        zip_file_name = f"{function_file}_deployment_package.zip"
        deployment_package_path = os.path.join(os.path.dirname(__file__), zip_file_name)
        shutil.make_archive(base_name=function_file, format="zip", root_dir=temp_dir)

        # Move the zip file to the desired location
        shutil.move(f"{function_file}.zip", deployment_package_path)

        # Read the deployment package content
        with open(deployment_package_path, "rb") as deployment_package:
            deployment_package_content = deployment_package.read()

        # Clean up the temporary directory
        shutil.rmtree(temp_dir)

        return deployment_package_content
class GeminiAgent(Agent):
    def __init__(self, agent_config):
        pass

    def generate_message(self, prompt):
        pass

    def terminate(self, remove_files=False):
        pass

    def load_thread(self, thread):
        pass
 