import os
from typing import TypedDict, Annotated, Sequence, Any
import operator
from google import genai
from google.genai import types
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, ToolMessage
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from dotenv import load_dotenv
from .tools import calculator, search, calculator_func, search_func

load_dotenv()

# 1. Define State
class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]

# 2. Initialize Client
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    api_key = os.getenv("GOOGLE_API_KEY")

if not api_key:
    raise ValueError("GEMINI_API_KEY or GOOGLE_API_KEY not found.")

client = genai.Client(api_key=api_key)

# 3. Define Tools
gemini_tools = [calculator_func, search_func]
langchain_tools = [calculator, search]

# Helper to convert LangChain messages to Gemini Contents
def convert_messages(messages: Sequence[BaseMessage]) -> list[types.Content]:
    contents = []
    for msg in messages:
        if isinstance(msg, HumanMessage):
            contents.append(types.Content(
                role="user",
                parts=[types.Part.from_text(text=msg.content)]
            ))
        elif isinstance(msg, AIMessage):
            parts = []
            if msg.content:
                parts.append(types.Part.from_text(text=msg.content))
            if msg.tool_calls:
                for tc in msg.tool_calls:
                    # Construct FunctionCall part
                    # Note: Gemini SDK expects FunctionCall object
                    parts.append(types.Part.from_function_call(
                        name=tc['name'], # Ensure name matches what Gemini expects (e.g. calculator_func)
                        args=tc['args']
                    ))
            contents.append(types.Content(
                role="model",
                parts=parts
            ))
        elif isinstance(msg, ToolMessage):
            # Tool output
            # Gemini expects function_response in a 'user' role (or 'function' depending on API version, but SDK handles it)
            # Actually, for google-genai SDK, we use Part.from_function_response
            # And it usually goes into a 'user' role content block.
            
            # We need to match the response to the call.
            # LangChain ToolMessage has 'tool_call_id' and 'name'.
            
            # IMPORTANT: Gemini needs the function name in the response.
            # LangChain's ToolMessage might not have the function name if not explicitly set, 
            # but usually it does or we can infer it.
            
            parts = [types.Part.from_function_response(
                name=msg.name, # This must match the function name called
                response={"result": msg.content} # The response content
            )]
            contents.append(types.Content(
                role="user",
                parts=parts
            ))
            
    return contents

# 4. Define Nodes
def call_model(state: AgentState):
    messages = state['messages']
    
    # Convert full history
    gemini_contents = convert_messages(messages)
    
    # Call Gemini 2.5 Flash
    # We pass the full history as 'contents'
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=gemini_contents,
        config=types.GenerateContentConfig(
            tools=gemini_tools
        )
    )
    
    # Convert response to AIMessage
    tool_calls = []
    content = ""
    
    if response.candidates and response.candidates[0].content.parts:
        for part in response.candidates[0].content.parts:
            if part.text:
                content += part.text
            if part.function_call:
                # Map Gemini function call to LangChain tool_call
                fn_name = part.function_call.name
                
                # Normalize names if needed (Gemini uses function name, LangChain uses tool name)
                # In our tools.py, we mapped calculator_func -> calculator tool.
                # But here we need to be careful.
                # If Gemini calls 'calculator_func', we must return a tool call for 'calculator' 
                # so ToolNode can execute it.
                # AND we must ensure the ToolMessage returned has name='calculator_func' 
                # so Gemini knows it's the response for that call.
                
                # Wait, ToolNode executes based on tool name.
                # If we return tool_call name='calculator', ToolNode looks for 'calculator'.
                # Our tool is named 'calculator'.
                # But Gemini expects response for 'calculator_func'.
                
                # Solution:
                # 1. Gemini calls 'calculator_func'.
                # 2. We map it to 'calculator' for ToolNode execution.
                # 3. ToolNode executes and returns ToolMessage.
                # 4. We need to ensure ToolMessage.name is 'calculator_func' when converting back to Gemini history.
                
                # Let's keep it simple: Rename LangChain tools to match function names.
                # We will update tools.py to name tools 'calculator_func' and 'search_func'.
                
                tool_calls.append({
                    "name": fn_name,
                    "args": part.function_call.args,
                    "id": "call_" + fn_name
                })
    
    return {"messages": [AIMessage(content=content, tool_calls=tool_calls)]}

tool_node = ToolNode(langchain_tools)

# 5. Define Conditional Logic
def should_continue(state: AgentState):
    messages = state['messages']
    last_message = messages[-1]
    if last_message.tool_calls:
        return "tools"
    return END

# 6. Build Graph
workflow = StateGraph(AgentState)

workflow.add_node("agent", call_model)
workflow.add_node("tools", tool_node)

workflow.set_entry_point("agent")

workflow.add_conditional_edges(
    "agent",
    should_continue,
    {
        "tools": "tools",
        END: END
    }
)

workflow.add_edge("tools", "agent")

from langgraph.checkpoint.memory import MemorySaver

# ... (existing code)

# 7. Compile
checkpointer = MemorySaver()
app = workflow.compile(checkpointer=checkpointer)
