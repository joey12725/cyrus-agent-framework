import streamlit as st
from streamlit_agraph import agraph, Node, Edge, Config
from streamlit_tags import st_tags
from cyrus import *
import asyncio
import json

def main():

    project_name = "dev"
    global env
    env = Environment.getInstance(project_name=project_name)

    list_of_agents = [x.split(".")[0] for x in os.listdir(os.path.join(env.config["project_directory"], "agents")) if x.endswith(".agent")]
    agents = {}
    for agent in list_of_agents:
        agents[agent] = asyncio.run(Agent.create(agent))


    list_of_functions = [x.split(".")[0] for x in os.listdir(os.path.join(env.config["project_directory"], "functions")) if x.endswith(".function")]

    flow = create_flow(list_of_agents, list_of_functions)

 # # Create the transitions
    # user_to_dm_transition = Transition(user_talks_to_dm_state, mm_talks_to_jeff_state, returns("rollDice", "*"), label="dm rolls dice")
    # dm_to_self_transition = Transition(mm_talks_to_jeff_state, print_completed_state, turn(3), label="3 turns of conversation")
    # test_transition = Transition(print_completed_state, user_talks_to_dm_state, returns("rollDice", "*"))
    # # Create the flow
    # flow = cFlow.getInstance([user_talks_to_dm_state, mm_talks_to_jeff_state, print_completed_state], user_talks_to_dm_state, [user_to_dm_transition, dm_to_self_transition, test_transition])

    # # Define nodes and edges for agraph visualization
    # visualize_flow(flow)

def visualize_flow(flow):
    nodes = []
    edges = []

    for state in flow.states:
        nodes.append(Node(id=state.name, 
                          label=state.name, 
                          size=50, 
                          shape="image", 
                          image=state.create_icon()))
        if state == flow.start_state:
            nodes.append(Node(id="start", 
                              label="Start", 
                              size=50, 
                              color="green",
                                shape="circle"))
            edges.append(Edge(source="start", 
                              target=state.name, 
                              label="Start"))
            

    for transition in flow.transitions:
        edges.append(Edge(source=transition.source.name, 
                          target=transition.destination.name, 
                          label=transition.label))

    # Define agraph config with more spacing between nodes
    config = Config(width=750,
                    height=950,
                    directed=True, 
                    physics=False, 
                    hierarchical=False,
                    )  # Increase node spacing

    # Display the graph using agraph
    return_value = agraph(nodes=nodes, edges=edges, config=config)
    return return_value



def create_transition(list_of_states, list_of_functions):    
    source = st.selectbox("Source", [x.name for x in list_of_states])
    destination = st.selectbox("Destination", [x.name for x in list_of_states])
    label = st.text_input("Label")
    condition_types = [
            "is_called",
            "returns",
            "turn",
            "in",
            "not_in_",
            "and_",
            "or_",
            "not_",
            "equals",
            "not_equals"
        ]
    
    condition_type = st.selectbox("Condition Type", condition_types)

    if condition_type == "is_called":
        function_name = st.selectbox("Function Name", list_of_functions)
        condition = is_called(function_name)
    
    elif condition_type == "returns":
        function_name = st.selectbox("Function Name", list_of_functions)
        value = st.text_input("Value")
        condition = returns(function_name, value)
    
    elif condition_type == "turn":
        turn_number = st.number_input("Turn Number", step=1, value=1)
        condition = turn(turn_number)
    
    elif condition_type == "in":
        value = st.text_input("Value")
        is_in_environment = st.selectbox("Is the list stored in the environment", ["Yes", "No"])
        if is_in_environment == "Yes":
            list_of_values = st.text_input("Enter the environment variable name (env.variables['a']['b] = [1, 2, 3] -> a.b)")
            list_of_values = env.get_variable_from_string(list_of_values)
        else:
            list_of_values = st_tags(label="",text="Enter the list of values")

        condition = in_(value, list_of_values)   
    
    elif condition_type == "not_in_":
        value = st.text_input("Value")
        is_in_environment = st.selectbox("Is the list stored in the environment", ["Yes", "No"])
        if is_in_environment == "Yes":
            list_of_values = st.text_input("Enter the environment variable name (env.variables['a']['b] = [1, 2, 3] -> a.b)")
            list_of_values = env.get_variable_from_string(list_of_values)
        else:
            list_of_values = st_tags(label="",text="Enter the list of values")

        condition = not_in_(value, list_of_values)

    elif condition_type == "and_":
        condition1 = st.text_input("Condition 1 (env.variables['a']['b] = True -> a.b)")
        condition2 = st.text_input("Condition 2")
        condition = and_(env.get_variable_from_string(condition1), env.get_variable_from_string(condition2))

    elif condition_type == "or_":
        condition1 = st.text_input("Condition 1 (env.variables['a']['b] = True -> a.b)")
        condition2 = st.text_input("Condition 2")
        condition = or_(env.get_variable_from_string(condition1), env.get_variable_from_string(condition2))
    
    elif condition_type == "not_":
        condition1 = st.text_input("Condition 1 (env.variables['a']['b] = True -> a.b)")
        condition = not_(env.get_variable_from_string(condition1))
    
    elif condition_type == "equals":
        value1 = st.text_input("Value 1 (env.variables['a']['b] = foo -> env.a.b)")
        value2 = st.text_input("Value 2")
        if 'env' in value1:
            value1 = env.get_variable_from_string(value1.replace("env.", ""))
        if 'env' in value2:
            value2 = env.get_variable_from_string(value2.replace("env.", ""))
        condition = equals(value1, value2)
    
    elif condition_type == "not_equals":
        value1 = st.text_input("Value 1 (env.variables['a']['b] = foo -> env.a.b)")
        value2 = st.text_input("Value 2")
        if 'env' in value1:
            value1 = env.get_variable_from_string(value1.replace("env.", ""))
        if 'env' in value2:
            value2 = env.get_variable_from_string(value2.replace("env.", ""))
        condition = not_equals(value1, value2)
        
    if st.button("Create Transition"):
        return Transition(source, destination, condition,label= label)

