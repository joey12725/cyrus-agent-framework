from setuptools import setup, find_packages

setup(
    name='cyrus',
    version='0.0.1',
    packages=find_packages(include=['cyrus', 'cyrus.*']),
    description='Orchestrate agent swarms',
    author='Joey Hersh',
    url='https://github.com/joey12725/cyrus-agent-framework',
    license='MIT',
    python_requires='>=3.12',
    install_requires=[
        'openai>=1.30,<2',
        'boto3>=1.34.120,<2',
        'chromadb>=0.5,<0.6',
        'cohere>=5.5,<6',
        'rich>=13',
        'pillow>=10',
        'base256>=1.0',
    ],
    extras_require={
        'gui': [
            'streamlit>=1.35,<2',
            'streamlit-ace',
            'streamlit-agraph',
            'streamlit-chat',
            'streamlit-tags',
        ],
    },
)
