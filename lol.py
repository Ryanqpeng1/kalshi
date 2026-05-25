"""
Kalshi Automated Trading Bot
A basic infrastructure for placing orders on Kalshi markets
"""

import asyncio
import json
import base64
import uuid
import time
import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from decimal import Decimal
import requests
import websockets
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric import padding
from urllib.parse import urlparse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class KalshiConfig:
    """Configuration for Kalshi API access"""
    
    # =========================
    # ACCOUNT-SPECIFIC SETTINGS
    # =========================
    
    # API Environment: 'production' or 'demo'
    ENVIRONMENT = 'demo'
    
    # Your API Key ID (UUID format)
    API_KEY_ID = 'your-api-key-id-here'
    
    # Path to your private key file
    PRIVATE_KEY_PATH = 'path/to/your/kalshi-key.key'
    
    # =========================
    # API ENDPOINTS
    # =========================
    
    REST_URLS = {
        'production': 'https://external-api.kalshi.com/trade-api/v2',
        'demo': 'https://external-api.demo.kalshi.co/trade-api/v2'
    }
    
    WS_URLS = {
        'production': 'wss://external-api-ws.kalshi.com/trade-api/ws/v2',
        'demo': 'wss://external-api-ws.demo.kalshi.co/trade-api/ws/v2'
    }
    
    @property
    def REST_URL(self) -> str:
        return self.REST_URLS[self.ENVIRONMENT]
    
    @property
    def WS_URL(self) -> str:
        return self.WS_URLS[self.ENVIRONMENT]


class KalshiAuth:
    """Handle Kalshi API authentication and request signing"""
    
    def __init__(self, api_key_id: str, private_key_path: str):
        self.api_key_id = api_key_id
        self.private_key = self._load_private_key(private_key_path)
    
    @staticmethod
    def _load_private_key(key_path: str):
        """Load RSA private key from file"""
        try:
            with open(key_path, 'rb') as f:
                return serialization.load_pem_private_key(
                    f.read(),
                    password=None,
                    backend=default_backend()
                )
        except FileNotFoundError:
            raise ValueError(f"Private key file not found: {key_path}")
        except Exception as e:
            raise ValueError(f"Failed to load private key: {e}")
    
    def _sign_message(self, message: str) -> str:
        """Sign a message using RSA-PSS with SHA256"""
        msg_bytes = message.encode('utf-8')
        signature = self.private_key.sign(
            msg_bytes,
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.DIGEST_LENGTH
            ),
            hashes.SHA256()
        )
        return base64.b64encode(signature).decode('utf-8')
    
    def get_headers(self, method: str, path: str) -> Dict[str, str]:
        """Generate authenticated request headers"""
        timestamp = str(int(time.time() * 1000))
        
        # Strip query parameters from path before signing
        path_to_sign = path.split('?')[0]
        msg_string = f"{timestamp}{method}{path_to_sign}"
        signature = self._sign_message(msg_string)
        
        return {
            'KALSHI-ACCESS-KEY': self.api_key_id,
            'KALSHI-ACCESS-SIGNATURE': signature,
            'KALSHI-ACCESS-TIMESTAMP': timestamp,
            'Content-Type': 'application/json'
        }
    
    def get_ws_headers(self, path: str = '/trade-api/ws/v2') -> Dict[str, str]:
        """Generate WebSocket authentication headers"""
        return self.get_headers('GET', path)