def create_action(list_of_agents, list_of_functions, list_of_states):
    valid_action_types = [
        "talks_to",
        "cot",
        "call",
        "println",
        "let",
        "loop",
        "go_to",
        "terminate"
    ]

    action_type = st.selectbox("Action Type", valid_action_types)

    if action_type == "talks_to":
        agent1 = st.selectbox("Agent", list_of_agents + ["user"], key="agent1")
        agent2 = st.selectbox("Agent", list_of_agents + ["user"], key="agent2")
        context = st.text_input("Context")
        until_checkbox = st.checkbox("Until condition")
        if until_checkbox:
            condition_types = [
                    "is_called",
                    "returns",
                    "turn",
                    "in",
                    "not_in_",
                    "and_",
                    "or_",
                    "not_",
                    "equals",
                    "not_equals"
                ]
            
            condition_type = st.selectbox("Condition Type", condition_types, key="condition_type_until_condition")

            if condition_type == "is_called":
                function_name = st.selectbox("Function Name", list_of_functions, key="function_name_is_called_until_condition")
                condition = is_called(function_name)
            
            elif condition_type == "returns":
                function_name = st.selectbox("Function Name", list_of_functions)
                value = st.text_input("Value", key="value_returns_until_condition")
                condition = returns(function_name, value)
            
            elif condition_type == "turn":
                turn_number = st.number_input("Turn Number", step=1, value=1, key="turn_number_until_condition")
                condition = turn(turn_number)
            
            elif condition_type == "in":
                value = st.text_input("Value")
                is_in_environment = st.selectbox("Is the list stored in the environment", ["Yes", "No"], key="is_in_environment_in_until_condition")
                if is_in_environment == "Yes":
                    list_of_values = st.text_input("Enter the environment variable name (env.variables['a']['b] = [1, 2, 3] -> a.b)", key="list_of_values_in_until_condition")
                    list_of_values = env.get_variable_from_string(list_of_values)
                else:
                    list_of_values = st_tags(label="",text="Enter the list of values")

                condition = in_(value, list_of_values)   
            
            elif condition_type == "not_in_":
                value = st.text_input("Value")
                is_in_environment = st.selectbox("Is the list stored in the environment", ["Yes", "No"], key="is_in_environment_not_in_until_condition")
                if is_in_environment == "Yes":
                    list_of_values = st.text_input("Enter the environment variable name (env.variables['a']['b] = [1, 2, 3] -> a.b)",   key="list_of_values_not_in_until_condition")
                    list_of_values = env.get_variable_from_string(list_of_values)
                else:
                    list_of_values = st_tags(label="",text="Enter the list of values")

                condition = not_in_(value, list_of_values)

            elif condition_type == "and_":
                condition1 = st.text_input("Condition 1 (env.variables['a']['b] = True -> a.b)", key="condition1_and_until_condition")
                condition2 = st.text_input("Condition 2", key="condition2_and_until_condition")
                condition = and_(env.get_variable_from_string(condition1), env.get_variable_from_string(condition2))

            elif condition_type == "or_":
                condition1 = st.text_input("Condition 1 (env.variables['a']['b] = True -> a.b)", key="condition1_or_until_condition")
                condition2 = st.text_input("Condition 2", key="condition2_or_until_condition")
                condition = or_(env.get_variable_from_string(condition1), env.get_variable_from_string(condition2))
            
            elif condition_type == "not_":
                condition1 = st.text_input("Condition 1 (env.variables['a']['b] = True -> a.b)", key="condition1_not_until_condition")
                condition = not_(env.get_variable_from_string(condition1))
            
            elif condition_type == "equals":
                value1 = st.text_input("Value 1 (env.variables['a']['b] = foo -> env.a.b)", key="value1_equals_until_condition")
                value2 = st.text_input("Value 2")
                if 'env' in value1:
                    value1 = env.get_variable_from_string(value1.replace("env.", ""))
                if 'env' in value2:
                    value2 = env.get_variable_from_string(value2.replace("env.", ""))
                condition = equals(value1, value2)
            
            elif condition_type == "not_equals":
                value1 = st.text_input("Value 1 (env.variables['a']['b] = foo -> env.a.b)")
                value2 = st.text_input("Value 2")
                if 'env' in value1:
                    value1 = env.get_variable_from_string(value1.replace("env.", ""))
                if 'env' in value2:
                    value2 = env.get_variable_from_string(value2.replace("env.", ""))
                condition = not_equals(value1, value2)
        if not until_checkbox:
            condition = False
        ret = talks_to(agent1, agent2, context, condition, until=condition)
    
    elif action_type == "cot":
        agent = st.selectbox("Agent", list_of_agents)
        context = st.text_input("Context")
        prompts = st_tags(label="",text="Prompts")
        ret = cot(agent, context, prompts=prompts)
    
    elif action_type == "call":
        function_name = st.selectbox("Function Name", list_of_functions)
        function_definition = json.load(open(os.path.join(env.config["project_directory"], "functions", f"{function_name}.function")))
        parameters = list(function_definition["parameters"]["properties"].keys())
        kwargs = {}
        for parameter in parameters:
            value = st.text_input(parameter)
            kwargs[parameter] = value
        ret = call(function_name, kwargs)
    
    elif action_type == "println":
        message = st.text_input("Message")
        ret = println(message)
    
    elif action_type == "let":
        variable_name = st.text_input("Variable Name (env.variables['a']['b'] = foo -> a.b)")
        value = st.text_input("Value")
        ret = let(variable_name, value)
    
    elif action_type == "loop":
        st.write("I don't feel like implementing this right now.")
    
    elif action_type == "go_to":
        state_name = st.selectbox("State", [x.name for x in list_of_states])
        ret = go_to(state_name)
    
    elif action_type == "terminate":
        ret = terminate()
    
    if st.button("Create Action"):
        return ret
    
