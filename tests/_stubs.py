"""Offline stand-ins for the provider SDKs so the core runs without network
access or API keys. Imported by the tests before `cyrus`."""
import importlib
import sys
import types


def _module(name, **attrs):
    mod = types.ModuleType(name)
    for key, value in attrs.items():
        setattr(mod, key, value)
    sys.modules[name] = mod
    return mod


class _Client:
    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs


def install():
    # Provider SDKs are always faked: tests must never touch the network.
    _module("openai", OpenAI=_Client)
    _module("cohere", Client=_Client)
    _module("chromadb", Client=_Client)
    _module("boto3", Session=_Client)

    # Local-only libraries are used for real when installed.
    try:
        importlib.import_module("rich.console")
    except ImportError:
        class Console:
            def print(self, *args, **kwargs):
                print(*args)

        _module("rich")
        _module("rich.console", Console=Console)
        _module("rich.markdown", Markdown=str)

    try:
        importlib.import_module("PIL.Image")
    except ImportError:
        _module("PIL", Image=None, ImageDraw=None, ImageOps=None)

    try:
        importlib.import_module("base256")
    except ImportError:
        _module("base256")


class FakeVectorDatabase:
    def __init__(self, *args, **kwargs):
        self.threads = []
        self.messages = []

    def add_thread(self, thread):
        self.threads.append(thread)

    def add_message(self, message, thread_id=None, state=None):
        self.messages.append(message)


install()
