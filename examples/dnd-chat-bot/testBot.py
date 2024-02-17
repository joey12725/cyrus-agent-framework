from cyrus import Agent

dm = Agent(r"agents/dm.agent")

while True:
    user_input = input("You: ")
    if user_input == "quit":
        dm.terminate()
        break
    print(f"DM: {dm.get_response(user_input)}")
