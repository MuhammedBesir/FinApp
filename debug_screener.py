
import sys
import os
import logging

# Configure logging to print to console
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add current directory to path so we can import app modules
sys.path.append(os.getcwd())
sys.path.append(os.path.join(os.getcwd(), 'backend'))

try:
    from backend.app.services.stock_screener import StockScreener
except ImportError:
    # Try alternative path if running from root
    try:
        from app.services.stock_screener import StockScreener
    except ImportError:
        print("Could not import StockScreener. Check python path.")
        sys.exit(1)

def test_top_movers():
    print("Initializing StockScreener...")
    try:
        screener = StockScreener()
        print("StockScreener initialized. Fetching top movers...")
        
        result = screener.get_top_movers(top_n=5)
        
        print("\nResult:")
        if result.get('success'):
            print("SUCCESS!")
            print(f"Gainers: {len(result.get('gainers', []))}")
            print(f"Losers: {len(result.get('losers', []))}")
        else:
            print("FAILED!")
            print(result.get('message'))
            
    except Exception as e:
        print(f"\nCRITICAL ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_top_movers()
