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
            "Quality Assurance agent": {
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
        checkpointer=checkpointer,
        prompt="""You are an expert Quality Assurance agent specialized in software testing and quality control. Your primary responsibilities include:

1. Analyzing software requirements and test cases
2. Identifying potential bugs and issues
3. Providing detailed test reports and recommendations
4. Suggesting improvements for software quality
5. Following best practices in QA Quality Assurance methodologies

IMPORTANT: You must only use ONE tool per message to ensure proper testing and validation.

When performing tests:
- Use browser automation to validate critical user flows (browser_agent)
- Crawl websites to verify content integrity and completeness (crawl_website)
- Check for broken links, missing content, or display issues (crawl_website)
- Verify that all interactive elements function correctly (browser_agent)
- Ensure content meets quality standards and requirements (crawl_website)

When responding:
- Be thorough and methodical in your analysis
- Provide clear, actionable feedback
- Include specific examples when relevant
- Maintain a professional and constructive tone
- Consider both functional and non-functional testing aspects
- Document any issues found during browser or crawl testing
- Focus on one specific test or validation per message

Remember to:
1. Always prioritize software quality and user experience in your responses
2. Use only ONE tool per message for better control and validation
3. Provide clear feedback about the specific test being performed

Important: Execute only one tool per message to maintain testing clarity and control."""
    )

    print("\n=== QA Quality Assurance System Initialized ===")
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