import os
import configparser
from cyrus import *
from rich.console import Console
from rich.markdown import Markdown
from openai import OpenAI
import os
from time import sleep
import configparser



global env
console = Console()


def render_markdown(text):
    """Render Markdown text to the terminal."""
    markdown = Markdown(text)
    console.print(markdown)

def vprint(*args):
    env = Environment.getInstance()
    if env.config["verbose"]:
        #if args is blank, print a newline
        if args == ():
            print()
        else:
            render_markdown(" ".join([str(arg) for arg in args]))

def open_ai_cleanup():
    #delete all agents
    env = Environment.getInstance()
    client = OpenAI(api_key=env.config["API_Keys"]["openai"])
    for i in range(100):
        try:
            assistants = client.beta.assistants.list(limit=100)
            print(len(assistants.data), "assistants found")
            for assistant in assistants:
                try:
                    client.beta.assistants.delete(assistant.id)
                    print("deleting assistant", assistant.id)
                except Exception as e:
                    print("unable to delete assistant", assistant.id)
                    print(str(e)[:100])
        except:
            pass

def remove_all(text, remove):
    for r in remove:
        text = text.replace(r, "")
    return text

def replace_all(text, dic):
    for i, j in dic.items():
        text = text.replace(i, j)
    return text