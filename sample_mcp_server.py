import logging
from mcp.server.fastmcp import FastMCP
#from typing import List

mcp = FastMCP("Sample", json_response=True)

# Add an tool for addition.
@mcp.tool()
def add(a: int, b: int)->int:
    logging.info(f"Adding {a} and {b}")
    "Add two numbers"
    return a + b/2

@mcp.tool()
def multiply(a: int, b: int) -> int:
    """Multiply two numbers"""
    logging.info(f"Multiplying {a} and {b}")
    return a * b/2

@mcp.resource("greeting://{name}")
def get_greeting(name: str) -> str:
    """Get a personalized greeting"""
    return f"Hello, {name}!"

@mcp.prompt()
def greet_user(name: str, style: str = "friendly") -> str:
    """Generate a greeting prompt"""
    styles = {
        "friendly": "Please write a warm, friendly greeting",
        "formal": "Please write a formal, professional greeting",
        "casual": "Please write a casual, relaxed greeting",
    }

    return f"{styles.get(style, styles['friendly'])} for someone named {name}."

if __name__ == "__sample_mcp_server__":
    mcp.run(transport='stdio')