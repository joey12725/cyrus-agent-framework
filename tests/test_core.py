import asyncio
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from tests import _stubs  # noqa: F401  (installs SDK stand-ins)

import cyrus
from cyrus import environment as environment_module
from cyrus.agent import Agent, BedrockAgent
from cyrus.environment import Environment, Message, Thread
from cyrus.flow import cFlow

REPO = Path(__file__).resolve().parent.parent
EXAMPLE = REPO / "examples" / "dnd-chat-bot"

INI = """[Settings]
project_directory = {project_directory}
memory_mode = ephemeral
token_limit = 1000
verbose = false
export_env = false

[API_Keys]
openai = test-openai
perplexity =
aws_access_key_id =
aws_secret_access_key =
cohere =
"""


class FakeAgent:
    """Answers with a canned line so conversations run offline."""

    def __init__(self, name):
        self.name = name
        self.prompts = []

    async def get_response(self, prompt, images=None):
        self.prompts.append(prompt)
        return f"{self.name} reply {len(self.prompts)}"

    async def load_thread(self, thread):
        self.thread = thread


class CyrusTestCase(unittest.TestCase):
    def setUp(self):
        Environment._instance = None
        cFlow.instance = None
        self._cwd = os.getcwd()
        self._tmp = tempfile.TemporaryDirectory()
        os.chdir(self._tmp.name)
        os.mkdir("config-files")
        Path("config-files/test.ini").write_text(INI.format(project_directory=EXAMPLE))
        patcher = mock.patch.object(environment_module, "VectorDatabase", _stubs.FakeVectorDatabase)
        patcher.start()
        self.addCleanup(patcher.stop)
        env_patch = mock.patch.dict(os.environ, {"COHERE_API_KEY": "from-env"})
        env_patch.start()
        self.addCleanup(env_patch.stop)
        self.env = Environment.getInstance(project_name="test")

    def tearDown(self):
        os.chdir(self._cwd)
        self._tmp.cleanup()
        Environment._instance = None
        cFlow.instance = None


class EnvironmentTests(CyrusTestCase):
    def test_reads_settings_and_falls_back_to_env_vars(self):
        self.assertEqual(self.env.config["memory_mode"], "ephemeral")
        self.assertEqual(self.env.config["token_limit"], 1000)
        self.assertFalse(self.env.config["verbose"])
        self.assertEqual(self.env.config["API_Keys"]["openai"], "test-openai")
        self.assertEqual(self.env.config["API_Keys"]["cohere"], "from-env")

    def test_rejects_project_names_with_special_characters(self):
        Environment._instance = None
        with self.assertRaises(ValueError):
            Environment.getInstance(project_name="bad name")

    def test_dotted_variable_paths(self):
        self.env.set_variable_from_string("party.gold", 42)
        self.assertEqual(self.env.get_variable_from_string("party.gold"), 42)
        self.assertIsNone(self.env.get_variable_from_string("party.silver"))

    def test_increment_step_threads_messages(self):
        self.env.increment_step(message="hi", sender="user", recipient="dm", new_conversation=True)
        self.env.increment_step(message="welcome", sender="dm", recipient="user")
        history = self.env.get_agent_chat_history("dm")
        self.assertEqual([m.content for m in history.messages], ["hi", "welcome"])


class ThreadTests(CyrusTestCase):
    def test_dump_formats(self):
        thread = Thread()
        thread.add_message(Message("user", "dm", "I open the door"))
        thread.add_message(Message("dm", "user", "A goblin waits inside"))
        self.assertEqual(thread.dump(), "user -> dm: I open the door\ndm -> user: A goblin waits inside")
        self.assertEqual(thread.dump(token_saver=True, character_limit=20), "user: I open the door")
        self.assertEqual(thread.members, ["user", "dm"])


class ConditionTests(CyrusTestCase):
    def test_returns_and_is_called(self):
        self.assertFalse(cyrus.returns("rollDice", "*").run())
        self.env.function_status["rollDice"] = "completed"
        self.assertTrue(cyrus.returns("rollDice", "*").run())
        self.assertTrue(cyrus.is_called("rollDice").run())

    def test_turn(self):
        thread = self.env.messages["current_thread"]
        for _ in range(3):
            thread.add_message(Message("a", "b", "c"))
        self.assertTrue(cyrus.turn(thread.turn()).run())
        self.assertFalse(cyrus.turn(thread.turn() + 1).run())

    def test_transition_accepts_callables_coroutines_and_functions(self):
        a, b = cyrus.State("a", []), cyrus.State("b", [])

        async def async_true():
            return True

        for condition in (lambda: True, async_true, cyrus.equals(1, 1), True):
            self.assertTrue(asyncio.run(cyrus.Transition(a, b, condition).check()))
        self.assertFalse(asyncio.run(cyrus.Transition(a, b, cyrus.false_function()).check()))


class FlowTests(CyrusTestCase):
    def test_flow_follows_transitions_between_states(self):
        loot = cyrus.State("loot", [cyrus.let("party.gold", 10)])
        shop = cyrus.State("shop", [cyrus.let("party.sword", True)])
        to_shop = cyrus.Transition(loot, shop, lambda: self.env.get_variable_from_string("party.gold") == 10)
        flow = cFlow.getInstance([loot, shop], loot, [to_shop])

        asyncio.run(flow.run())

        self.assertEqual(self.env.variables["party"], {"gold": 10, "sword": True})
        self.assertIs(self.env.flow["current_state"], shop)

    def test_loop_action_binds_iterator(self):
        seen = []

        class Record:
            async def run(self_inner):
                seen.append(self.env.variables["die"])

        asyncio.run(cyrus.loop([4, 6, 20], "die", [Record()]).run())
        self.assertEqual(seen, [4, 6, 20])

    def test_agents_talk_until_condition(self):
        dm, merchant = FakeAgent("dm"), FakeAgent("merchant")

        class AfterTwoReplies(cyrus.false_function):
            def run(self_inner):
                return len(merchant.prompts) >= 2

        action = cyrus.talks_to(dm, merchant, context="Haggle over a sword", until=AfterTwoReplies())
        asyncio.run(action.run())

        self.assertEqual(len(dm.prompts), 2)
        self.assertEqual(len(merchant.prompts), 2)
        self.assertIn("Haggle over a sword", dm.prompts[0])
        self.assertEqual(str(action), "dm talks to merchant")


class ExampleProjectTests(CyrusTestCase):
    def test_example_agents_and_functions_validate(self):
        for agent_file in (EXAMPLE / "agents").glob("*.agent"):
            Agent.validate_agent_file(str(agent_file))
        for function_file in (EXAMPLE / "functions").glob("*.function"):
            Agent.validate_function_file(str(function_file))

    def test_call_function_loads_tool_from_project(self):
        result = Agent.call_function("rollDice", {"diceCount": 2, "sidesPerDie": 1, "additionalSum": 3})
        self.assertEqual(result, "5")
        self.assertEqual(self.env.function_status["rollDice"], "completed")

    def test_bedrock_tool_spec_translation(self):
        spec = json.loads((EXAMPLE / "functions" / "rollDice.function").read_text())
        tool = BedrockAgent.translate_function_definition(None, spec)["toolSpec"]
        self.assertEqual(tool["name"], "rollDice")
        self.assertEqual(tool["inputSchema"]["json"]["required"], ["diceCount", "sidesPerDie"])


if __name__ == "__main__":
    unittest.main()
