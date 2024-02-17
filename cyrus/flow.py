class cflow():

    class state():
        class action():
            pass
            """
            valid actions: 
                talks to (2 agents or 1 agent and user, optional: context)
                reflects (one agent, optional: context)
                call (fuction, args)
                let (variable name, value)
                print (message)
                loop (list, varname, actions)
                if (condition, actions)
                go_to (state, optional: context)
                terminate ()
            """
        
        class function(): 
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
        
        def check_transitions(self, transition):
            pass
        
        def check_if_statements(self, if_actions):
            pass

        def run_actions(self, action):
            pass
        
    class transition():
        def __init__(self, source, destination, condition):
            self.source = source
            self.destination = destination
            self.condition = condition

    def __init__(self, states, start_state, environment):
        self.states = states
        self.start_state = start_state
        self.current_state = start_state
        self.environment = environment

    def run_transition(self, transition):
        pass
    
    def terminate(self):
        pass

    def show():
        pass