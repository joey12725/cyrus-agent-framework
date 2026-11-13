# Cyrus architecture

Cyrus models a multi-agent application as a state machine. This page walks through the runtime one layer at a time, then covers configuration and how to extend it.

## The pieces

| Piece | Module | Role |
| --- | --- | --- |
| `Environment` | `cyrus/environment.py` | Process-wide singleton. Loads the project config, holds variables, tool status, conversation threads and the vector memory. |
| `Thread`, `Message` | `cyrus/environment.py` | A conversation and its messages (sender, recipient, content, state, timestamp). `Thread.dump()` renders a transcript, optionally trimmed to a character budget. |
| `VectorDatabase` | `cyrus/environment.py` | Chroma collections for messages and documents, embedded with OpenAI `text-embedding-3-small`, optionally reranked with Cohere `rerank-english-v3.0`. |
| `Agent` | `cyrus/agent.py` | Abstract base plus `OAIAgent`, `PerplexityAgent` and `BedrockAgent`. `Agent.create(name)` reads `agents/<name>.agent` and returns the right subclass. |
| Actions | `cyrus/actions.py` | The verbs a state performs: `talks_to`, `cot`, `call`, `let`, `println`, `loop`, `go_to`, `terminate`. |
| Conditions | `cyrus/functions.py` | Small objects with a `run()` method: `returns`, `is_called`, `turn`, `and_`, `or_`, `not_`, `equals`, `in_`, comparison and arithmetic helpers, `false_function`. |
| `State` | `cyrus/states.py` | A named list of actions. Also renders a rounded avatar icon for the flow graph from the agents it involves. |
| `Transition` | `cyrus/transition.py` | Source state, destination state and a condition (callable, coroutine, condition object or plain bool). |
| `cFlow` | `cyrus/flow.py` | Singleton runner that executes one state at a time and follows transitions. |

## A flow run, step by step

1. `Environment.getInstance(project_name="dnd")` reads `config-files/dnd.ini` from the working directory and builds the vector memory.
2. `Agent.create("dm")` validates `agents/dm.agent`, loads each listed `.function` schema and constructs the provider client. Bedrock agents translate the schemas into Converse `toolSpec` blocks and consult a capability table, so a model without tool use or system prompts still loads cleanly.
3. Actions, states and transitions are constructed. Each registers with the `cFlow` singleton, so states know their outgoing transitions.
4. `await flow.run()` starts at the start state. For each state it launches two asyncio tasks:
   - **actions task**: runs the state's actions in order.
   - **transitions task**: polls every outgoing transition every 100 ms.
5. Whichever finishes first decides what happens next. A transition that fires sets `env.flow["kill_state"]`, which long-running actions such as `talks_to` check between turns, and the flow moves to the destination state. If the actions finish first, the flow checks transitions once more and stops when none fire.

`talks_to` also checks transitions between conversational turns, so a condition like `returns("rollDice", "*")` can end a conversation the moment the agent's tool call completes.

## Tool calls

A tool is two files in the project's `functions/` directory:

- `rollDice.function`: the name, description and JSON Schema parameters, in the OpenAI function format.
- `rollDice.py`: a module exposing a function with the same name.

When a model asks for a tool, `Agent.call_function` imports the module from disk, checks the arguments against the function signature, marks the tool `"in progress"` in `env.function_status`, runs it and marks it `"completed"`. The result goes back to the model as a tool message (OpenAI) or a `toolResult` block (Bedrock), and the model's follow-up is returned to the caller.

## Memory

Every message recorded with `env.increment_step()` is appended to a thread and embedded into Chroma with its sender, recipient, thread and state as metadata. Threads are matched by an additive score: same state, shared members and recency.

`memory_mode` in the project config controls how far back an agent can see:

| Mode | Behavior |
| --- | --- |
| `ephemeral` | Each `talks_to` starts a fresh thread. |
| `state-persistent` | `cot` pulls the most relevant past message from the same state. |
| `agent-persistent` | `cot` pulls the most relevant past message the agent sent or received. |

Agents that set `use_rerank_documents` get the nearest document chunk added to their context as well.

## Configuration

A project is a directory with `agents/`, `functions/` and `documents/`, plus an INI file in `config-files/` next to the script that runs it:

```ini
[Settings]
project_directory = .
memory_mode = ephemeral
token_limit = 100000
verbose = true
export_env = false

[API_Keys]
openai =
perplexity =
aws_access_key_id =
aws_secret_access_key =
cohere =
```

Blank keys fall back to `OPENAI_API_KEY`, `PERPLEXITY_API_KEY`, `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY` and `COHERE_API_KEY`. Project names may only contain letters and digits. Real `*.ini` files are git-ignored; commit the `*.ini.example` templates.

### Agent files

| Field | Required | Notes |
| --- | --- | --- |
| `platform` | yes | `openai`, `bedrock` or `perplexity` (`gemini` is reserved). |
| `name`, `role`, `system_prompt`, `model` | yes | `model` is the provider's model ID. |
| `functions` | no | Tool names from the project's `functions/` directory. |
| `documents` | no | Files from `documents/` attached to the agent. Index text into the shared store with `env.vdb.add_document(text, chunk_size=...)`. |
| `use_memory`, `use_rerank_memory`, `use_rerank_documents` | no | Retrieval switches. |
| `profile_picture` | no | Avatar filename under `front-end/resources/profile_images`; picked at random when missing. |

## Extending Cyrus

- **New provider.** Subclass `Agent` and implement `__init__(agent_config)`, `async generate_message(prompt, images)`, `async load_thread(thread)` and `async terminate()`. Add a branch for its `platform` in `Agent.create` and `Agent.validate_agent_file`.
- **New action.** Subclass `Action`, call `super().__init__()` so the action is bound to the live environment and flow, and implement `async run()`. Long-running actions should return early when `env.flow["kill_state"]` is set.
- **New condition.** Subclass `Function` (or pass any callable) and return a bool from `run()`.

## Studio

The `front-end/` scripts are standalone Streamlit apps run from inside `front-end/`:

| Script | What it does |
| --- | --- |
| `config-editor.py` | Create or edit a project INI and scaffold its directories, optionally copying API keys from another config. |
| `agent-configuration.py` | Build agents from a model dropdown covering the OpenAI, Bedrock and Perplexity catalogs of mid-2024, then chat with the result. |
| `function-configuration.py` | Write a tool's schema and Python body side by side in an Ace editor. |
| `flow-generator.py` | Assemble states and transitions and render the flow as a graph with agent avatars as nodes. |
