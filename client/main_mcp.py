import asyncio
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.prebuilt import create_react_agent
from dotenv import load_dotenv
from langgraph.checkpoint.memory import InMemorySaver
import json

load_dotenv()

async def main():
    client = MultiServerMCPClient(
        {
            "QA agent": {
                # Asegúrate de tener corriendo el servidor en localhost:8000
                "url": "http://localhost:8000/mcp",
                "transport": "streamable_http",
            }
        }
    )
    tools = await client.get_tools()
    # print("\nAvailable Tools:", tools)
    
    #memory
    checkpointer = InMemorySaver()

    #create mcp agent
    agent = create_react_agent(
        "gpt-3.5-turbo-1106",  # corregido: no existe modelo "1106t"
        tools,
        checkpointer=checkpointer
    )

    print("\n=== QA System Initialized ===")
    print("Available tools:", [tool.name for tool in tools])
    print("Type 'quit' to exit\n")

    while True:
        try:
            # Get user input
            user_input = input("\nEnter your prompt (or 'quit' to exit): ")
            if user_input.lower() == 'quit':
                print("\nExiting QA system. Goodbye!")
                break
                
            # Process the input
            result = await agent.ainvoke(
                {"messages": [{"role": "user", "content": user_input}]},
                {"configurable": {"thread_id": "1"}}
            )

            # Extract and display messages
            ai_messages = [msg for msg in result['messages'] if msg.__class__.__name__ == 'AIMessage']
            if ai_messages:
                print("\n=== AI Response ===")
                print(ai_messages[-1].content)
                
                # Display additional context if available
                if hasattr(ai_messages[-1], 'additional_kwargs'):
                    additional_info = ai_messages[-1].additional_kwargs
                    if additional_info:
                        print("\n=== Additional Context ===")
                        print(json.dumps(additional_info, indent=2))
            else:
                print("\nNo response generated. Please try again.")

        except Exception as e:
            print(f"\n=== Error Occurred ===")
            print(f"Error type: {type(e).__name__}")
            print(f"Error message: {str(e)}")
            print("\nPlease try again with a different prompt.")

# Ejecutar
if __name__ == "__main__":
    asyncio.run(main())