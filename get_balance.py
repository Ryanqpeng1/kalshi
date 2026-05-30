#!/usr/bin/env python3
"""
Get account balance
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from config import API_KEY_ID, PRIVATE_KEY_PATH, ENVIRONMENT
from lol import KalshiClient, KalshiConfig

def main():
    if API_KEY_ID == 'your-api-key-id-here':
        print("ERROR: API credentials not configured")
        print("Run: python setup.py")
        sys.exit(1)
    
    try:
        print(f"\n{'='*50}")
        print(f"  Kalshi Account Balance ({ENVIRONMENT})")
        print(f"{'='*50}\n")
        
        config = KalshiConfig()
        config.ENVIRONMENT = ENVIRONMENT
        config.API_KEY_ID = API_KEY_ID
        config.PRIVATE_KEY_PATH = PRIVATE_KEY_PATH
        
        client = KalshiClient(config)
        balance = client.get_balance()
        
        balance_dollars = balance['balance'] / 100
        print(f"Balance: ${balance_dollars:,.2f}\n")
    
    except Exception as e:
        print(f"Error: {e}\n")
        sys.exit(1)

if __name__ == '__main__':
    main()
