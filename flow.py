class cflow():
    #this class is made up of states
    #the flow is non-deterministic (each state can have multiple transitions)
    #each state transition has a source, a destination, and a condition
    #each transition is a tuple (source, destination, condition) where source and destination are states and condition is a function returning a boolean
    #each state has a name and a list of transitions
    #the flow has a start state, current state, and enviroment (a dictionary of variables).
    #the flow has a method to check if the current state has any valid transitions and to move to the next state
    #CURRENTLY JUST DEFINING THE CLASS, NOT IMPLEMENTING IT

    class state():
        def __init__(self, name, transitions):
            self.name = name
            self.transitions = transitions
        
    class transition():
        def __init__(self, source, destination, condition):
            self.source = source
            self.destination = destination
            self.condition = condition
    
    class environment():
        def __init__(self):
            self.value = ""
            self .message.


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