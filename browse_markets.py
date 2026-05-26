#!/usr/bin/env python3
"""
Browse available markets on Kalshi
Usage: python browse_markets.py [series_ticker] [status]
"""

import sys
from pathlib import Path
from decimal import Decimal

sys.path.insert(0, str(Path(__file__).parent))

from config import ENVIRONMENT, API_KEY_ID, PRIVATE_KEY_PATH
from lol import KalshiClient, KalshiConfig

def format_price(price_str):
    """Format price string to currency"""
    try:
        return f"${Decimal(price_str):.2f}"
    except:
        return "N/A"

def main():
    series_ticker = None
    status = "open"
    
    if len(sys.argv) > 1:
        series_ticker = sys.argv[1].upper()
    
    if len(sys.argv) > 2:
        status = sys.argv[2].lower()
    
    try:
        print(f"\n{'='*70}")
        print(f"  Available Markets ({ENVIRONMENT})")
        if series_ticker:
            print(f"  Series: {series_ticker}")
        print(f"  Status: {status}")
        print(f"{'='*70}\n")
        
        config = KalshiConfig()
        config.ENVIRONMENT = ENVIRONMENT
        config.API_KEY_ID = API_KEY_ID
        config.PRIVATE_KEY_PATH = PRIVATE_KEY_PATH
        
        client = KalshiClient(config)
        markets = client.get_markets(
            series_ticker=series_ticker,
            status=status,
            limit=50
        )
        
        if not markets:
            print("No markets found.\n")
            return
        
        print(f"{'Ticker':<25} {'Title':<30} {'YES Bid':<10} {'Volume':<10}")
        print("-" * 70)
        
        for market in markets:
            ticker = market['ticker'][:24]
            title = market['title'][:29]
            yes_bid = format_price(market.get('yes_bid_dollars', 'N/A'))
            volume = market.get('volume_fp', 'N/A')
            
            print(f"{ticker:<25} {title:<30} {yes_bid:<10} {volume:<10}")
        
        print(f"\nFound {len(markets)} markets\n")
    
    except Exception as e:
        print(f"❌ Error: {e}\n")
        sys.exit(1)

if __name__ == '__main__':
    main()
