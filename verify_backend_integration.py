
import sys
import os
import asyncio
from datetime import datetime

# Add project root to path
sys.path.append("/home/MuhammedBesir/trading-botu/backend")

try:
    from app.services.signal_generator import SignalGenerator
    from app.api.routes.signals import daily_picks_cache
    print("✅ Imports successful")
except Exception as e:
    print(f"❌ Import failed: {e}")
    sys.exit(1)

async def test_signal_gen():
    print("Testing SignalGenerator initialization...")
    sg = SignalGenerator(strategy_type="moderate")
    print(f"✅ Initialized with strategy: {sg.strategy_type}")
    
    # We won't run full data fetching here as it might be slow, 
    # but we checked imports and class structure.
    
    print("Checking Cache Structure...")
    if "date" in daily_picks_cache and "data" in daily_picks_cache:
        print("✅ Cache structure valid")
    else:
        print("❌ Cache structure invalid")

if __name__ == "__main__":
    asyncio.run(test_signal_gen())
