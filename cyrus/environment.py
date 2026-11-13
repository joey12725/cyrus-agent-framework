import configparser
import os
import uuid
import datetime
import logging
import chromadb
from openai import OpenAI
import cohere
from uuid import uuid4

# Keys can live in the [API_Keys] section of the project .ini file or in the
# environment. The .ini value wins when both are set.
API_KEY_ENV_VARS = {
    "openai": "OPENAI_API_KEY",
    "perplexity": "PERPLEXITY_API_KEY",
    "aws_access_key_id": "AWS_ACCESS_KEY_ID",
    "aws_secret_access_key": "AWS_SECRET_ACCESS_KEY",
    "cohere": "COHERE_API_KEY",
}

class VectorDatabase:
    def __init__(self, openai_api_key, cohere_api_key):
        self.openai_client = OpenAI(api_key=openai_api_key)
        self.cohere_client = cohere.Client(api_key=cohere_api_key)
        self.client = chromadb.Client()
        self.messages_collection = self.client.create_collection("messages")
        self.documents_collection = self.client.create_collection("documents")
    
    def get_embedding(self, text):
        text = text.replace("\n", " ")
        return self.openai_client.embeddings.create(input=[text], model="text-embedding-3-small").data[0].embedding
    
    def add_thread(self, thread):
        for message in thread.messages:
            self.add_message(message, thread_id=thread.id, state=thread.state)
    
    def add_message(self, message, thread_id=None, state=None):
        embedding = self.get_embedding(message.content)
        self.messages_collection.add(
            documents=[message.content],
            metadatas=[{"sender": message.sender, "recipient": message.recipient, "thread_id": thread_id, "state": state}],
            embeddings=[embedding],
            ids=[str(uuid4())]
        )
    
    def add_document(self, document, chunk_size=None):
        if chunk_size:
            chunks = [document[i:i + chunk_size] for i in range(0, len(document), chunk_size)]
        else:
            chunks = [document]
        
        for chunk in chunks:
            embedding = self.get_embedding(chunk)
            self.documents_collection.add(
                documents=[chunk],
                embeddings=[embedding],
                ids=[str(uuid4())]
            )
    
    def get_most_relevant_message(self, query_text, k=1, sender=None, recipient=None, state=None, thread_id=None, rerank=False, messages_ahead=0, messages_behind=0):
        embedding = self.get_embedding(query_text)
        query = {}
        if sender:
            query["sender"] = sender
        if recipient:
            query["recipient"] = recipient
        if state:
            query["state"] = state
        if thread_id:
            query["thread_id"] = thread_id
            
        filtered_results = self.messages_collection.query(query_texts=[query_text], n_results=k, where=query)
        
        if rerank:
            docs = [res['document'] for res in filtered_results]
            rerank_results = self.cohere_client.rerank(
                model="rerank-english-v3.0",
                query=query_text,
                documents=docs,
                top_n=k,
                return_documents=True
            )
            filtered_results = rerank_results['results']
        
        relevant_message = filtered_results[0]
        relevant_thread = self._build_thread_from_message(relevant_message, messages_ahead, messages_behind)
        return relevant_thread
    
    def _build_thread_from_message(self, message, messages_ahead, messages_behind):
        thread_messages = []
        current_thread = self.client.get_thread(id=message['metadata']['thread_id'])
        message_index = current_thread.messages.index(message)
        
        start_index = max(0, message_index - messages_behind)
        end_index = min(len(current_thread.messages), message_index + messages_ahead + 1)
        
        for i in range(start_index, end_index):
            thread_messages.append(current_thread.messages[i])
        
        return thread_messages
    
    def get_nearest_document_chunk(self, query_text, k=1, rerank=False, document_ids=None):
        embedding = self.get_embedding(query_text)
        query = {"ids": document_ids} if document_ids else {}
        filtered_results = self.documents_collection.query(query_texts=[query_text], n_results=k, where=query)
        
        if rerank:
            docs = [res['document'] for res in filtered_results]
            rerank_results = self.cohere_client.rerank(
                model="rerank-english-v3.0",
                query=query_text,
                documents=docs,
                top_n=k,
                return_documents=True
            )
            filtered_results = rerank_results['results']
        
        return filtered_results[0]['document']

