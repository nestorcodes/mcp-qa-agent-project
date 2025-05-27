import asyncio
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.prebuilt import create_react_agent
from dotenv import load_dotenv
from langgraph.checkpoint.memory import InMemorySaver

load_dotenv()

async def main():
    client = MultiServerMCPClient(
        {
            "weather": {
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

    while True:
        #terminal input
        user_input = input("\nEnter your prompt (or 'quit' to exit): ")
        if user_input.lower() == 'quit':
            break
            
        try:
            # you can use aiinvoke invoke or stream to call the agent
            # configurable is for memory
            result =  await agent.ainvoke(
            {"messages": [{"role": "user", "content": user_input}]},
            {"configurable": {"thread_id": "1"}}
        )
            # Get only the last AI message
            ai_messages = [msg for msg in result['messages'] if msg.__class__.__name__ == 'AIMessage']
            if ai_messages:
                print("\nAI Response:", ai_messages[-1].content)
        except Exception as e:
            print(f"Error: {str(e)}")

# Ejecutar
if __name__ == "__main__":
    asyncio.run(main())