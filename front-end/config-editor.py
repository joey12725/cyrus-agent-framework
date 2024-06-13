import streamlit as st
import os
import configparser

api_keys = {}
loaded_keys = []


def replace_last_n_lines(source_path, target_path, n=6):
    # Read the source file and get the last n lines
    with open(source_path, 'r') as source_file:
        source_lines = source_file.readlines()
        last_n_source_lines = source_lines[-n:]
    
    # Read the target file
    with open(target_path, 'r') as target_file:
        target_lines = target_file.readlines()
    
    # Replace the last n lines of the target file with the last n lines of the source file
    target_lines = target_lines[:-n] + last_n_source_lines
    
    # Write the modified lines back to the target file
    with open(target_path, 'w') as target_file:
        target_file.writelines(target_lines)

# Function to load ini file
def load_ini_file(file_path):
    config = configparser.ConfigParser()
    config.read(file_path)
    return config

# Function to save ini file
def save_ini_file(config, file_path):
    with open(file_path, 'w') as configfile:
        config.write(configfile)

# Function to create project directories
def create_project_directories(project_directory):
    directories = ['documents', 'functions', 'agents']
    for dir_name in directories:
        os.makedirs(os.path.join(project_directory, dir_name), exist_ok=True)

# Function to load API keys from another INI file
def load_api_keys_from_file(file_path):
    config = load_ini_file(file_path)
    if 'API_Keys' in config:
        st.success(dict(config['API_Keys']))
        return config['API_Keys']
    st.error('No API keys found in ' + file_path)
    return None

# Streamlit UI
st.title('INI File Editor and Project Manager')

st.sidebar.header('Options')
option = st.sidebar.selectbox('Choose an option', ('Edit Existing Project', 'Create New Project'))

if option == 'Edit Existing Project':
    ini_files = [f for f in os.listdir() if f.endswith('.ini')]
    selected_file = st.sidebar.selectbox('Select an INI file', ini_files)
    if selected_file:
        config = load_ini_file(selected_file)

        st.header('Edit INI File')

        project_directory = st.text_input('Project Directory', config['Settings']['project_directory'])
        memory_mode = st.text_input('Memory Mode', config['Settings']['memory_mode'])
        token_limit = st.number_input('Token Limit', value=int(config['Settings']['token_limit']))
        verbose = st.checkbox('Verbose', value=config['Settings'].getboolean('verbose'))
        export_env = st.checkbox('Export Env', value=config['Settings'].getboolean('export_env'))

        openai_key = st.text_input('OpenAI Key', config['API_Keys']['openai'])
        perplexity_key = st.text_input('Perplexity Key', config['API_Keys']['perplexity'])
        aws_access_key_id = st.text_input('AWS Access Key ID', config['API_Keys']['aws_access_key_id'])
        aws_secret_access_key = st.text_input('AWS Secret Access Key', config['API_Keys']['aws_secret_access_key'])
        cohere_key = st.text_input('Cohere Key', config['API_Keys']['cohere'])
        
        if st.button('Save Changes'):
            config['Settings']['project_directory'] = project_directory
            config['Settings']['memory_mode'] = memory_mode
            config['Settings']['token_limit'] = str(token_limit)
            config['Settings']['verbose'] = str(verbose)
            config['Settings']['export_env'] = str(export_env)

            if "openai" not in loaded_keys and openai_key != config['API_Keys']['openai'] and openai_key != '':
                config['API_Keys']['openai'] = openai_key 
            if "perplexity" not in loaded_keys and perplexity_key != config['API_Keys']['perplexity'] and perplexity_key != '':
                config['API_Keys']['perplexity'] = perplexity_key
            if "aws_access_key_id" not in loaded_keys and aws_access_key_id != config['API_Keys']['aws_access_key_id'] and aws_access_key_id != '':
                config['API_Keys']['aws_access_key_id'] = aws_access_key_id
            if "aws_secret_access_key" not in loaded_keys and aws_secret_access_key != config['API_Keys']['aws_secret_access_key'] and aws_secret_access_key != '':
                config['API_Keys']['aws_secret_access_key'] = aws_secret_access_key
            if "cohere" not in loaded_keys and cohere_key != config['API_Keys']['cohere'] and cohere_key != '':
                config['API_Keys']['cohere'] = cohere_key

            save_ini_file(config, selected_file)
            create_project_directories(project_directory)
            st.success('INI file updated and project directories created.')

        st.subheader('Load API Keys from Another Project')
        load_keys_file = st.selectbox('Select an INI file to load API keys from', ini_files)
        if st.button('Load API Keys'):
            if load_keys_file:
                api_keys = dict(load_api_keys_from_file(load_keys_file))
                if api_keys:
                    for key in api_keys:
                        config['API_Keys'][key] = api_keys[key]
                        loaded_keys.append(key)
                    st.success('API keys loaded from ' + load_keys_file)
                    replace_last_n_lines(os.path.join(os.getcwd(), load_keys_file), os.path.join(os.getcwd(), selected_file))

elif option == 'Create New Project':
    st.header('Create New Project')

    new_file_name = st.text_input('INI File Name', 'new_project.ini')
    project_directory = st.text_input('Project Directory', '')
    memory_mode = st.text_input('Memory Mode', 'ephemeral')
    token_limit = st.number_input('Token Limit', value=100000)
    verbose = st.checkbox('Verbose', value=True)
    export_env = st.checkbox('Export Env', value=False)

    openai_key = st.text_input('OpenAI Key', '')
    perplexity_key = st.text_input('Perplexity Key', '')
    aws_access_key_id = st.text_input('AWS Access Key ID', '')
    aws_secret_access_key = st.text_input('AWS Secret Access Key', '')
    cohere_key = st.text_input('Cohere Key', '')

    st.subheader('Load API Keys from Another Project')
    ini_files = [f for f in os.listdir() if f.endswith('.ini')]
    load_keys_file = st.selectbox('Select an INI file to load API keys from', ini_files)
    if st.button('Load API Keys'):
        if load_keys_file:
            api_keys = load_api_keys_from_file(load_keys_file)
            if api_keys:
                for key in api_keys:
                    st.session_state[key] = api_keys[key]
                openai_key = st.session_state.get('openai', openai_key)
                perplexity_key = st.session_state.get('perplexity', perplexity_key)
                aws_access_key_id = st.session_state.get('aws_access_key_id', aws_access_key_id)
                aws_secret_access_key = st.session_state.get('aws_secret_access_key', aws_secret_access_key)
                cohere_key = st.session_state.get('cohere', cohere_key)
                st.success('API keys loaded from ' + load_keys_file)

    if st.button('Create Project'):
        config = configparser.ConfigParser()
        config['Settings'] = {
            'project_directory': project_directory,
            'memory_mode': memory_mode,
            'token_limit': str(token_limit),
            'verbose': str(verbose),
            'export_env': str(export_env)
        }

        config['API_Keys'] = {
            'openai': openai_key,
            'perplexity': perplexity_key,
            'aws_access_key_id': aws_access_key_id,
            'aws_secret_access_key': aws_secret_access_key,
            'cohere': cohere_key
        }

        save_ini_file(config, new_file_name)
        create_project_directories(project_directory)
        st.success(f'Project {new_file_name} created and directories initialized.')
