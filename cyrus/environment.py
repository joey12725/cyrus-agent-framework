import configparser
import os
import uuid
import datetime

import uuid
import datetime
import os

class File:
    def __init__(self, extension, content=None, directory=None):
        self.extension = extension.replace(".", "")
        if directory is not None:
            self.load_from_directory(directory)
        elif content is not None:
            self.content = content
        else:
            raise ValueError("Either content or directory must be provided")

    def load_from_directory(self, directory):
        try:
            with open(directory, 'rb') as file:
                self.content = file.read()
        except Exception as e:
            raise IOError(f"Error loading file from directory: {e}")

class Message:
    def __init__(self, sender, recipient, message, files=None):
        if files is None:
            files = []
        if type(files) != list:
            raise ValueError("Files must be a list of File objects")
        self.sender = sender
        self.recipient = recipient
        self.content = message
        self.id = uuid.uuid4()
        self.files = files
        self.timestamp = datetime.datetime.now()
    
    def __eq__(self, other):
        return self.sender == other.sender and self.recipient == other.recipient and self.content == other.content

class Thread:
    def __init__(self):
        self.messages = []
        self.members = []
        self.state = None
        self.id = uuid.uuid4()
        self.creation_time = datetime.datetime.now()
        self.last_message = datetime.datetime.now()
        self.env = Environment.getInstance()

    def add_message(self, message):
        if message.sender not in self.members:
            self.members.append(message.sender)
        if message.recipient not in self.members:
            self.members.append(message.recipient)
        if len(self.messages) == 0:
            self.speaks_first = message.sender
        self.last_message = message.timestamp
        self.messages.append(message)
        self.env.messages['current_thread'] = self
        
    def turn(self):
        return len(self.messages)
    
    def __str__(self):
        return f"Thread with members: {self.members} and messages: {[f'Sender: {message.sender}, Recipient: {message.recipient}, Content: {message.content}' for message in self.messages]}"
    
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
    def getInstance():
        if Environment._instance is None:
            Environment()
        return Environment._instance

    def __init__(self):
        if Environment._instance is not None:
            raise Exception("This class is a singleton!")
        else:
            Environment._instance = self
        
        self.variables = {}
        self.function_status = {}
        self.flow = {}
        self.messages = {'conversations': [], 'current_thread': Thread()}
        self.functions = []
        self.config = {}
        self.configfile = configparser.ConfigParser()
        
        if not os.path.exists(os.path.join(os.getcwd(), "config.ini")):
            raise Exception("config.ini not found")
        
        self.clear()

    def clear(self):
        self.variables.clear()
        self.function_status.clear()
        self.messages = {'conversations': [], 'current_thread': Thread(), 'step': 0}
        self.functions = []
        self.flow.clear()
        self.flow['kill_state'] = False
        self.flow['current_state'] = self.flow.get('start_state')

        if os.path.exists(os.path.join(os.getcwd(), "config.ini")):
            self.configfile.read(os.path.join(os.getcwd(), "config.ini"))
            self.config['memory_mode'] = self.configfile["Settings"]["memory_mode"].replace("\"", "")
            self.config['verbose'] = self.configfile["Settings"]["verbose"].replace("\"", "").lower() == "true"
            self.config['export_env'] = self.configfile["Settings"]["export_env"].replace("\"", "").lower() == "true"
            self.config['token_limit'] = int(self.configfile["Settings"]["token_limit"].replace("\"", ""))
        else:
            print("config.ini not found, unable to re-read configuration.")

    def increment_step(self, message=None, sender=None, state=None, recipient=None, new_conversation=False, id=None):
        self.value = False
        if state:
            state = state.lower().replace(" ", "_")
        
        for function in self.function_status:
            if self.function_status.get(function) != "in progress":
                self.function_status[function] = False
        
        if new_conversation:
            new_thread = Thread()
            new_thread.state = state
            new_thread.add_message(Message(sender, recipient, message))
            self.messages['conversations'].append(new_thread)
        elif id is None:
            added_message = False
            thread = self.get_thread(state=state, members=[sender, recipient])
            if thread:
                if message is not None and Message(sender, recipient, message) != thread.messages[-1]:
                    thread.add_message(Message(sender, recipient, message))
                    added_message = True
            if not added_message:
                new_thread = Thread()
                new_thread.state = state
                new_thread.add_message(Message(sender, recipient, message))
                self.messages['conversations'].append(new_thread)
        elif id is not None:
            added_message = False
            for conversation in self.messages['conversations']:
                if conversation.id == id:
                    conversation.add_message(Message(sender, recipient, message))
                    added_message = True
                    break
            if not added_message:
                new_thread = Thread()
                new_thread.add_message(Message(sender, recipient, message))
                self.messages['conversations'].append(new_thread)
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
