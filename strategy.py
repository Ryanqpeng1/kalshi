"""
Base strategy class for Kalshi trading bot
Extend this class to implement your own trading strategies
"""

from typing import Optional, List, Dict, Any
import pandas as pd
from lol import KalshiClient


class BaseStrategy:
    """
    Momentum trading strategy - default implementation
    
    Tracks volume changes across cycles and trades markets with increasing momentum.
    Extend this class to implement custom trading logic by overriding analyze().
    """
    
    def __init__(self, client: KalshiClient, name: str = "Momentum Strategy", 
                 min_volume: float = 10.0, momentum_threshold: float = 1.1):
        """
        Initialize momentum strategy
        
        Args:
            client: KalshiClient instance for API calls
            name: Strategy name for logging
            min_volume: Minimum market volume to trade
            momentum_threshold: Volume increase ratio to trigger trade (1.1 = 10% increase)
        """
        self.client = client
        self.name = name
        self.min_volume = min_volume
        self.momentum_threshold = momentum_threshold
        self.positions = []
        self.last_volumes = {}
    
    def analyze(self, markets_df: pd.DataFrame) -> List[Dict[str, Any]]:
        """
        Momentum trading: buy markets with increasing volume
        
        Args:
            markets_df: DataFrame from get_market_positions() with all market data
        
        Returns:
            List of order dictionaries to place
        
        Override this method to implement custom trading logic:
            
            def analyze(self, markets_df):
                # Find markets with wide spreads
                wide_spreads = markets_df[markets_df['yes_spread'] > 5]
                
                orders = []
                for _, market in wide_spreads.iterrows():
                    orders.append({
                        'ticker': market['ticker'],
                        'side': 'yes',
                        'action': 'buy',
                        'count': 1,
                        'price': market['yes_bid_dollars'] * 100
                    })
                return orders
        """
        orders = []
        
        # Filter for minimum volume
        high_vol = markets_df[markets_df['volume'] >= self.min_volume]
        
        if high_vol.empty:
            return orders
        
        # Track volume momentum across cycles
        for _, market in high_vol.iterrows():
            ticker = market['ticker']
            current_vol = market['volume']
            
            # Skip if first time seeing this market
            if ticker not in self.last_volumes:
                self.last_volumes[ticker] = current_vol
                continue
            
            prev_vol = self.last_volumes[ticker]
            self.last_volumes[ticker] = current_vol
            
            # If volume increased past threshold, buy YES (market heating up)
            if current_vol > prev_vol * self.momentum_threshold:
                orders.append({
                    'ticker': ticker,
                    'side': 'yes',
                    'action': 'buy',
                    'count': 1,
                    'price': int(market['yes_bid_dollars'] * 100)
                })
        
        return orders
    
    def execute_orders(self, orders: List[Dict[str, Any]]) -> List[str]:
        """
        Execute list of orders
        
        Args:
            orders: List of order dictionaries
        
        Returns:
            List of order IDs
        """
        order_ids = []
        for order in orders:
            try:
                result = self.client.place_order(
                    ticker=order['ticker'],
                    side=order['side'],
                    action=order['action'],
                    count=order['count'],
                    price=int(order['price'])
                )
                order_ids.append(result)
                print(f"Order placed: {order['side'].upper()} {order['count']} {order['ticker'][:20]} @ ${order['price']}")
            except Exception as e:
                print(f"Failed to place order: {e}")
        
        return order_ids
    
    def cancel_orders(self, order_ids: List[str]) -> int:
        """
        Cancel list of orders
        
        Args:
            order_ids: List of order IDs to cancel
        
        Returns:
            Number of successfully cancelled orders
        """
        cancelled = 0
        for order_id in order_ids:
            try:
                self.client.cancel_order(order_id)
                cancelled += 1
            except Exception as e:
                print(f"Failed to cancel order {order_id}: {e}")
        
        return cancelled
    
    def get_positions(self) -> pd.DataFrame:
        """
        Get current positions
        
        Returns:
            DataFrame of current holdings
        """
        try:
            positions = self.client.get_positions()
            return pd.DataFrame(positions)
        except Exception as e:
            print(f"Error fetching positions: {e}")
            return pd.DataFrame()
    
    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}: {self.name}>"
