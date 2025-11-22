import sys
from langchain_core.messages import HumanMessage
from src.graph import app

def main():
    print("Initializing LangGraph Agent with Gemini...")
    print("Type 'exit' to quit.")
    print("-" * 50)

    while True:
        try:
            user_input = input("You: ")
            if user_input.lower() in ["exit", "quit"]:
                print("Goodbye!")
                break
            
            if not user_input.strip():
                continue

            # Run the graph
            inputs = {"messages": [HumanMessage(content=user_input)]}
            
            # Stream the output to see intermediate steps
            print("Agent is thinking...")
            for output in app.stream(inputs):
                for key, value in output.items():
                    print(f"Node '{key}':")
                    # Extract and print the last message content
                    if "messages" in value and value["messages"]:
                        last_msg = value["messages"][-1]
                        if hasattr(last_msg, "content") and last_msg.content:
                            print(last_msg.content)
                        elif hasattr(last_msg, "tool_calls") and last_msg.tool_calls:
                             print(f"Calling Tool: {last_msg.tool_calls[0]['name']}")
                    print("---")
            
            # Get final response
            # The state is updated in the loop, but we can also just look at the last message
            # However, app.stream yields updates. 
            # Let's just print the final response from the last update if it's from the agent.
            
            # A simpler way for the user to see the final answer:
            # The loop above shows progress.
            # We can invoke it again or just rely on the stream.
            # Let's just print a separator.
            print("-" * 50)

        except Exception as e:
            print(f"An error occurred: {e}")
            print("Did you set your GOOGLE_API_KEY in .env?")

if __name__ == "__main__":
    main()
