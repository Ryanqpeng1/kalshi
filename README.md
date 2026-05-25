# Kalshi Trading Bot

A modular, production-ready infrastructure for automated trading on Kalshi markets.

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Your Account

Edit `lol.py` and update `KalshiConfig`:

```python
class KalshiConfig:
    ENVIRONMENT = 'demo'  # or 'production'
    API_KEY_ID = 'your-api-key-id-here'  # Get from https://kalshi.com/account/profile
    PRIVATE_KEY_PATH = 'path/to/your/kalshi-key.key'
```

### 3. Generate API Keys

1. Log in to [Kalshi](https://kalshi.com) (or [demo](https://demo.kalshi.co))
2. Go to **Account & security → API Keys**
3. Click **Create Key**
4. Save your Private Key and API Key ID
5. Update the config above

### 4. Run Examples

```bash
# Get market data
python lol.py

# See the example_get_market_data() function
```

## Architecture

### Core Components

**`KalshiAuth`** - Handles RSA-PSS signing and authentication headers
- Loads private key from file
- Signs requests with required Kalshi format
- Generates WebSocket auth headers

**`KalshiClient`** - REST API wrapper
- `get_balance()` - Account balance
- `get_markets()` - List available markets
- `get_orderbook(ticker)` - Orderbook for a market
- `place_order()` - Create new order
- `cancel_order()` - Cancel existing order
- `get_positions()` - Current holdings

**`KalshiWebSocketClient`** - Real-time market data
- Connect with authentication
- Subscribe to channels: `ticker`, `orderbook_delta`, `fill`
- Listen for market updates in real-time

**`TradingBot`** - Base trading bot class
- Initialize with market data
- Connect to WebSocket
- Implement custom trading logic in `handle_market_update()`

## Usage Examples

### Get Account Balance

```python
config = KalshiConfig()
client = KalshiClient(config)
balance = client.get_balance()
print(f"Balance: ${balance['balance'] / 100:.2f}")
```

### Browse Markets

```python
# Get open markets for a series
markets = client.get_markets(series_ticker='KXHIGHNY', status='open')

for market in markets:
    orderbook = client.get_orderbook(market['ticker'])
    ob = orderbook['orderbook_fp']
    best_yes = ob['yes_dollars'][-1]  # Last = best bid
    print(f"{market['ticker']}: YES bid ${best_yes[0]}")
```

### Place an Order

```python
order = client.place_order(
    ticker='KXHARRIS24-LSV',
    side='yes',
    action='buy',
    count=10,
    price=42  # 42 cents
)
print(f"Order ID: {order['order']['order_id']}")
```

### Custom Trading Strategy

Extend `TradingBot` and override `handle_market_update()`:

```python
class MyBot(TradingBot):
    async def handle_market_update(self, data: Dict):
        msg_type = data.get('type')
        
        if msg_type == 'ticker':
            market = data['msg']['market_ticker']
            yes_bid = Decimal(data['msg']['yes_bid_dollars'])
            
            # Your trading logic here
            if yes_bid < Decimal('0.30'):
                # Buy if price is low
                self.client.place_order(
                    ticker=market,
                    side='yes',
                    action='buy',
                    count=5,
                    price=int(yes_bid * 100)
                )
        
        elif msg_type == 'fill':
            order_id = data['msg']['order_id']
            logger.info(f"Order filled: {order_id}")

# Run it
async def main():
    config = KalshiConfig()
    bot = MyBot(config)
    await bot.run()

asyncio.run(main())
```

## Key Concepts

### Binary Markets
- Each market has YES/NO outcomes
- Prices sum to $1.00
- If YES is $0.42, NO is $0.58
- Orders are placed at specific price points (1-99 cents)

### Order Placement
```python
order_data = {
    'ticker': 'MARKET_TICKER',
    'side': 'yes' | 'no',      # Which side you're buying
    'action': 'buy' | 'sell',  # Action direction
    'count': 10,               # Number of contracts
    'type': 'limit',           # limit or market
    'yes_price': 42,           # Price for YES side (1-99 cents)
    'client_order_id': uuid4() # For deduplication
}
```

### Orderbook Format
```python
{
    "orderbook_fp": {
        "yes_dollars": [
            ["0.41", "50"],   # Price: $0.41, Quantity: 50 contracts
            ["0.42", "100"],  # Best YES bid is last element
        ],
        "no_dollars": [
            ["0.58", "75"],
            ["0.59", "25"],   # Best NO bid
        ]
    }
}
```

### WebSocket Channels
- `ticker` - Market price/volume updates (all markets)
- `orderbook_delta` - Orderbook changes (requires market filter)
- `trade` - Public trades
- `fill` - Your order fills (requires auth)
- `market_positions` - Your position updates (requires auth)

## Rate Limits

Depends on your API tier (Basic, Premier, Market Maker). Check limits:

```python
limits = client._make_request('GET', '/account/api-limits')
```

## Demo vs Production

- **Demo**: No real money, test strategies safely
  - URL: `https://external-api.demo.kalshi.co/trade-api/v2`
  - WebSocket: `wss://external-api-ws.demo.kalshi.co/trade-api/ws/v2`

- **Production**: Real trading with real funds
  - URL: `https://external-api.kalshi.com/trade-api/v2`
  - WebSocket: `wss://external-api-ws.kalshi.com/trade-api/ws/v2`

## Troubleshooting

**401 Unauthorized**
- Check API Key ID and private key file path
- Ensure private key format is RSA PEM

**Signature Error**
- Timestamp must be in milliseconds (not seconds)
- Ensure path is signed WITHOUT query parameters
- Check system clock is accurate

**No Open Markets**
- Use `status='all'` instead of `status='open'`
- Try different series tickers
- Check market lifecycle

## Security Best Practices

1. **Never commit credentials** - Use environment variables or separate config files
2. **Secure key storage** - Don't share or expose private keys
3. **Use demo first** - Test strategies in demo before production
4. **Rate limiting** - Implement backoff for production usage
5. **Error handling** - Log errors but don't expose sensitive data

## Resources

- [Kalshi Docs](https://docs.kalshi.com)
- [Discord Community](https://discord.gg/kalshi)
- [API Reference](https://docs.kalshi.com/api-reference)
- [WebSocket Guide](https://docs.kalshi.com/getting_started/quick_start_websockets)

## License

MIT