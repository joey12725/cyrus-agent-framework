from cyrus import Agent, Action, talks_to, Environment, Thread, Message


env = Environment.getInstance()
env2 = Environment.getInstance()
env3 = Environment.getInstance()
env4 = Environment.getInstance()
env5 = Environment.getInstance()

#test setting variables with . 
env.variables.name = "test"
env.variables.role = 3.5
env.variables.system_prompt = 3
env.variables.ind1.ind2 = "hello world"


t1 = (env.variables.name == "test")
t2 = (env.variables.role == 3.5)
t3 = (env.variables.system_prompt == 3)
t4 = (env.variables.ind1.ind2 == "hello world")

if all([t1, t2, t3, t4]):
    print("setting variables with . passed")
else:
    if not t1:
        print("setting variables with . failed for name")
    if not t2:
        print("setting variables with . failed for role")
    if not t3:
        print("setting variables with . failed for system_prompt")
    if not t4:
        print("setting variables with . failed for ind1.ind2")
#test setting variables with  set_value

foo = "bar"
env.variables.ind1.set_value(foo, "bar")

t1 = (env.variables.ind1.bar == "bar")

if t1:
    print("setting variables with set_value passed")
else:
    print("setting variables with set_value failed")

#test setting variables with get_index

foo = "bar"
env.variables.get_index(foo).new_value = "bar"

t1 = (env.variables.bar.new_value == "bar")

if t1:
    print("setting variables with get_index passed")
else:
    print("setting variables with get_index failed")
#test show method

print("show method:")
env.variables.show()


#test __str__ method

print("str method:")
print(env.variables.__str__())


#test __contains__ method

t1 = ("name" in env.variables)
t2 = ("role" in env.variables)
t3 = ("system_prompt" in env.variables)
t4 = ("ind1" in env.variables)


if all([t1, t2, t3, t4]):
    print("contains method passed for top level")
else:
    print("contains method failed for top level")


#test __iter__ method

t1 = ("name" in env.variables)
t2 = ("ind1" in env.variables)
t3 = ("ind2" in env.variables.ind1)
t4 = (len([x for x in env.variables]) == 4)
t5 = (len([x for x in env.variables.ind1]) == 1)

if all([t1, t2, t3, t4, t5]):
    print("iter method passed")
else:
    if not t1:
        print("iter method failed for top level")
    if not t2:
        print("iter method failed for ind1")
    if not t3:
        print("iter method failed for ind2")


#test __bool__ method

t1 = (bool(env.variables))
t2 = (bool(env.variables.ind1.unused_index))

if all([t1, not t2]):
    print("bool method passed")
else:
    if not t1:
        print("bool method failed for top level")
    if t2:
        print("bool method failed for unused index")


#test __delattr__ method

del env.variables.name

t1 = ("name" not in env.variables)

#test callable objects stored in variables

def test_callable():
    env.variables.callable = lambda: True
    t1 = env.variables.callable()
    assert t1
    print("test_callable passed")
    env.variables.callable2 = ["hello", "world"]
    env.variables.callable2.append("!")
    assert env.variables.callable2 == ["hello", "world", "!"]
test_callable()

#test threads and messages

def test_thread_creation():
    thread = Thread()
    assert thread.id is not None
    assert thread.creation_time is not None
    assert thread.last_message is not None
    assert thread.members == []
    assert thread.messages == []
    print("test_thread_creation passed")

def test_add_message():
    thread = Thread()
    message1 = Message("Alice", "Bob", "Hello, Bob!")
    message2 = Message("Bob", "Alice", "Hi, Alice!")

    thread.add_message(message1)
    assert thread.members == ["Alice", "Bob"]
    assert thread.messages == [message1]
    assert thread.speaks_first == "Alice"
    assert thread.last_message == message1.timestamp

    thread.add_message(message2)
    assert thread.members == ["Alice", "Bob"]
    assert thread.messages == [message1, message2]
    assert thread.speaks_first == "Alice"
    assert thread.last_message == message2.timestamp
    print("test_add_message passed")

def test_message_creation():
    message = Message("Alice", "Bob", "Hello, Bob!")
    assert message.sender == "Alice"
    assert message.recipient == "Bob"
    assert message.content == "Hello, Bob!"
    assert message.id is not None
    assert message.timestamp is not None
    print("test_message_creation passed")

def test_thread_str():
    thread = Thread()
    message1 = Message("Alice", "Bob", "Hello, Bob!")
    message2 = Message("Bob", "Alice", "Hi, Alice!")
    thread.add_message(message1)
    thread.add_message(message2)

    
    print(thread)

def test_thread_dump():
    thread = Thread()
    message1 = Message("Alice", "Bob", "Hello, Bob!")
    message2 = Message("Bob", "Alice", "Hi, Alice!")
    thread.add_message(message1)
    thread.add_message(message2)
    print(thread)
    print(thread.dump())
    print(thread.dump(token_saver=True))

# Run the tests
test_thread_creation()
test_add_message()
test_message_creation()
test_thread_str()
test_thread_dump()

print(env.messages.conversations)
print(type(env.messages.conversations))
env.messages.conversations.append(Thread())
print(env.messages.conversations)
def test_increment_step():
    env = Environment.getInstance()
    env.clear()  # Clear the environment before running the test

    # Test incrementing step with a new conversation
    print(env.messages.conversations)
    print(type(env.messages.conversations))
    env.increment_step(message="Hello, Alice!", sender="Bob", recipient="Alice", new_conversation=True)
    print("len of conversation should be 1, is ", len(env.messages.conversations))
    print(env.messages.conversations)
    assert len(env.messages.conversations) == 1
    assert len(env.messages.conversations[0].messages) == 1
    assert env.messages.conversations[0].messages[0].content == "Hello, Alice!"

    # Test incrementing step with an existing conversation
    env.increment_step(message="Hi, Bob!", sender="Alice", recipient="Bob")
    print("len of conversation should be 2, is ", len(env.messages.conversations))
    print([x.messages for x in env.messages.conversations])
    assert len(env.messages.conversations) == 1
    assert len(env.messages.conversations[0].messages) == 2
    assert env.messages.conversations[0].messages[1].content == "Hi, Bob!"

    # Test incrementing step with a specific conversation ID
    conversation_id = env.messages.conversations[0].id
    env.increment_step(message="How are you?", sender="Bob", recipient="Alice", id=conversation_id)
    assert len(env.messages.conversations) == 1
    assert len(env.messages.conversations[0].messages) == 3
    assert env.messages.conversations[0].messages[2].content == "How are you?"

    # Test incrementing step with a new conversation between different participants
    env.increment_step(message="Hello, Eve!", sender="Alice", recipient="Eve", new_conversation=True)
    assert len(env.messages.conversations) == 2
    assert len(env.messages.conversations[1].messages) == 1
    assert env.messages.conversations[1].messages[0].content == "Hello, Eve!"

    print("test_increment_step passed")

# Run the test
test_increment_step()