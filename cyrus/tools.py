from cyrus.environment import Environment
from rich.console import Console
from rich.markdown import Markdown

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

def remove_all(text, remove):
    for r in remove:
        text = text.replace(r, "")
    return text

def replace_all(text, dic):
    for i, j in dic.items():
        text = text.replace(i, j)
    return text