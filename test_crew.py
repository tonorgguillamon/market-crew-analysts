from dotenv import load_dotenv

load_dotenv()

import asyncio
from src.agents.crew import MarketWarRoom


async def test_war_room():
    print("🚀 Initializing Market War Room Test...")
    
    # 1. Mock market event
    # This simulates the data that would normally come from your WebSocket/RabbitMQ
    mock_inputs = {
        'event': "NVIDIA (NVDA) dropped 8% in 30 minutes following a report of new export restrictions."
    }

    # 2. Initialize the Crew
    # We use the class we built in crew.py
    market_crew = MarketWarRoom().crew()
    market_crew.clear_cache() # Wipes the slate clean for the new trading day

    print(f"🧐 Analyzing Event: {mock_inputs['event']}")
    print("-" * 30)

    # 3. Execute Async Kickoff
    # This triggers the 4 peers in parallel and then the Boss
    try:
        result = await market_crew.kickoff_async(inputs=mock_inputs)
        
        print("\n" + "="*50)
        print("✅ ANALYSIS COMPLETE")
        print("="*50)
        print(f"\nFINAL VERDICT:\n{result.raw}")

        print(f"Total Tokens: {result.token_usage.total_tokens}")
        print(f"Total Cost (Est): ${result.token_usage.total_tokens * 0.000002}") # Rough average
        
    except Exception as e:
        print(f"❌ Test Failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_war_room())