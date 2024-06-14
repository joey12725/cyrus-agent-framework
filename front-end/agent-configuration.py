import streamlit as st
from streamlit_chat import message
import json
from cyrus import *
import asyncio
import os

#before loading the rest of the code, we need to set the project name from a dropdown
#the options are any .ini files in os.getcwd() with the .ini removed
project_name = st.selectbox("Select Project", [f[:-4] for f in os.listdir(os.path.join(os.getcwd(), "config-files")) if f.endswith(".ini")])

global env
env = Environment.getInstance(project_name=project_name)

# Define models to platforms mapping
models_to_platforms = {
    "amazon.titan-text-express-v1": "bedrock",
    "amazon.titan-text-lite-v1": "bedrock",
    "amazon.titan-text-premier-v1:0": "bedrock",
    "anthropic.claude-v2": "bedrock",
    "anthropic.claude-v2:1": "bedrock",
    "anthropic.claude-3-sonnet-20240229-v1:0": "bedrock",
    "anthropic.claude-3-haiku-20240307-v1:0": "bedrock",
    "anthropic.claude-3-opus-20240229-v1:0": "bedrock",
    "anthropic.claude-instant-v1": "bedrock",
    "cohere.command-r-v1:0": "bedrock",
    "cohere.command-r-plus-v1:0": "bedrock",
    "meta.llama2-13b-chat-v1": "bedrock",
    "meta.llama2-70b-chat-v1": "bedrock",
    "mistral.mistral-7b-instruct-v0:2": "bedrock",
    "mistral.mixtral-8x7b-instruct-v0:1": "bedrock",
    "mistral.mistral-large-2402-v1:0": "bedrock",
    "mistral.mistral-small-2402-v1:0": "bedrock",
    "ai21.j2-mid-v1": "bedrock",
    "ai21.j2-ultra-v1": "bedrock",
    "llama-3-sonar-small-32k-chat": "perplexity",
    "llama-3-sonar-small-32k-online": "perplexity",
    "llama-3-sonar-large-32k-chat": "perplexity",
    "llama-3-sonar-large-32k-online": "perplexity",
    "llama-3-8b-instruct": "perplexity",
    "llama-3-70b-instruct": "perplexity",
    "mixtral-8x7b-instruct": "perplexity",
    "gpt-4o": "openai",
    "gpt-4o-2024-05-13": "openai",
    "gpt-4-turbo": "openai",
    "gpt-4-turbo-2024-04-09": "openai",
    "gpt-4-turbo-preview": "openai",
    "gpt-4-0125-preview": "openai",
    "gpt-4-1106-preview": "openai",
    "gpt-4-vision-preview": "openai",
    "gpt-4-1106-vision-preview": "openai",
    "gpt-4": "openai",
    "gpt-4-0613": "openai",
    "gpt-4-32k": "openai",
    "gpt-4-32k-0613": "openai",
    "gpt-3.5-turbo-0125": "openai",
    "gpt-3.5-turbo": "openai",
    "gpt-3.5-turbo-1106": "openai",
    "gpt-3.5-turbo-instruct": "openai",
    "gpt-3.5-turbo-16k": "openai",
    "gpt-3.5-turbo-0613": "openai",
    "gpt-3.5-turbo-16k-0613": "openai"
}

# Default values
default_system_prompt = "system prompt here..."
#default_profile_picture = r"resources\profile_images\372a4505-c031-455d-ab1a-91091159b749.jpg"
fallback_profile_picture = os.path.join(os.getcwd(), "resources", "default", "default-pfp.webp")  # Replace with your fallback image path

# Paths
path_to_functions = os.path.join(env.config["project_directory"], "functions")
path_to_documents = os.path.join(env.config["project_directory"], "documents")
path_to_agents = os.path.join(env.config["project_directory"], "agents")

# Load available functions and documents
available_functions = [f[:-9] for f in os.listdir(path_to_functions) if f.endswith(".function")]
available_documents = list(os.listdir(path_to_documents))

# Load agents from files
def load_agents():
    agents = []
    for file_name in os.listdir(path_to_agents):
        if file_name.endswith(".agent"):
            try:
                with open(os.path.join(path_to_agents, file_name), "r") as file:
                    agent = json.load(file)
                    agents.append(agent)
            except json.JSONDecodeError as e:
                st.error(f"Error loading {file_name}: {e}")
    return agents

