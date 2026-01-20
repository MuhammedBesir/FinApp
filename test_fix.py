#!/usr/bin/env python3
"""Quick test for data_fetcher fixes"""

import sys
import os
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from backend.app.services.data_fetcher import DataFetcher

def test_fetch():
    print("Testing DataFetcher with improved error handling...")
    df_service = DataFetcher()
    
    # Test single ticker
    result = df_service.fetch_realtime_data('AKBNK.IS')
    
    if result is not None and not result.empty:
        print(f"✓ SUCCESS: Fetched {len(result)} data points for AKBNK.IS")
        print(f"✓ Columns: {list(result.columns)}")
        return True
    else:
        print("✗ FAILED: Empty or None result")
        return False

if __name__ == "__main__":
    success = test_fetch()
    sys.exit(0 if success else 1)
