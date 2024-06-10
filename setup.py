import os
from setuptools import setup, find_packages

setup(
    name='cyrus',
    version='0.0.1',
    packages=find_packages(),
    description='Orchestrate agent swarms',
    author='Joey Hersh',
    author_email='joeyandpaige@gmail.com',
    url='https://github.com/joey12725/cyrus-agent-framework',
    install_requires=[
        'openai',
        'networkx',
        'matplotlib',
    ],
)

#set api key eviroment variable
os.environ["OPENAI_API_KEY"] = "REDACTED_OPENAI_KEY"
