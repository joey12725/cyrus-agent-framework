import random
def GetNRandomNumbers(number_of_random_numbers=10, lower_bound=0, upper_bound=100):
    return [random.randint(lower_bound, upper_bound) for _ in range(number_of_random_numbers)]