def create_state(list_of_agents, list_of_functions, list_of_states):
    state_name = st.text_input("State Name")
    actions = []

    if 'actions' not in st.session_state:
        st.session_state.actions = []

    add_action = st.button("Add Action")

    if add_action:
        st.session_state.actions.append(None)

    for i, action in enumerate(st.session_state.actions):
        st.write(f"Action {i+1}")
        created_action = create_action(list_of_agents, list_of_functions, list_of_states)
        if created_action:
            st.session_state.actions[i] = created_action
        
        if st.button(f"Remove Action {i+1}"):
            st.session_state.actions.pop(i)
            break

    if st.button("Create State"):
        if st.session_state.actions:
            state = State(state_name, st.session_state.actions)
            st.session_state.actions = []  # Reset actions after state creation
            return state
        else:
            st.warning("Please add at least one action.")



def create_flow(list_of_agents, list_of_functions):
    if 'states' not in st.session_state:
        st.session_state.states = []

    if 'transitions' not in st.session_state:
        st.session_state.transitions = []

    st.header("Manage States")
    add_state = st.button("Add State")

    if add_state:
        st.session_state.states.append(None)

    for i, state in enumerate(st.session_state.states):
        st.write(f"State {i+1}")
        created_state = create_state(list_of_agents, list_of_functions, st.session_state.states)
        if created_state:
            st.session_state.states[i] = created_state
        
        if st.button(f"Remove State {i+1}"):
            st.session_state.states.pop(i)
            break

    state_options = [state.name for state in st.session_state.states if state]
    if state_options:
        st.header("Manage Transitions")
        start_state = st.selectbox("Start State", state_options)

        add_transition = st.button("Add Transition")
        if add_transition:
            st.session_state.transitions.append(None)

        for i, transition in enumerate(st.session_state.transitions):
            st.write(f"Transition {i+1}")
            created_transition = create_transition(st.session_state.states, list_of_functions)
            if created_transition:
                st.session_state.transitions[i] = created_transition
            
            if st.button(f"Remove Transition {i+1}"):
                st.session_state.transitions.pop(i)
                break

        if st.button("Create Flow"):
            selected_state_objects = [state for state in st.session_state.states if state]
            start_state_object = next(state for state in selected_state_objects if state.name == start_state)
            if selected_state_objects and st.session_state.transitions:
                flow = cFlow(selected_state_objects, start_state_object, st.session_state.transitions)
                st.session_state.states = []  # Reset states after flow creation
                st.session_state.transitions = []  # Reset transitions after flow creation
                return flow
            else:
                st.warning("Please create states and transitions.")
    else:
        st.warning("Please create at least one state.")

if __name__ == "__main__":
    main()