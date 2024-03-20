from cyrus import *
import random

env = Environment.getInstance()
agent = Agent.create("dm")

#action = talks_to("user", agent, context="Three goblins, armed with scimitars and shortbows, lurk in the camp; they have 7 HP each, AC 15, and can deal 1d6+2 slashing or piercing damage per attack.")    
action = talks_to(agent, "self", context="Whoever talks first is the dungeon master. Set the scene for the player to inhabit. The (whoever speaks second) will then explain their charecter and begin playing. Remember, you are not both the DM and the player, you will assume the role of either the DM or the player. Remember to use your dice and include combat.")
#action = println("Hello World")
action.run()

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