# Initialize session state
if "agents" not in st.session_state:
    st.session_state.agents = load_agents()
if "selected_agent" not in st.session_state:
    st.session_state.selected_agent = 0
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# Selected agent details
selected_agent = st.session_state.agents[st.session_state.selected_agent]

# Display profile picture at the top of the page
if "profile_picture" in selected_agent: 
    profile_picture_path = os.path.join(os.getcwd(), "resources", "profile_images", selected_agent["profile_picture"]) if os.path.exists(os.path.join(os.getcwd(), "resources", "profile_images", selected_agent["profile_picture"]) ) else fallback_profile_picture
else:
    profile_picture_path = os.path.join(os.getcwd(), "resources", "profile_images", random.choice(os.listdir(os.path.join(os.getcwd(), "resources", "profile_images"))))
st.image(profile_picture_path, width=100)

# Sidebar for agents
st.sidebar.title("Agents")
for i, agent in enumerate(st.session_state.agents):
    if st.sidebar.button(agent["name"], key=i):
        st.session_state.selected_agent = i
        selected_agent = st.session_state.agents[i]

# Add new agent
if st.sidebar.button("Add New Agent"):
    new_agent = {
        "name": "New Agent",
        "role": "",
        "model": list(models_to_platforms.keys())[0],
        "system_prompt": "",
        "profile_picture": os.path.join(os.getcwd(), "resources", "profile_images", random.choice(os.listdir(os.path.join(os.getcwd(), "resources", "profile_images")))),
        "functions": [],
        "documents": [],
        "use_rerank_documents": False,
        "use_memory": False,
        "use_rerank_memory": False
    }
    st.session_state.agents.append(new_agent)
    st.session_state.selected_agent = len(st.session_state.agents) - 1
    selected_agent = new_agent

# Agent Info Form
with st.form("agent_form"):
    name = st.text_input("Name", value=selected_agent["name"])
    role = st.text_input("Role", value=selected_agent["role"])
    model = st.selectbox("Model", models_to_platforms.keys(), index=list(models_to_platforms.keys()).index(selected_agent["model"]))
    system_prompt = st.text_area("System Prompt", value=selected_agent["system_prompt"])

    functions = st.multiselect("Functions", available_functions, default=selected_agent["functions"])
    # Ensure default documents are in the available documents
    valid_default_documents = [doc for doc in selected_agent["documents"] if doc in available_documents]
    documents = st.multiselect("Documents", available_documents, default=valid_default_documents)
    use_rerank_documents = st.checkbox("Use Cohere Rerank for improved document search", value="rerank" in selected_agent.get("functions", []))
    use_memory = st.checkbox("Use Retrieval Augmented Memory", value="memory" in selected_agent.get("functions", []))
    if use_memory
        use_rerank_memory = st.checkbox("Use Cohere Rerank for improved memory search", value="rerank_memory" in selected_agent.get("functions", []))
    else:
        use_rerank_memory = False

    submitted = st.form_submit_button("Save Configuration")

if submitted:
    selected_agent.update({
        "platform": models_to_platforms[model],
        "name": name,
        "role": role,
        "model": model,
        "system_prompt": system_prompt,
        "functions": functions,
        "documents": documents,
        "profile_picture": selected_agent.get("profile_picture", random.choice(os.listdir(os.path.join(os.getcwd(), "resources", "profile_images"))))
        "use_rerank_documents": use_rerank_documents,
        "use_memory": use_memory,
        "use_rerank_memory": use_rerank_memory
    })

    with open(os.path.join(path_to_agents, name + ".agent"), "w") as file:
        json.dump(selected_agent, file, indent=4)
    
    agent_demo = asyncio.run(Agent.create(name))
    st.success("Configuration saved!")

# Chat interface
st.title("Test Agent Interaction")

if "past" not in st.session_state:
    st.session_state.past = []
if "generated" not in st.session_state:
    st.session_state.generated = []

def on_input_change():
    user_input = st.session_state.user_input
    st.session_state.past.append(user_input)
    st.session_state.generated.append(asyncio.run(agent_demo.get_response(user_input)))
    st.session_state.user_input = ""

with st.container():
    for i in range(len(st.session_state.generated)):
        message(st.session_state.past[i], is_user=True, key=f"{i}_user", avatar_style="adventurer", seed="Felix")
        message(st.session_state.generated[i], key=f"{i}_response")

    st.text_input("Your message:", key="user_input", on_change=on_input_change)
