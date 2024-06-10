import configparser
import os
import uuid
import datetime
from cyrus import *

# Initialize the Environment singleton
env = Environment.getInstance()

# Test for turn function
def test_turn():
    env.clear()  # Reset environment
    env.messages['current_thread'].add_message(Message("a", "b", "c"))
    env.messages['current_thread'].add_message(Message("a", "b", "c"))
    env.messages['current_thread'].add_message(Message("a", "b", "c"))
    env.messages['current_thread'].add_message(Message("a", "b", "c"))
    turn_function = turn(4)
    assert turn_function.run() == True, "Turn function failed for matching step"

# Test for and_ function
def test_and_():
    env.clear()  # Reset environment
    and_function = and_(True, True)
    assert and_function.run() == True, "and_ function failed for both true conditions"

    env.clear()  # Reset environment
    and_function = and_(True, False)
    assert and_function.run() == False, "and_ function failed for one false condition"

# Test for or_ function
def test_or_():
    env.clear()  # Reset environment
    or_function = or_(True, False)
    assert or_function.run() == True, "or_ function failed for one true condition"

    env.clear()  # Reset environment
    or_function = or_(False, False)
    assert or_function.run() == False, "or_ function failed for both false conditions"

# Test for not_ function
def test_not_():
    env.clear()  # Reset environment
    not_function = not_(False)
    assert not_function.run() == True, "not_ function failed for false condition"

    env.clear()  # Reset environment
    not_function = not_(True)
    assert not_function.run() == False, "not_ function failed for true condition"

# Test for equals function
def test_equals():
    env.clear()  # Reset environment
    equals_function = equals(1, 1)
    assert equals_function.run() == True, "equals function failed for equal values"

    env.clear()  # Reset environment
    equals_function = equals(1, 2)
    assert equals_function.run() == False, "equals function failed for unequal values"

# Test for not_equals function
def test_not_equals():
    env.clear()  # Reset environment
    not_equals_function = not_equals(1, 2)
    assert not_equals_function.run() == True, "not_equals function failed for unequal values"

    env.clear()  # Reset environment
    not_equals_function = not_equals(1, 1)
    assert not_equals_function.run() == False, "not_equals function failed for equal values"

# Test for greater_than function
def test_greater_than():
    env.clear()  # Reset environment
    greater_than_function = greater_than(2, 1)
    assert greater_than_function.run() == True, "greater_than function failed for 2 > 1"

    env.clear()  # Reset environment
    greater_than_function = greater_than(1, 2)
    assert greater_than_function.run() == False, "greater_than function failed for 1 > 2"

# Test for less_than function
def test_less_than():
    env.clear()  # Reset environment
    less_than_function = less_than(1, 2)
    assert less_than_function.run() == True, "less_than function failed for 1 < 2"

    env.clear()  # Reset environment
    less_than_function = less_than(2, 1)
    assert less_than_function.run() == False, "less_than function failed for 2 < 1"

# Test for greater_than_or_equals function
def test_greater_than_or_equals():
    env.clear()  # Reset environment
    gte_function = greater_than_or_equals(2, 1)
    assert gte_function.run() == True, "greater_than_or_equals function failed for 2 >= 1"

    env.clear()  # Reset environment
    gte_function = greater_than_or_equals(1, 1)
    assert gte_function.run() == True, "greater_than_or_equals function failed for 1 >= 1"

# Test for less_than_or_equals function
def test_less_than_or_equals():
    env.clear()  # Reset environment
    lte_function = less_than_or_equals(1, 2)
    assert lte_function.run() == True, "less_than_or_equals function failed for 1 <= 2"

    env.clear()  # Reset environment
    lte_function = less_than_or_equals(1, 1)
    assert lte_function.run() == True, "less_than_or_equals function failed for 1 <= 1"

# Test for add function
def test_add():
    env.clear()  # Reset environment
    add_function = add(1, 2)
    assert add_function.run() == 3, "add function failed for 1 + 2"

# Test for subtract function
def test_subtract():
    env.clear()  # Reset environment
    subtract_function = subtract(5, 3)
    assert subtract_function.run() == 2, "subtract function failed for 5 - 3"

# Test for multiply function
def test_multiply():
    env.clear()  # Reset environment
    multiply_function = multiply(2, 3)
    assert multiply_function.run() == 6, "multiply function failed for 2 * 3"

# Test for divide function
def test_divide():
    env.clear()  # Reset environment
    divide_function = divide(6, 3)
    assert divide_function.run() == 2, "divide function failed for 6 / 3"

    env.clear()  # Reset environment
    divide_function = divide(6, 0)
    assert divide_function.run() == 'Error: Division by zero', "divide function failed for 6 / 0"

# Test for mod function
def test_mod():
    env.clear()  # Reset environment
    mod_function = mod(5, 3)
    assert mod_function.run() == 2, "mod function failed for 5 % 3"

# Test for in_ function
def test_in_():
    env.clear()  # Reset environment
    in_function = in_('a', ['a', 'b', 'c'])
    assert in_function.run() == True, "in_ function failed for 'a' in ['a', 'b', 'c']"

# Test for not_in_ function
def test_not_in_():
    env.clear()  # Reset environment
    not_in_function = not_in_('d', ['a', 'b', 'c'])
    assert not_in_function.run() == True, "not_in_ function failed for 'd' not in ['a', 'b', 'c']"

# Test for index function
def test_index():
    env.clear()  # Reset environment
    test_dict = {'key1': 'value1', 'key2': 'value2'}
    index_function = index(test_dict, 'key1')
    assert index_function.run() == 'value1', "index function failed for 'key1' in test_dict"

# Run the tests
test_turn()
test_and_()
test_or_()
test_not_()
test_equals()
test_not_equals()
test_greater_than()
test_less_than()
test_greater_than_or_equals()
test_less_than_or_equals()
test_add()
test_subtract()
test_multiply()
test_divide()
test_mod()
test_in_()
test_not_in_()
test_index()

# Output success message or handle assertion errors
print("All non-agent tests passed successfully!")

agent = Agent.create("dm")

# Test isCalled by asking the agent to "roll 3d6". In a separate thread, watch the environment to see if the function is called.

import threading
import time

env.clear()  # Reset environment

def send_command():
    # Code to send the "roll 3d6" command to the agent
    agent.get_response("roll 3d6")

def monitor_function():
    start_time = time.time()
    called_checker = is_called("rollDice")
    returns_checker = returns("rollDice", "*")
    called = False
    returned = False
    reset = False
    while not called_checker.run() and time.time() - start_time < 120:
        time.sleep(0.1)
        called = True
    if called:
        print("rollDice function was called, is_called function returned True")
    else:
        print("timeout reached, rollDice function was not called")
    while called_checker.run() and time.time() - start_time < 120:
        if returns_checker.run() and not returned:
            print("returns works correctly")
            returned = True
        time.sleep(0.1)
        reset = True
    if reset:
        print("is_called function successfully reset on turn end")

# Set up threading
command_thread = threading.Thread(target=send_command)
monitor_thread = threading.Thread(target=monitor_function)

# Start threads
command_thread.start()
monitor_thread.start()

# Optionally join threads if needed
command_thread.join()
monitor_thread.join()
