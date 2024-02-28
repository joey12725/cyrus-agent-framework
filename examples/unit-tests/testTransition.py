from cyrus import *
import random

state1 = State("state1", [], [println("Hello World")])
state2 = State("state2", [], [println("Hello World")])

def rand_bool():
    return random.choice([True, False])

transition = Transition(state1, state2, rand_bool)

for i in range(10):
    print(transition.check())

transition = Transition(state1, state2, True)

for i in range(10):
    print(transition.check())

