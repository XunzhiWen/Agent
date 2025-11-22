from langchain_core.tools import tool

# 1. Define raw functions (for google-genai SDK)
def calculator_func(expression: str) -> str:
    """
    Useful for performing mathematical calculations.
    The input should be a valid mathematical expression as a string.
    Example: "5 + 5" or "10 * 2"
    """
    try:
        # WARNING: eval is dangerous in production. Use with caution or replace with a safer parser.
        return str(eval(expression))
    except Exception as e:
        return f"Error calculating: {e}"

def search_func(query: str) -> str:
    """
    Useful for searching for information on the internet.
    """
    # Mock implementation for demonstration
    return f"Mock search results for: {query}. The weather is sunny."

# 2. Create LangChain tools (for ToolNode)
# We name them explicitly to match what Gemini might infer or what we want.
# IMPORTANT: Name them exactly as the function name so Gemini mapping is 1:1
calculator = tool("calculator_func")(calculator_func)
search = tool("search_func")(search_func)
