from cyrus import *

#create a flow where the dm talks to the user until it rolls a die, then the dm talks to itself until 5 turns have passed then prints "completed flow"

#create the agents
dm = Agent.create("dm")
env = Environment.getInstance()

#Create the actions
user_talks_to_dm = talks_to(dm, "user", context="Start by asking the user to describe their charecter, then, create an appropriate combat encounter and roll initative for them and the monster(s)")
#previous_conversation = str(env.messages.conversations[0])
dm_talks_to_self = talks_to(dm, "self", context="THIS IS A TEST. START BY JUST SAYING 'COUNT 1', THEN, THE NEXT TO SPEAK WILL SAY 'COUNT 2', THE THIRD, 'COUNT 3', AND SO ON.") 
print_completed = println("Completed flow")

#Create the states
user_talks_to_dm_state = State("user_talks_to_dm", [user_talks_to_dm])
dm_talks_to_self_state = State("dm_talks_to_self", [dm_talks_to_self])
print_completed_state = State("print_completed", [print_completed])

#Create the transitions
user_to_dm_transition = Transition(user_talks_to_dm_state, dm_talks_to_self_state, returns("rollDice", "*"))
dm_to_self_transition = Transition(dm_talks_to_self_state, print_completed_state, turn(3))

#create the flow
flow = cFlow.getInstance([user_talks_to_dm_state, dm_talks_to_self_state, print_completed_state], user_talks_to_dm_state, [user_to_dm_transition, dm_to_self_transition])
print("Running flow...")
flow.run()
