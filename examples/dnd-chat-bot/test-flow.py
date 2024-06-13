from cyrus import *
import asyncio

async def main():
    # Create the agent asynchronously
    dm = await Agent.create("dm-haiku")
    env = Environment.getInstance()

    # Create the actions
    user_talks_to_dm = talks_to(dm, "user", context="Start by asking the user to describe their character, then create an appropriate combat encounter and roll initiative for them and the monster(s)")
    dm_talks_to_self = talks_to(dm, "self", context="THIS IS A TEST. START BY JUST SAYING 'COUNT 1', THEN, THE NEXT TO SPEAK WILL SAY 'COUNT 2', THE THIRD, 'COUNT 3', AND SO ON.") 
    print_completed = println("Completed flow")

    # Create the states
    user_talks_to_dm_state = State("user_talks_to_dm", [user_talks_to_dm])
    dm_talks_to_self_state = State("dm_talks_to_self", [dm_talks_to_self])
    print_completed_state = State("print_completed", [print_completed])

    # Create the transitions
    user_to_dm_transition = Transition(user_talks_to_dm_state, dm_talks_to_self_state, returns("rollDice", "*"))
    dm_to_self_transition = Transition(dm_talks_to_self_state, print_completed_state, turn(3))

    # Create the flow
    flow = cFlow.getInstance([user_talks_to_dm_state, dm_talks_to_self_state, print_completed_state], user_talks_to_dm_state, [user_to_dm_transition, dm_to_self_transition])

    print("Running flow...")
    await flow.run()

# Run the main function using asyncio
asyncio.run(main())