class KalshiClient:
    """Client for Kalshi API interactions"""
    
    def __init__(self, config: KalshiConfig):
        self.config = config
        self.auth = KalshiAuth(config.API_KEY_ID, config.PRIVATE_KEY_PATH)
        self.base_url = config.REST_URL
    
    def _make_request(self, method: str, path: str, data: Optional[Dict] = None) -> Dict:
        """Make authenticated request to Kalshi API"""
        url = f"{self.base_url}{path}"
        # Use the full request path (including any base path like /trade-api/v2)
        # when generating the signature, since the server expects the absolute
        # request path without query params.
        parsed = urlparse(url)
        path_to_sign = parsed.path
        headers = self.auth.get_headers(method, path_to_sign)
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers)
            elif method == 'POST':
                response = requests.post(url, headers=headers, json=data)
            elif method == 'PUT':
                response = requests.put(url, headers=headers, json=data)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers)
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            response.raise_for_status()
            return response.json() if response.text else {}
        
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed: {method} {path} - {e}")
            raise
    
    def get_balance(self) -> Dict:
        """Get account balance in cents"""
        return self._make_request('GET', '/portfolio/balance')
    
    def get_markets(self, series_ticker: Optional[str] = None, 
                   status: Optional[str] = None, limit: int = 100) -> List[Dict]:
        """Get available markets"""
        params = []
        if series_ticker:
            params.append(f"series_ticker={series_ticker}")
        if status:
            params.append(f"status={status}")
        params.append(f"limit={limit}")
        
        path = '/markets?' + '&'.join(params) if params else '/markets'
        result = self._make_request('GET', path)
        return result.get('markets', [])
    
    def get_market(self, ticker: str) -> Dict:
        """Get single market details"""
        return self._make_request('GET', f'/markets/{ticker}')
    
    def get_orderbook(self, ticker: str) -> Dict:
        """Get orderbook for a market (public endpoint, no auth needed)"""
        url = f"{self.base_url}/markets/{ticker}/orderbook"
        try:
            response = requests.get(url)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch orderbook for {ticker}: {e}")
            raise
    
    def get_orders(self, status: Optional[str] = None) -> List[Dict]:
        """Get all orders"""
        path = '/portfolio/orders'
        if status:
            path += f"?status={status}"
        result = self._make_request('GET', path)
        return result.get('orders', [])
    
    def get_order(self, order_id: str) -> Dict:
        """Get single order details"""
        return self._make_request('GET', f'/portfolio/orders/{order_id}')
    
    def place_order(self, ticker: str, side: str, action: str, 
                   count: int, price: int, order_type: str = 'limit') -> Dict:
        """
        Place an order on Kalshi
        
        Args:
            ticker: Market ticker
            side: 'yes' or 'no'
            action: 'buy' or 'sell'
            count: Number of contracts
            price: Price in cents (1-99)
            order_type: 'limit' or 'market'
        
        Returns:
            Order confirmation
        """
        if price < 1 or price > 99:
            raise ValueError("Price must be between 1 and 99 cents")
        
        order_data = {
            'ticker': ticker,
            'side': side,
            'action': action,
            'count': count,
            'type': order_type,
            'yes_price': price if side == 'yes' else 100 - price,
            'client_order_id': str(uuid.uuid4())  # For deduplication
        }
        
        logger.info(f"Placing order: {order_data}")
        return self._make_request('POST', '/portfolio/orders', order_data)
    
    def cancel_order(self, order_id: str) -> Dict:
        """Cancel an order"""
        logger.info(f"Cancelling order: {order_id}")
        return self._make_request('DELETE', f'/portfolio/orders/{order_id}')
    
    def amend_order(self, order_id: str, count: Optional[int] = None, 
                   price: Optional[int] = None) -> Dict:
        """Amend an existing order"""
        data = {}
        if count is not None:
            data['count'] = count
        if price is not None:
            data['price'] = price
        
        logger.info(f"Amending order {order_id}: {data}")
        return self._make_request('PUT', f'/portfolio/orders/{order_id}', data)
    
    def get_positions(self) -> List[Dict]:
        """Get all positions"""
        result = self._make_request('GET', '/portfolio/positions')
        return result.get('positions', [])


class KalshiWebSocketClient:
    """WebSocket client for real-time market updates"""
    
    def __init__(self, config: KalshiConfig):
        self.config = config
        self.auth = KalshiAuth(config.API_KEY_ID, config.PRIVATE_KEY_PATH)
        self.ws = None
        self.message_id = 1
    
    async def connect(self):
        """Establish WebSocket connection"""
        headers = self.auth.get_ws_headers()
        try:
            self.ws = await websockets.connect(
                self.config.WS_URL,
                additional_headers=headers
            )
            logger.info("WebSocket connected")
        except Exception as e:
            logger.error(f"WebSocket connection failed: {e}")
            raise
    
    async def disconnect(self):
        """Close WebSocket connection"""
        if self.ws:
            await self.ws.close()
            logger.info("WebSocket disconnected")
    
    async def subscribe_to_ticker(self):
        """Subscribe to all market ticker updates"""
        subscription = {
            'id': self.message_id,
            'cmd': 'subscribe',
            'params': {'channels': ['ticker']}
        }
        self.message_id += 1
        await self.ws.send(json.dumps(subscription))
        logger.info("Subscribed to ticker channel")
    
    async def subscribe_to_orderbook(self, market_tickers: List[str]):
        """Subscribe to orderbook updates for specific markets"""
        subscription = {
            'id': self.message_id,
            'cmd': 'subscribe',
            'params': {
                'channels': ['orderbook_delta'],
                'market_tickers': market_tickers
            }
        }
        self.message_id += 1
        await self.ws.send(json.dumps(subscription))
        logger.info(f"Subscribed to orderbook for: {market_tickers}")
    
    async def subscribe_to_fills(self):
        """Subscribe to order fill notifications"""
        subscription = {
            'id': self.message_id,
            'cmd': 'subscribe',
            'params': {'channels': ['fill']}
        }
        self.message_id += 1
        await self.ws.send(json.dumps(subscription))
        logger.info("Subscribed to fills channel")
    
    async def listen(self, callback=None):
        """Listen for WebSocket messages"""
        try:
            async for message in self.ws:
                data = json.loads(message)
                logger.debug(f"Received: {data.get('type')}")
                
                if callback:
                    await callback(data)
        except Exception as e:
            logger.error(f"WebSocket error: {e}")


