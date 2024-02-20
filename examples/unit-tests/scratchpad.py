from cyrus import *

env = Environment.getInstance()
agent = Agent("agents/dm.agent")
action = talks_to("user", agent, context="Three goblins, armed with scimitars and shortbows, lurk in the camp; they have 7 HP each, AC 15, and can deal 1d6+2 slashing or piercing damage per attack.")
action.run()