import streamlit as st
from streamlit_ace import st_ace
import json
import os
import uuid
import time
from cyrus import Environment

project_name = st.selectbox("Select Project", [f[:-4] for f in os.listdir(os.path.join(os.getcwd(), "config-files")) if f.endswith(".ini")])

global env
env = Environment.getInstance(project_name=project_name)

project_directory = env.config["project_directory"]

# Helper function to load function configurations from a file
def load_function_config(file_path):
    with open(file_path, 'r') as file:
        return json.load(file)

# Helper function to save function configurations to a file
def save_function_config(file_path, config):
    with open(file_path, 'w') as file:
        json.dump(config, file, indent=4)

# Helper function to save function code to a Python file
def save_function_code(file_path, code):
    with open(file_path, 'w') as file:
        file.write(code)

# Function to generate repeating field group for parameters
def generate_repeating_field_group(keys, group_id, default_values=None):
    if f"rows_{group_id}" not in st.session_state:
        st.session_state[f"rows_{group_id}"] = []

    rows_collection = []

    def add_row():
        element_id = uuid.uuid4()
        st.session_state[f"rows_{group_id}"].append(str(element_id))

    def remove_row(row_id):
        st.session_state[f"rows_{group_id}"].remove(str(row_id))

    def generate_row(row_id, defaults=None):
        row_container = st.container()
        row_columns = row_container.columns((2, 1, 1))
        field_group = {}

        for key, value in keys.items():
            field_type = value["type"]
            default_value = defaults[key] if defaults and key in defaults else value["default"]

            if field_type == int:
                field_group[key] = row_columns[0].number_input(key, value=int(default_value), step=1, key=f"{key}_{row_id}_{group_id}")
            elif field_type == float:
                field_group[key] = row_columns[0].number_input(key, value=float(default_value), format="%.2f", key=f"{key}_{row_id}_{group_id}")
            elif field_type == str:
                field_group[key] = row_columns[0].text_input(key, value=str(default_value), key=f"{key}_{row_id}_{group_id}")
            elif field_type == "date":
                field_group[key] = row_columns[0].date_input(key, value=datetime.date.fromisoformat(default_value) if isinstance(default_value, str) else default_value, key=f"{key}_{row_id}_{group_id}")
            elif field_type == "paragraph":
                field_group[key] = row_columns[0].text_area(key, value=str(default_value), key=f"{key}_{row_id}_{group_id}")
            elif field_type == "choice":
                choices = value["choices"]
                field_group[key] = row_columns[0].selectbox(key, options=choices, index=choices.index(default_value), key=f"{key}_{row_id}_{group_id}")
            else:
                raise ValueError(f"Invalid field type: {field_type}")

        required = row_columns[1].checkbox("Required", key=f"required_{row_id}_{group_id}", value=defaults.get("required", False) if defaults else False)
        field_group["required"] = required
        row_columns[2].button("🗑️", key=f"del_{row_id}_{group_id}", on_click=remove_row, args=[row_id])
        return field_group

    menu = st.columns(2)
    with menu[0]:
        st.button("Add Item", on_click=add_row, key=f"add_item_{group_id}")

    for row in st.session_state[f"rows_{group_id}"]:
        defaults = None
        if default_values and row in default_values:
            defaults = default_values[row]
        row_data = generate_row(row, defaults)
        rows_collection.append(row_data)

    return rows_collection

# Streamlit UI
st.title('Function Configuration Manager')

# Sidebar for function selection or creation
st.sidebar.header('Functions')
functions_dir = os.path.join(project_directory, 'functions')
os.makedirs(functions_dir, exist_ok=True)
function_files = [f for f in os.listdir(functions_dir) if f.endswith('.function')]
selected_file = st.sidebar.selectbox('Select a Function', ['Create New Function'] + function_files)

# Function details
if selected_file == 'Create New Function':
    st.header('Create New Function')
    function_name = st.text_input('Function Name')
    function_description = st.text_area('Function Description')
    dependencies = st.text_area('Dependencies (comma-separated)', value="requests")

    parameters = generate_repeating_field_group({
        "name": {"type": str, "default": ""},
        "type": {"type": "choice", "choices": ["string", "integer", "number", "boolean", "array"], "default": "string"},
        "description": {"type": str, "default": ""}
    }, "parameters")
else:
    st.header('Edit Function')
    function_config = load_function_config(os.path.join(functions_dir, selected_file))
    function_name = st.text_input('Function Name', value=function_config['name'])
    function_description = st.text_area('Function Description', value=function_config['description'])
    dependencies = st.text_area('Dependencies (comma-separated)', value=", ".join(function_config.get('dependencies', [])))

    parameters = generate_repeating_field_group({
        "name": {"type": str, "default": ""},
        "type": {"type": "choice", "choices": ["string", "integer", "number", "boolean", "array"], "default": "string"},
        "description": {"type": str, "default": ""}
    }, "parameters", default_values=function_config.get('parameters', {}))
    
# Function code editor
st.header('Function Code Editor')
function_code = st_ace(language='python')

# Save function details
if st.button('Save Function'):
    if not function_name:
        st.error("Function name cannot be empty.")
    else:
        function_config = {
            "name": function_name,
            "dependencies": [dep.strip() for dep in dependencies.split(",")],
            "description": function_description,
            "parameters": {
                "type": "object",
                "properties": {param["name"]: {"type": param["type"], "description": param["description"]} for param in parameters},
                "required": [param["name"] for param in parameters if param["required"]]
            },
            "id": str(uuid.uuid4())
        }
        save_function_config(os.path.join(functions_dir, f"{function_name}.function"), function_config)
        save_function_code(os.path.join(functions_dir, f"{function_name}.py"), function_code)
        st.success('Function saved successfully!')
