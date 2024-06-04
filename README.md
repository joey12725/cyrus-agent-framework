# Cyrus Agent Framework

Cyrus is a powerful and intuitive tool for rapidly building AI agent applications. It provides a user-friendly GUI that enables users with basic programming knowledge to create, tune, and deploy AI agents efficiently.

## Key Features

1. **Intuitive GUI**: Cyrus offers a simple and intuitive graphical user interface that allows users to work on and fine-tune AI agents with ease. The interface provides quick access to important safety and cybersecurity features, ensuring secure and reliable agent development.

2. **Transparent Pricing**: Cyrus provides transparent pricing information, enabling users to make informed decisions about their AI agent deployments. Users can easily understand the costs associated with their applications and optimize their usage accordingly.

3. **Data Store Management**: Cyrus simplifies data store management, allowing users to efficiently organize and manage the data required for their AI agent applications. It provides a centralized and streamlined approach to data handling.

4. **Model Capability Management**: With Cyrus, users can easily manage the capabilities of their AI agents. The framework provides a clear overview of the available models and their functionalities, enabling users to select and configure the most suitable models for their specific use cases.

5. **Automated Event-Driven Data Pipelines**: Cyrus offers automated, event-driven data pipelines specifically designed for multi-agent applications. These pipelines facilitate seamless data flow between agents, enabling efficient collaboration and communication.

6. **Support for Major Models**: Cyrus supports all the major AI models, including OpenAI's GPT series, Google's Gemini, and others. Users can leverage the power of these pre-trained models to build sophisticated AI agent applications.

7. **Custom Model Integration**: In addition to supporting major models, Cyrus provides a framework for quickly integrating new models as they become available. This flexibility allows users to stay up-to-date with the latest advancements in AI and incorporate them into their agent applications.

8. **Shared Workspace**: Cyrus introduces a shared workspace that all the agents can access. This workspace acts as a collaborative environment, resembling a combination of a whiteboard and a filesystem. It enables agents to share information, coordinate tasks, and work together seamlessly.

9. **Code Integration**: Cyrus supports the integration of custom code within the agent framework. Users can write code that reads from or writes to the shared environment, enabling powerful customization and extension possibilities.

## Current Progress

So far the underlying mechanics work. Agents can be quickly and easily created and attached to all sorts of capabilities. Function calling has been standardized across models and a system of universal cost tracking has been built. Agents can communicate with each other and a pipeline can be executed from end to end without issue. Right now the code is a bit clunky and slow. Support for Claude needs to be improved since I am fighting the rate-limiting system. Gemini 1.5 Pro and GPT-3.5 Turbo, GPT4, and GPT40 all work well. I also want to add support for LLAMA 3. The plan right now is to build the GUI using Streamlit for version 1 with a "bring your own api key" approach. I would like to quickly switch to a Stripe monthly invoice system or credits purchase system as bringing an api key for OpenaAI + an api key for anthropic + a google account + ... + ... can get complicated quickly. 
