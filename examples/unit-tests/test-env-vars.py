from cyrus import Agent, Action, talks_to, Environment

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


#test modifyung messages.step (ensuring that the singleton is working properly)

env.messages.step = 1

t1 = (env.messages.step == env2.messages.step == env3.messages.step == env4.messages.step == env5.messages.step == 1)

env3.messages.step = 2

t2 = (env.messages.step == env2.messages.step == env3.messages.step == env4.messages.step == env5.messages.step == 2)

if all([t1, t2]):
    print("singleton passed")
else:
    print("singleton failed")

