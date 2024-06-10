import random

def rollDice(diceCount=1, sidesPerDie=6, additionalSum=0):
    return str(sum([random.randint(1, sidesPerDie) for _ in range(diceCount)]) + additionalSum)