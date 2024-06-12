from cyrus import *
import random
import asyncio
async def main():
    env = Environment.getInstance()
    agent = await Agent.create("dm-llama")

    action = talks_to("user", agent, context="Help the player come up with a characeter.")    
    #action = talks_to(agent, "self", context="Trade dnd theamed roasts/joking insults with the user. This is not a game of dnd, just some relaxing humor. This is not in charecter. Responses should be short and quippy.")
    #action = println("Hello World")
    await action.run()

"""
agent.get_response("write a christmas strory about 3 goblins gifting the spoils of their raids")
action = reflect(agent)
action.run()
print(agent.get_response("What changes did you make?"))
"""

#print(call("rollDice", {"diceCount":8, "sidesPerDie": 6, "additionalSum": 4}).run())

#let("x.y.z.a.b.c", 5).run()
#env.variables.show()

#loop([1,2,3], "x", [println("hello world"), println("goodbye world")]).run()


#go_to("1").run()
#print(env.current_state)

"""
env.variables.x.y.z.a = 5
env.variables.x.y.z.b = 5
env.variables.x.y.z.c = 5
env.variables.x.y.z.d = 5
env.variables.x.y.z.e = 5


env.variables.show()

env.clear()

print("cleared enviroment")

env.variables.show()
"""

asyncio.run(main())
