from cyrus import *

#create a flow where the dm talks to the user until it rolls a die, then the dm talks to itself until 5 turns have passed then prints "completed flow"

#create the agents
dm = Agent("dm")
env = Environment.getInstance()

#Create the actions
user_talks_to_dm = talks_to(dm, "user", context="Start by asking the user to describe their charecter, then, create an appropriate combat encounter and roll initative for them and the monster(s)")
#previous_conversation = str(env.messages.conversations[0])
dm_talks_to_self = talks_to(dm, "self", context="The first of you to talk will be the player charecter, taking over the charecter of the previous pc, whoever speaks second will play the DM") 
print_completed = println("Completed flow")

#Create the states
user_talks_to_dm_state = State("user_talks_to_dm", [user_talks_to_dm])
dm_talks_to_self_state = State("dm_talks_to_self", [dm_talks_to_self])
print_completed_state = State("print_completed", [print_completed])

#Create the transitions
user_to_dm_transition = Transition(user_talks_to_dm_state, dm_talks_to_self_state, returns("rollDice", "*"))
dm_to_self_transition = Transition(dm_talks_to_self_state, print_completed_state, turn(5))

#create the flow
flow = cFlow.getInstance([user_talks_to_dm_state, dm_talks_to_self_state, print_completed_state], user_talks_to_dm_state, [user_to_dm_transition, dm_to_self_transition])
print("Running flow...")
flow.run()