class Message:
    def __init__(self, sender, recipient, message, state=None, files=None):
        if files is None:
            files = []
        if type(files) != list:
            raise ValueError("Files must be a list of File objects")
        self.sender = sender
        self.recipient = recipient
        self.content = message
        self.state = state
        self.id = uuid4()
        self.files = files
        self.timestamp = datetime.datetime.now()
    
    def __eq__(self, other):
        return self.sender == other.sender and self.recipient == other.recipient and self.content == other.content and self.state == other.state

class Thread:
    def __init__(self, state=None):
        self.messages = []
        self.members = []
        self.state = state
        self.id = uuid4()
        self.creation_time = datetime.datetime.now()
        self.last_message = datetime.datetime.now()

    def add_message(self, message):
        if message.sender not in self.members:
            self.members.append(message.sender)
        if message.recipient not in self.members:
            self.members.append(message.recipient)
        if len(self.messages) == 0:
            self.speaks_first = message.sender
        self.last_message = message.timestamp
        self.messages.append(message)
        
    def turn(self):
        return len(self.messages)
    
    def __str__(self):
        return f"Thread with members: {self.members} and messages: {[f'Sender: {message.sender}, Recipient: {message.recipient}, Content: {message.content}, State: {message.state}' for message in self.messages]}"
    
    def dump(self, token_saver=False, character_limit=0):
        ret = []
        if not token_saver:
            for message in self.messages:
                ret.append(f"{message.sender} -> {message.recipient}: {message.content}")
        elif token_saver and not character_limit:
            for message in self.messages:
                ret.append(f"{message.sender}: {message.content}")
        elif token_saver and character_limit:
            chars = 0
            for message in self.messages:
                chars += len(message.content)
                if chars <= character_limit:
                    ret.append(f"{message.sender}: {message.content}")
                else:
                    break
        return "\n".join(ret)

    def get_all_files(self):
        return [file for message in self.messages for file in message.files]


