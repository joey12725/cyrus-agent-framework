import configparser
import os
import uuid
from types import SimpleNamespace
import datetime

class DynamicAttrDict:
    def __getattr__(self, name):
        if name not in self.__dict__:
            # Only create a new DynamicAttrDict if the attribute doesn't exist
            self.__dict__[name] = DynamicAttrDict()
        return self.__dict__[name]
    def __setattr__(self, name, value):
        self.__dict__[name] = value

    def __delattr__(self, name):
        if name in self.__dict__:
            del self.__dict__[name]

    def __contains__(self, name):
        return name in self.__dict__

    def __iter__(self):
        return iter(self.__dict__)

    def __bool__(self):
        return bool(self.__dict__)
    
    def __str__(self, indent=0):
        result = []
        for key, value in self.__dict__.items():
            if isinstance(value, DynamicAttrDict):
                result.append('  ' * indent + str(key))
                result.append(value.__str__(indent + 1))
            else:
                result.append('  ' * indent + f'{key}: {value}')
        return '\n'.join(result)
    
    def show(self, indent=1):
        for key, value in self.__dict__.items():
            if isinstance(value, DynamicAttrDict):
                print('  ' * indent + str(key))
                value.show(indent + 1)
            else:
                print('  ' * indent + f'{key}: {value}')

    def set_value(self, name, value):
        self.__dict__[name] = value

    def get_index(self, name):
        if name not in self.__dict__:
            self.__dict__[name] = DynamicAttrDict()
        return self.__dict__[name]
class Message:
    def __init__(self, sender, recipient, message):
        self.sender = sender
        self.recipient = recipient
        self.content = message
        self.id = uuid.uuid4()
        self.timestamp = datetime.datetime.now()
    #equality is based on the sender, recipient, and content of the message
    def __eq__(self, other):
        return self.sender == other.sender and self.recipient == other.recipient and self.content == other.content
class Thread:
# class to manage conversation threads for llms
    def __init__(self):
        self.messages = []
        self.members = []
        self.state=None
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
        self.env.messages.current_thread = self
        
    def turn(self):
        return len(self.messages)
    
    def __str__(self):
        return f"Thread with members: {self.members} and messages: {[f"Sender: {message.sender}, Recipient: {message.recipient}, Content: {message.content}" for message in self.messages]}"
    
    def dump(self, token_saver=False, charecter_limit=0):
        ret = []
        if not token_saver:
            for message in self.messages:
                ret.append(f"{message.sender} -> {message.recipient}: {message.content}")
        elif token_saver and not charecter_limit:
            for message in self.messages:
                ret.append(f"{message.sender}: {message.content}")
        elif token_saver and charecter_limit:
            chars = 0
            for message in self.messages:
                chars += len(message.content)
                if chars <= charecter_limit:
                    ret.append(f"{message.sender}: {message.content}")
                else:
                    break
        return "\n".join(ret)
                
