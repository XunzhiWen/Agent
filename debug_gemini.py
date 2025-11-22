import os
from google import genai
from google.genai import types
from dotenv import load_dotenv
from src.tools import calculator_func, search_func

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
if not api_key:
    print("Error: API Key not found")
    exit(1)

client = genai.Client(api_key=api_key)

gemini_tools = [calculator_func, search_func]

print("Calling Gemini with tool...")
try:
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents="Search for the weather in Timbuktu",
        config=types.GenerateContentConfig(
            tools=gemini_tools
        )
    )
    print("\n--- Response ---")
    print(response)
    print("\n--- Parts ---")
    if response.candidates:
        for part in response.candidates[0].content.parts:
            print(f"Part: {part}")
            if part.function_call:
                print(f"Function Call: {part.function_call}")
except Exception as e:
    print(f"Error: {e}")
