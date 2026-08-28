import asyncio
from shared.llm import OllamaClient, LLMRequest
import sys

async def main():
    # Setup Windows event loop policy if needed
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        
    client = OllamaClient()
    print("Sending request to LLM...")
    
    # Note: The generate method expects an LLMRequest object, not a raw string.
    request = LLMRequest(prompt="Hello, who are you?")
    
    try:
        response = await client.generate(request)
        print("\nResponse:")
        print(response.raw_text)
    except Exception as e:
        print(f"\nError: {e}")

if __name__ == "__main__":
    asyncio.run(main())