class Environment:

    _instance = None

    @staticmethod
    def getInstance(project_name=None):
        if Environment._instance is None:
            Environment(project_name)
        return Environment._instance

    def __init__(self, project_name):
        if Environment._instance is not None:
            raise Exception("This class is a singleton!")
        else:
            Environment._instance = self

        if project_name is None:
            raise ValueError("project_name must be provided when first instantiating the Environment")
        
        forbidden_characters = [" ", ".", ",", ":", ";", "'", "\"", "!", "?", "(", ")", "[", "]", "{", "}", "<", ">", "/", "\\", "|", "*", "&", "^", "%", "$", "#", "@", "~", "`", "+", "-", "=", "_"]
        if any([char for char in project_name if char in forbidden_characters]) or project_name == "":
            raise ValueError("project_name must be a string without spaces or special characters")
        
        self.variables = {}
        self.function_status = {}
        self.flow = {}
        self.messages = {'conversations': [], 'current_thread': Thread()}
        self.functions = []
        self.config = {}
        self.configfile = configparser.ConfigParser()
        if project_name is not None:
            self.config["project_name"] = project_name
        else:
            raise ValueError("project_name must be provided")
        if not os.path.exists(os.path.join(os.getcwd(), "config-files", f"{project_name}.ini")):
            raise FileNotFoundError(f"Configuration file for project {project_name} not found")
        self.clear()

    def clear(self):
        self.variables.clear()
        self.function_status.clear()
        self.messages = {'conversations': [], 'current_thread': Thread(), 'step': 0}
        self.functions = []
        self.flow.clear()
        self.flow['kill_state'] = False
        self.flow['current_state'] = self.flow.get('start_state')

        if os.path.exists(os.path.join(os.getcwd(), "config-files", f"{self.config["project_name"]}.ini")):
            self.configfile.read(os.path.join(os.getcwd(), "config-files", f"{self.config["project_name"]}.ini"))
            self.config["project_directory"] = self.configfile["Settings"]["project_directory"].replace("\"", "")
            self.config['memory_mode'] = self.configfile["Settings"]["memory_mode"].replace("\"", "")
            self.config['verbose'] = self.configfile["Settings"]["verbose"].replace("\"", "").lower() == "true"
            self.config['export_env'] = self.configfile["Settings"]["export_env"].replace("\"", "").lower() == "true"
            self.config['token_limit'] = int(self.configfile["Settings"]["token_limit"].replace("\"", ""))
            self.config["API_Keys"] = {}
            keys = self.configfile["API_Keys"] if self.configfile.has_section("API_Keys") else {}
            for name, env_var in API_KEY_ENV_VARS.items():
                value = keys.get(name, "").strip().strip("\"") or os.environ.get(env_var, "")
                self.config["API_Keys"][name] = value
            print("Configuration re-read successfully, all configuration variables have been reset.")
        else:
            raise FileNotFoundError("config.ini not found, unable to re-read configuration.")
        self.vdb = VectorDatabase(self.config["API_Keys"]["openai"], self.config["API_Keys"]["cohere"])

    def increment_step(self, message=None, sender=None, state=None, recipient=None, new_conversation=False, id=None):
        self.value = False
        if state:
            state = state.lower().replace(" ", "_")
        
        for function in self.function_status:
            if self.function_status.get(function) != "in progress":
                self.function_status[function] = False
        
        if new_conversation:
            new_thread = Thread(state=state)
            new_thread.add_message(Message(sender, recipient, message, state=state))
            self.messages['conversations'].append(new_thread)
            self.vdb.add_thread(new_thread)
        elif id is None:
            added_message = False
            thread = self.get_thread(state=state, members=[sender, recipient])
            if thread:
                if message is not None and Message(sender, recipient, message, state=state) != thread.messages[-1]:
                    thread.add_message(Message(sender, recipient, message, state=state))
                    added_message = True
                    self.vdb.add_message(Message(sender, recipient, message, state=state), thread_id=thread.id, state=state)
            if not added_message:
                new_thread = Thread(state=state)
                new_thread.add_message(Message(sender, recipient, message, state=state))
                self.messages['conversations'].append(new_thread)
                self.vdb.add_thread(new_thread)
        elif id is not None:
            added_message = False
            for conversation in self.messages['conversations']:
                if conversation.id == id:
                    conversation.add_message(Message(sender, recipient, message, state=state))
                    added_message = True
                    self.vdb.add_message(Message(sender, recipient, message, state=state), thread_id=conversation.id, state=state)
                    break
            if not added_message:
                new_thread = Thread(state=state)
                new_thread.add_message(Message(sender, recipient, message, state=state))
                self.messages['conversations'].append(new_thread)
                self.vdb.add_thread(new_thread)
        return True
    
    def get_thread(self, id=None, state=None, members=None):
        sorted_conversations = sorted(self.messages['conversations'], key=lambda x: x.last_message, reverse=True)
        
        if id is not None:
            for conversation in sorted_conversations:
                if conversation.id == id:
                    return conversation

        best_match = None
        best_match_score = 0

        for conversation in sorted_conversations:
            score = 0

            if state is not None and conversation.state == state:
                score += 2

            if members is not None:
                score += .5 * len([member for member in members if member in conversation.members])

            time_bonus = 0
            if conversation.last_message:
                time_bonus = 1 / (1 + (datetime.datetime.now() - conversation.last_message).seconds)
            score += time_bonus
        
            if score > best_match_score:
                best_match = conversation
                best_match_score = score

        return best_match if best_match else Thread()

    def get_agent_chat_history(self, agent):

        thread = Thread()
        for conversation in self.messages['conversations']:
            if agent in conversation.members:
                for message in conversation.messages:
                    if message.sender == agent or message.recipient == agent:
                        thread.add_message(message)
        thread.messages = sorted(thread.messages, key=lambda x: x.timestamp)
        return thread

    def get_variable_from_string(self, variable):
        #(env.variables['a']['b] = [1, 2, 3] -> a.b)
        variable = variable.split(".")
        value = self.variables
        for var in variable:
            value = value.get(var)
            if value is None:
                return None
        return value
    
    def set_variable_from_string(self, variable, value):
        variable = variable.split(".")
        if len(variable) == 1:
            self.variables[variable[0]] = value
        else:
            self.variables[variable[0]] = self.variables.get(variable[0], {})
            self.variables[variable[0]][variable[1]] = value
