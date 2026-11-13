"""Chat with the Dungeon Master from your terminal.

Run from this directory after copying config-files/dnd.ini.example to
config-files/dnd.ini (or exporting the matching API key env vars):

    python chat.py
"""
import asyncio

from cyrus import Agent, Environment, talks_to


async def main():
    Environment.getInstance(project_name="dnd")
    dm = await Agent.create("dm")

    action = talks_to("user", dm, context="Help the player come up with a character.")
    await action.run()


if __name__ == "__main__":
    asyncio.run(main())
