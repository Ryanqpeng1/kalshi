"""
Configuration file for Kalshi trading bot
Update the values below with your actual credentials
"""

# ===========================================
# API CREDENTIALS (UPDATE THESE)
# ===========================================

# Your API Key ID (from https://kalshi.com/account/profile)
API_KEY_ID = '7d8fae7e-7793-4f4f-a38e-abf1b597cd85'

# Path to your private key file (downloaded from Kalshi)
PRIVATE_KEY_PATH = '/Users/ryanpeng/kalshi/kalshi/private_key.txt'

# Environment: 'demo' for testing, 'production' for real trading
ENVIRONMENT = 'demo'

# ===========================================
# ORDER DEFAULTS (Customize as needed)
# ===========================================

# Default action: 'buy' or 'sell'
DEFAULT_ACTION = 'buy'

# Default side: 'yes' or 'no'
DEFAULT_SIDE = 'yes'

# Default number of contracts
DEFAULT_COUNT = 1

# Default price in cents (1-99)
DEFAULT_PRICE = 50

# ===========================================
# API ENDPOINTS
# ===========================================

REST_URLS = {
    'production': 'https://external-api.kalshi.com/trade-api/v2',
    'demo': 'https://external-api.demo.kalshi.co/trade-api/v2'
}

WS_URLS = {
    'production': 'wss://external-api-ws.kalshi.com/trade-api/ws/v2',
    'demo': 'wss://external-api-ws.demo.kalshi.co/trade-api/ws/v2'
}

# ===========================================
# LOGGING
# ===========================================

LOG_LEVEL = 'INFO'  # DEBUG, INFO, WARNING, ERROR, CRITICAL
