#!/usr/bin/env python3
"""
Place an order on Kalshi
Usage: python place_order.py [market_ticker] [side] [action] [count] [price]
"""

import sys
import logging
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from config import API_KEY_ID, PRIVATE_KEY_PATH, ENVIRONMENT, REST_URLS
from lol import KalshiClient, KalshiConfig, KalshiAuth, logger

def print_header(text):
    print("\n" + "="*60)
    print(f"  {text}")
    print("="*60 + "\n")

def get_user_input_order():
    """Interactively get order parameters from user"""
    
    print_header("Place an Order on Kalshi")
    
    # Get market ticker
    ticker = input("Market ticker (e.g., KXHARRIS24-LSV): ").strip().upper()
    if not ticker:
        print("❌ Market ticker is required")
        sys.exit(1)
    
    # Get side
    while True:
        side = input("Side (yes/no): ").strip().lower()
        if side in ['yes', 'no']:
            break
        print("❌ Side must be 'yes' or 'no'")
    
    # Get action
    while True:
        action = input("Action (buy/sell): ").strip().lower()
        if action in ['buy', 'sell']:
            break
        print("❌ Action must be 'buy' or 'sell'")
    
    # Get count
    while True:
        try:
            count = int(input("Number of contracts: ").strip())
            if count > 0:
                break
            print("❌ Count must be greater than 0")
        except ValueError:
            print("❌ Count must be a number")
    
    # Get price
    while True:
        try:
            price = int(input("Price in cents (1-99): ").strip())
            if 1 <= price <= 99:
                break
            print("❌ Price must be between 1 and 99 cents")
        except ValueError:
            print("❌ Price must be a number")
    
    return ticker, side, action, count, price

def parse_command_line_args():
    """Parse command line arguments"""
    if len(sys.argv) == 1:
        return None  # Interactive mode
    
    if len(sys.argv) != 6:
        print("Usage: python place_order.py [ticker] [side] [action] [count] [price]")
        print("  ticker: Market ticker (e.g., KXHARRIS24-LSV)")
        print("  side:   yes or no")
        print("  action: buy or sell")
        print("  count:  Number of contracts")
        print("  price:  Price in cents (1-99)")
        sys.exit(1)
    
    ticker = sys.argv[1].upper()
    side = sys.argv[2].lower()
    action = sys.argv[3].lower()
    
    try:
        count = int(sys.argv[4])
        price = int(sys.argv[5])
    except ValueError:
        print("❌ Count and price must be numbers")
        sys.exit(1)
    
    # Validate
    if side not in ['yes', 'no']:
        print("❌ Side must be 'yes' or 'no'")
        sys.exit(1)
    
    if action not in ['buy', 'sell']:
        print("❌ Action must be 'buy' or 'sell'")
        sys.exit(1)
    
    if count <= 0:
        print("❌ Count must be greater than 0")
        sys.exit(1)
    
    if not (1 <= price <= 99):
        print("❌ Price must be between 1 and 99 cents")
        sys.exit(1)
    
    return ticker, side, action, count, price

def show_market_info(client, ticker):
    """Show market info before placing order"""
    try:
        market = client.get_market(ticker)
        print(f"Market:  {market['ticker']} - {market['title']}")
        print(f"Status:  {market['status']}")
        print(f"YES bid: ${market.get('yes_bid_dollars', 'N/A')}")
        print(f"NO bid:  ${market.get('no_bid_dollars', 'N/A')}")
    except Exception as e:
        print(f"⚠️  Could not fetch market info: {e}")

def main():
    # Parse arguments or get interactive input
    args = parse_command_line_args()
    
    if args:
        ticker, side, action, count, price = args
        interactive = False
    else:
        ticker, side, action, count, price = get_user_input_order()
        interactive = True
    
    # Validate config
    if API_KEY_ID == 'your-api-key-id-here':
        print("\n❌ ERROR: API credentials not configured")
        print("\nRun setup first:")
        print("  python setup.py")
        sys.exit(1)
    
    if PRIVATE_KEY_PATH == 'path/to/your/kalshi-key.key':
        print("\n❌ ERROR: Private key path not configured")
        print("\nRun setup first:")
        print("  python setup.py")
        sys.exit(1)
    
    # Initialize client
    try:
        print_header("Connecting to Kalshi")
        print(f"Environment: {ENVIRONMENT}")
        print(f"API Key ID: {API_KEY_ID}")
        
        config = KalshiConfig()
        config.ENVIRONMENT = ENVIRONMENT
        config.API_KEY_ID = API_KEY_ID
        config.PRIVATE_KEY_PATH = PRIVATE_KEY_PATH
        
        client = KalshiClient(config)
        print("✓ Connected")
    
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        sys.exit(1)
    
    # Show market info
    show_market_info(client, ticker)
    
    # Confirm order
    if interactive:
        print_header("Order Summary")
        print(f"Market:    {ticker}")
        print(f"Side:      {side.upper()}")
        print(f"Action:    {action.upper()}")
        print(f"Quantity:  {count} contracts")
        print(f"Price:     ${price/100:.2f}")
        
        confirm = input("\nPlace this order? (yes/no): ").strip().lower()
        if confirm != "yes":
            print("Cancelled.")
            sys.exit(0)
    
    # Place order
    try:
        print_header("Placing Order")
        print(f"Ticker: {ticker}")
        print(f"Side: {side}, Action: {action}")
        print(f"Quantity: {count}, Price: ${price/100:.2f}")
        
        order = client.place_order(
            ticker=ticker,
            side=side,
            action=action,
            count=count,
            price=price
        )
        
        print_header("✓ Order Placed Successfully")
        order_data = order.get('order', {})
        print(f"Order ID:       {order_data.get('order_id')}")
        print(f"Status:         {order_data.get('status')}")
        print(f"Ticker:         {order_data.get('ticker')}")
        print(f"Side:           {order_data.get('side')}")
        print(f"Count:          {order_data.get('count')}")
        print(f"Price:          ${order_data.get('yes_price', 'N/A')/100:.2f}")
    
    except Exception as e:
        print_header("❌ Order Failed")
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nCancelled.")
        sys.exit(0)