class Environment:

    _instance = None

    @staticmethod
    def getInstance():
        if Environment._instance == None:
            Environment()
        return Environment._instance

    def __init__(self):
        if Environment._instance != None:
            raise Exception("This class is a singleton!")
        else:
            Environment._instance = self
        self.variables = DynamicAttrDict()
        self.function_status = DynamicAttrDict()
        self.flow = DynamicAttrDict()
        self.messages = DynamicAttrDict()
        self.messages.conversations = []
        self.messages.current_thread = Thread()
        self.functions = []
        if os.path.exists(os.path.join(os.getcwd(), "config.ini")):
            self.configfile = configparser.ConfigParser()
            self.configfile.read(os.path.join(os.getcwd(), "config.ini"))
            self.config = DynamicAttrDict()
            self.config.memory_mode = self.configfile["Settings"]["memory_mode"].replace("\"","")
            self.config.verbose = True if self.configfile["Settings"]["verbose"].replace("\"","").lower() == "true" else False
            self.export_env = True if self.configfile["Settings"]["export_env"].replace("\"","") == "true" or self.config["Settings"]["export_env"].replace("\"","") == "True" else False
            self.config.token_limit = int(self.configfile["Settings"]["token_limit"].replace("\"",""))
        else:
            raise(Exception("config.ini not found"))
        print("conversations", self.messages.conversations)
    def clear(self):
        # Explicitly clear or reset all managed attributes
        self.variables = DynamicAttrDict()
        self.function_status = DynamicAttrDict()
        self.messages = DynamicAttrDict()
        self.messages.conversations = []
        self.messages.current_thread = Thread()
        self.functions = []
        self.flow = DynamicAttrDict()
        self.flow.kill_state = False
        self.flow.current_state = self.flow.start_state
        #if self.functions exists
        if hasattr(self, 'functions'):
            for function in self.functions:
                self.function_status.set_value(function, False)
        
        # Re-read configuration if necessary
        if os.path.exists(os.path.join(os.getcwd(), "config.ini")):
            self.configfile.read(os.path.join(os.getcwd(), "config.ini"))
            self.config.memory_mode = self.configfile["Settings"]["memory_mode"].replace("\"","")
            self.config.verbose = True if self.configfile["Settings"]["verbose"].replace("\"","") == "true" or self.config["Settings"]["verbose"].replace("\"","") == "True" else False
            self.export_env = True if self.configfile["Settings"]["export_env"].replace("\"","") == "true" or self.config["Settings"]["export_env"].replace("\"","") == "True" else False
            self.config.token_limit = int(self.configfile["Settings"]["token_limit"].replace("\"",""))
        else:
            print("config.ini not found, unable to re-read configuration.")


        # Clear any user-added attributes by iterating over __dict__
        # Be cautious to not remove essential attributes
        essential_attrs = {'_instance', 'variables', 'function_status', 'messages', 'functions', 'configfile', 'config'}
        user_attrs = [attr for attr in self.__dict__ if attr not in essential_attrs]
        for attr in user_attrs:
            delattr(self, attr)

        # Reset step count if it's specifically managed
        if hasattr(self, 'messages') and hasattr(self.messages, 'step'):
            self.messages.step = 0

        # Ensure _instance is updated to reflect the reset state
        Environment._instance = self



    def __str__(self):
        print(self.name, self.value)

    def increment_step(self, message=None, sender=None, state = None, recipient=None, new_conversation=False, id=None):
        self.value = False
        if state:
            state = state.lower().replace(" ", "_")
        for function in self.function_status:
            if self.function_status.get_index(function) != "in progress":
                self.function_status.set_value(function, False)
        if new_conversation:
            self.messages.conversations.append(Thread())
            self.messages.conversations[-1].state = state
            self.messages.conversations[-1].add_message(Message(sender, recipient, message))
            added_message = True
        elif id==None:
            added_message = False
            thread = self.get_thread(state=state, members=[sender, recipient])
            if thread:
                if message is not None and Message(sender, recipient, message) != thread.messages[-1]:
                    thread.add_message(Message(sender, recipient, message))
                    added_message = True
            else:
                self.messages.conversations.append(Thread())
                self.messages.conversations[-1].state = state
                self.messages.conversations[-1].add_message(Message(sender, recipient, message))
                added_message = True
        elif id!=None:
            for conversation in self.messages.conversations:
                if conversation.id == id:
                    conversation.add_message(Message(sender, recipient, message))
                    added_message = True
                    break
            if not added_message:
                self.messages.conversations.append(Thread())
                self.messages.conversations[-1].add_message(Message(sender, recipient, message))
                added_message = True
        return True
    
    def get_thread(self, id=None, state=None, members=None):
        # Sort the conversations by last_message attribute (descending order)
        sorted_conversations = sorted(self.messages.conversations, key=lambda x: x.last_message, reverse=True)
        
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
                score += .5*len([member for member in members if member in conversation.members])

            time_bonus = 0
            if conversation.last_message:
                time_bonus = 1 / (1+(datetime.datetime.now() - conversation.last_message).seconds)
            score += time_bonus
        
            if score > best_match_score:
                best_match = conversation
                best_match_score = score

        return best_match if best_match else Thread()

    def get_agent_chat_history(self, agent):
        #creates a new thread with the agent and every message that the agent has sent or recieved in the order that they were sent
        thread = Thread()
        for conversation in self.messages.conversations:
            if agent in conversation.members:
                for message in conversation.messages:
                    if message.sender == agent or message.recipient == agent:
                        thread.add_message(message)
        #sort the messages by timestamp
        thread.messages = sorted(thread.messages, key=lambda x: x.timestamp)
        return thread
    