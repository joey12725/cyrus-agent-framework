import random



def GetNRandomNumbers(number_of_random_numbers=10, lower_bound=0, upper_bound=100):

    return str([random.randint(int(lower_bound), int(upper_bound)) for _ in range(int(number_of_random_numbers))])

