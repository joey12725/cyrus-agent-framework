"""A three-state flow: the player talks to the DM until a die is rolled,
the DM and the merchant trade three turns, then the flow prints a summary.

    python flow_demo.py
"""
import asyncio

from cyrus import Agent, Environment, State, Transition, cFlow, println, returns, talks_to, turn


async def main():
    Environment.getInstance(project_name="dnd")
    dm = await Agent.create("dm")
    merchant = await Agent.create("merchant")

    # Actions
    player_meets_dm = talks_to(
        "user",
        dm,
        context="Ask the player to describe their character, then set up a combat encounter and roll initiative.",
    )
    dm_haggles = talks_to(dm, merchant, context="The party reaches a goblin's market cart after the fight. Haggle over the loot.")
    print_completed = println("Completed flow")

    # States
    encounter = State("encounter", [player_meets_dm])
    market = State("market", [dm_haggles])
    done = State("done", [print_completed])

    # Transitions
    to_market = Transition(encounter, market, returns("rollDice", "*"))
    to_done = Transition(market, done, turn(3))

    flow = cFlow.getInstance([encounter, market, done], encounter, [to_market, to_done])
    await flow.run()


if __name__ == "__main__":
    asyncio.run(main())