class TradingBot:
    """Base trading bot class - extend this for custom strategies"""
    
    def __init__(self, config: KalshiConfig):
        self.config = config
        self.client = KalshiClient(config)
        self.ws_client = KalshiWebSocketClient(config)
        self.positions = {}
        self.running = False
    
    async def initialize(self):
        """Initialize bot - fetch initial data"""
        try:
            balance = self.client.get_balance()
            logger.info(f"Account balance: ${balance['balance'] / 100:.2f}")
            
            positions = self.client.get_positions()
            for pos in positions:
                self.positions[pos['ticker']] = pos
            
            logger.info(f"Loaded {len(positions)} positions")
        except Exception as e:
            logger.error(f"Initialization failed: {e}")
            raise
    
    async def connect_websocket(self):
        """Connect to WebSocket and subscribe to channels"""
        try:
            await self.ws_client.connect()
            await self.ws_client.subscribe_to_ticker()
            await self.ws_client.subscribe_to_fills()
        except Exception as e:
            logger.error(f"WebSocket connection failed: {e}")
            raise
    
    async def handle_market_update(self, data: Dict):
        """Override this method to implement custom trading logic"""
        msg_type = data.get('type')
        
        if msg_type == 'ticker':
            # Handle ticker update
            market_ticker = data.get('msg', {}).get('market_ticker')
            yes_bid = data.get('msg', {}).get('yes_bid_dollars')
            logger.debug(f"Ticker: {market_ticker} - YES bid: ${yes_bid}")
        
        elif msg_type == 'fill':
            # Handle order fill
            order_id = data.get('msg', {}).get('order_id')
            logger.info(f"Order filled: {order_id}")
        
        elif msg_type == 'error':
            error_code = data.get('msg', {}).get('code')
            error_msg = data.get('msg', {}).get('msg')
            logger.error(f"WebSocket error {error_code}: {error_msg}")
    
    async def run(self):
        """Run the trading bot"""
        try:
            self.running = True
            await self.initialize()
            await self.connect_websocket()
            
            logger.info("Trading bot started")
            await self.ws_client.listen(callback=self.handle_market_update)
        
        except KeyboardInterrupt:
            logger.info("Shutting down...")
        except Exception as e:
            logger.error(f"Bot error: {e}")
        finally:
            self.running = False
            await self.ws_client.disconnect()
            logger.info("Trading bot stopped")


# ========================
# EXAMPLE USAGE
# ========================

async def main():
    """Example: Initialize bot and stream market data"""
    
    # Configure your account
    config = KalshiConfig()
    
    # Create bot instance
    bot = TradingBot(config)
    
    # Run bot (listens for market updates)
    await bot.run()


def example_place_order():
    """Example: Place a single order"""
    
    config = KalshiConfig()
    client = KalshiClient(config)
    
    try:
        # Get a market
        markets = client.get_markets(status='open', limit=1)
        if not markets:
            print("No open markets available")
            return
        
        market = markets[0]
        print(f"Selected market: {market['ticker']} - {market['title']}")
        
        # Place order: buy 1 YES contract at 30 cents
        order = client.place_order(
            ticker=market['ticker'],
            side='yes',
            action='buy',
            count=1,
            price=30
        )
        
        print(f"Order placed: {order['order']['order_id']}")
    
    except Exception as e:
        logger.error(f"Failed to place order: {e}")


def example_get_market_data():
    """Example: Fetch market data without placing orders"""
    
    config = KalshiConfig()
    client = KalshiClient(config)
    
    try:
        # Get markets for a specific series
        markets = client.get_markets(series_ticker='KXHIGHNY', status='open', limit=5)
        print(f"\nFound {len(markets)} open markets:")
        
        for market in markets:
            print(f"\n{market['ticker']}: {market['title']}")
            print(f"  YES bid: ${market.get('yes_bid_dollars', 'N/A')}")
            print(f"  Volume: {market.get('volume_fp', 'N/A')}")
            
            # Get orderbook
            orderbook = client.get_orderbook(market['ticker'])
            if 'orderbook_fp' in orderbook:
                ob = orderbook['orderbook_fp']
                if ob.get('yes_dollars'):
                    best_yes = ob['yes_dollars'][-1]
                    print(f"  Best YES bid: ${best_yes[0]}, volume: {best_yes[1]}")
    
    except Exception as e:
        logger.error(f"Failed to fetch market data: {e}")


if __name__ == '__main__':
    # Choose which example to run:
    
    # Option 1: Get market data
    # example_get_market_data()
    
    # Option 2: Place an order
    # example_place_order()
    
    # Option 3: Run trading bot with real-time updates
    # asyncio.run(main())
    
    print("Trading bot infrastructure ready!")
    print("\nTo get started:")
    print("1. Update KalshiConfig with your API credentials")
    print("2. Uncomment one of the example functions in __main__")
    print("3. Run: python lol.py")
