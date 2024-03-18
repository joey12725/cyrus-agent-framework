import os
import configparser
from cyrus import *
from rich.console import Console
from rich.markdown import Markdown

global env
env = Environment.getInstance()
console = Console()

def render_markdown(text):
    """Render Markdown text to the terminal."""
    markdown = Markdown(text)
    console.print(markdown)

def vprint(*args):
    if env.config.verbose:
        #if args is blank, print a newline
        if args == ():
            print()
        else:
            render_markdown(" ".join(args))