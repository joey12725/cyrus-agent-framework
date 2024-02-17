from cyrus import Agent, Enviroment
import os 
import configparser
class cflow():

    class state():
        class action():
            class user_conversation():
                def __init__(self, agent, context=""):
                    #load "memory-mode" from config.ini
                    if self.config["memory-mode"] == "ephemeral":
                        self.agents[agent].terminate()
                        self.agents[agent] = Agent(os.path.join(os.getcwd(), "agents", agent + ".agent"))

                def step_conversation(self, agent, context=""):
                    if self.env.step == 0 and context != "":
                        user_input = "CONTEXT: " + str(context) + "\n USER: " input("User: ")
                    else:
                        user_input = input("User: ")
                    response = self.agents[agent].get_response(user_input)
                    print(f"{agent}: {response}")
                    self.env.step += 1
                    self.check_transitions()
                    self.check_if_statements()
                    return self.step_conversation(agent)

                
            class agent_conversation():
                def __init__(self, agent1, agent2, context=""):
                    self.agent1 = agent1
                    self.agent2 = agent2
                    self.context = context
            class reflect():
                def __init__(self, agent, context=""):
                    self.agent = agent
                    self.context = context
            class call():
                def __init__(self, function, args):
                    self.function = function
                    self.args = args
            class let():
                def __init__(self, variable, value):
                    self.variable = variable
                    self.value = value   
            class println():
                def __init__(self, message):
                    self.message = message  
            class loop():
                def __init__(self, list, varname, actions):
                    self.list = list
                    self.varname = varname
                    self.actions = actions
            class if_statement():
                def __init__(self, condition, actions):
                    self.condition = condition
                    self.actions = actions
            class go_to():
                def __init__(self, state, context=""):
                    self.state = state
                    self.context = context
            class terminate():
                def __init__(self):
                    pass
            

        class function(): 
            class generate():
                def __init__(self, model, prompt):
                    self.model = model
                    self.prompt = prompt
            class predict():
                def __init__(self, model, data):
                    self.model = model
                    self.data = data
            class is_called():
                def __init__(self, function):
                    self.function = function
            class returns():
                def __init__(self, function, value):
                    self.function = function
                    self.value = value
            class turn():
                def __init__(self, turn):
                    self.turn = turn
            class and_():
                def __init__(self, condition, condition):
                    self.condition = condition
            class or_():
                def __init__(self, condition, condition):
                    self.condition = condition
            class not_():
                def __init__(self, condition):
                    self.condition = condition
            class equals():
                def __init__(self, value, value):
                    self.value = value
            class not_equals():
                def __init__(self, value, value):
                    self.value = value
            class greater_than():
                def __init__(self, value, value):
                    self.value = value
            class less_than():
                def __init__(self, value, value):
                    self.value = value
            class greater_than_or_equals():
                def __init__(self, value, value):
                    self.value = value
            class less_than_or_equals():
                def __init__(self, value, value):
                    self.value = value
            class add():
                def __init__(self, value, value):
                    self.value = value
            class subtract():
                def __init__(self, value, value):
                    self.value = value
            class multiply():
                def __init__(self, value, value):
                    self.value = value
            class divide():
                def __init__(self, value, value):
                    self.value = value
            class mod():
                def __init__(self, value, value):
                    self.value = value
            class in_():
                def __init__(self, value, list):
                    self.value = value
                    self.list = list
            class not_in_():
                def __init__(self, value, list):
                    self.value = value
                    self.list = list
            class index():
                def __init__(self, dict, key):
                    self.dict = dict
                    self.key = key
            
            """
            valid functions:
                generate (model, prompt)
                predict (model, data)
                is_called (function)
                returns (function, value)
                turn (int)
                and (condition, condition)
                or (condition, condition)
                not (condition)
                == (value, value)
                != (value, value)
                > (value, value)
                < (value, value)
                >= (value, value)
                <= (value, value)
                + (value, value)
                - (value, value)
                * (value, value)
                / (value, value)
                % (value, value)
                in (value, list or string)
                not_in (value, list or string)
                . (dict, key)


            """


        def __init__(self, name, transitions, actions):
            self.name = name
            self.transitions = transitions
        
        def get_agents(self):
            #get all the agents in actions in the state and sets self.agent[role] = Agent(os.path.join(os.getcwd(), "agents", agent + ".agent"))
            self.agents = {}

        def check_transitions(self):
            pass
        
        def check_if_statements(self):
            pass

        def run_actions(self, action):
            pass
        
    class transition():
        def __init__(self, source, destination, condition):
            self.source = source
            self.destination = destination
            self.condition = condition

    def __init__(self, states, start_state):
        self.states = states
        self.start_state = start_state
        self.current_state = start_state
        self.env = Environment()
        config = configparser.ConfigParser()
        config.read(os.path.join(os.getcwd(), "config.ini"))

    def run(self):
        pass

    def run_transition(self, transition):
        pass
    
    def terminate(self):
        pass

    def validate_config_file(self, config_file):
        pass

    def show():
        pass