# Quick Start Guide

## Step 1: Configure Your Credentials

Run the setup wizard:

```bash
python setup.py
```

This will ask you for:
1. **API Key ID** - From https://kalshi.com/account/profile
2. **Private Key Path** - Path to your `.key` file
3. **Environment** - `demo` (test) or `production` (real money)

The setup wizard will update `config.py` with your credentials.

## Step 2: Run Your First Command

### Get Account Balance

```bash
python get_balance.py
```

Example output:
```
==================================================
  Kalshi Account Balance (demo)
==================================================

Balance: $1,000.00
```

### Browse Markets

```bash
python browse_markets.py
```

Or filter by series and status:

```bash
python browse_markets.py KXHIGHNY open
```

Example output:
```
Ticker                    Title                          YES Bid    Volume    
-----
KXHIGHNY-26MAY-71        Will NYC hit 71+ degrees?      $0.45      1234.00
KXHIGHNY-26MAY-75        Will NYC hit 75+ degrees?      $0.22      567.00
```

### Place an Order

**Interactive mode** (recommended for first time):

```bash
python place_order.py
```

You'll be asked:
- Market ticker
- Side (yes/no)
- Action (buy/sell)
- Number of contracts
- Price in cents

**Command line mode** (for scripting):

```bash
python place_order.py KXHARRIS24-LSV yes buy 5 42
```

## Configuration File

Edit `config.py` to change defaults:

```python
# Default values for orders
DEFAULT_ACTION = 'buy'
DEFAULT_SIDE = 'yes'
DEFAULT_COUNT = 1
DEFAULT_PRICE = 50
```

## Available Scripts

| Script | Purpose | Usage |
|--------|---------|-------|
| `setup.py` | Configure API credentials | `python setup.py` |
| `get_balance.py` | Check account balance | `python get_balance.py` |
| `browse_markets.py` | List available markets | `python browse_markets.py [series] [status]` |
| `place_order.py` | Place a new order | `python place_order.py [args...]` |

## Common Issues

### "API credentials not configured"
Run `python setup.py` first to configure your credentials.

### "File not found: kalshi-key.key"
Make sure you've downloaded your private key from Kalshi and saved it in the right location. Check the path in `config.py`.

### "401 Unauthorized"
Your API credentials are incorrect. Run `python setup.py` again and verify your API Key ID and private key file.

### "No open markets"
Try `python browse_markets.py SERIES all` to see all markets (not just open ones).

## Examples

### Place a buy order

```bash
python place_order.py KXHARRIS24-LSV yes buy 10 45
```
This places a buy order for 10 YES contracts at $0.45

### Place a sell order

```bash
python place_order.py KXHARRIS24-LSV no sell 5 30
```
This places a sell order for 5 NO contracts at $0.30

### Check balance before trading

```bash
python get_balance.py
```

### Browse a specific market series

```bash
python browse_markets.py KXVOTE all
```

## Troubleshooting

### Check logs
All scripts log information to the console. Look for error messages.

### Test with demo
Always test in demo environment first:
- In `setup.py`, choose option 1 (demo)
- Or edit `config.py` and set `ENVIRONMENT = 'demo'`

### Validate credentials
Make sure your credentials are correct:
1. API Key ID is a UUID
2. Private key file is in PEM format
3. Private key file path is correct

## Next Steps

1. ✅ Run `setup.py` to configure
2. ✅ Run `get_balance.py` to verify connection
3. ✅ Run `browse_markets.py` to see markets
4. ✅ Run `place_order.py` to place your first order

For more details on the trading bot framework, see [README.md](README.md).
