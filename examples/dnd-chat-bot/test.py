from openai import OpenAI
import configparser
import os
import difflib

messages = [
    {
        "role": "system",
        "content": (
            "You are an artificial intelligence assistant and you need to "
            "engage in a helpful, detailed, polite conversation with a user."
        ),
    },
    {
        "role": "user",
        "content": (
            "How many stars are in the universe?"
        ),
    },
]

config = configparser.ConfigParser()
if not os.path.exists(os.path.join(os.getcwd(), "config.ini")):
    raise Exception("config.ini not found")
config.read(os.path.join(os.getcwd(), "config.ini"))
api_key = config["API_Keys"]["perplexity"]
print(f"API Key: {api_key}, type: {type(api_key)}, len {len(api_key)} equal {api_key == 'REDACTED_PERPLEXITY_KEY'}")
print(f"copied equals {"REDACTED_PERPLEXITY_KEY" == "REDACTED_PERPLEXITY_KEY"}")
case_a = api_key
case_b = 'REDACTED_PERPLEXITY_KEY'
for i in range(len(case_a)):
    if case_a[i] != case_b[i]:
        print(f"index {i} is different: {case_a[i]} != {case_b[i]}")