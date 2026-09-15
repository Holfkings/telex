"""
Sample Python service for testing tree-sitter AST scanner.
Calls create_completion directly and via client.create_completion().
"""
from openai import OpenAI

client = OpenAI()

def run_pipeline(prompt: str):
    # Plain identifier call
    direct_res = create_completion(model="gpt-4", prompt=prompt)

    # Attribute / member method call
    client_res = client.create_completion(model="gpt-4o", prompt=prompt)

    return direct_res, client_res
