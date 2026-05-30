"""
Example trading strategies for Kalshi bot

These are template strategies showing how to implement the BaseStrategy class
"""

import pandas as pd
from typing import List, Dict, Any
from strategy import BaseStrategy


class SpreadTradingStrategy(BaseStrategy):
    """
    Simple strategy that trades wide bid-ask spreads
    
    Looks for markets where YES or NO side has spread > threshold
    Buys the bid side and sells the ask side for quick profit
    """
    
    def __init__(self, client, name: str = "Spread Trading", 
                 min_spread: float = 0.02, min_volume: float = 10.0):
        """
        Initialize spread trading strategy
        
        Args:
            client: KalshiClient
            name: Strategy name
            min_spread: Minimum spread to trade (dollars)
            min_volume: Minimum market volume to trade
        """
        super().__init__(client, name)
        self.min_spread = min_spread
        self.min_volume = min_volume
    
    def analyze(self, markets_df: pd.DataFrame) -> List[Dict[str, Any]]:
        """
        Find markets with wide spreads and generate buy orders
        """
        orders = []
        
        # Filter by volume
        active_markets = markets_df[markets_df['volume'] >= self.min_volume]
        
        if active_markets.empty:
            return orders
        
        # Find markets with wide YES spreads
        yes_wide = active_markets[active_markets['yes_spread'] >= self.min_spread]
        
        for _, market in yes_wide.iterrows():
            # Buy the YES bid (lower price)
            orders.append({
                'ticker': market['ticker'],
                'side': 'yes',
                'action': 'buy',
                'count': 1,
                'price': market['yes_bid_dollars'] * 100
            })
        
        # Find markets with wide NO spreads
        no_wide = active_markets[active_markets['no_spread'] >= self.min_spread]
        
        for _, market in no_wide.iterrows():
            # Buy the NO bid (lower price)
            orders.append({
                'ticker': market['ticker'],
                'side': 'no',
                'action': 'buy',
                'count': 1,
                'price': market['no_bid_dollars'] * 100
            })
        
        return orders


class HighVolumeStrategy(BaseStrategy):
    """
    Trade only the highest volume markets
    
    Focuses on most liquid markets for better execution
    """
    
    def __init__(self, client, name: str = "High Volume", top_n: int = 5):
        """
        Initialize high volume strategy
        
        Args:
            client: KalshiClient
            name: Strategy name
            top_n: Number of top volume markets to trade
        """
        super().__init__(client, name)
        self.top_n = top_n
    
    def analyze(self, markets_df: pd.DataFrame) -> List[Dict[str, Any]]:
        """
        Trade top volume markets
        """
        if markets_df.empty:
            return []
        
        orders = []
        
        # Get top N by volume
        top_markets = markets_df.nlargest(self.top_n, 'volume')
        
        for _, market in top_markets.iterrows():
            # Simple strategy: buy at mid-price if YES is undervalued
            yes_mid = (market['yes_bid_dollars'] + market['yes_ask_dollars']) / 2
            
            if yes_mid < 0.5:  # YES is cheap, might be opportunity
                orders.append({
                    'ticker': market['ticker'],
                    'side': 'yes',
                    'action': 'buy',
                    'count': 1,
                    'price': int(yes_mid * 100)
                })
        
        return orders


class LOLOnlyStrategy(BaseStrategy):
    """
    Only trades League of Legends markets
    
    Specializes in esports prediction markets
    """
    
    def __init__(self, client, name: str = "LoL Only"):
        super().__init__(client, name)
    
    def analyze(self, markets_df: pd.DataFrame) -> List[Dict[str, Any]]:
        """
        Trade only LoL markets with wide spreads
        """
        from markets import filter_by_sport
        
        # Filter to LoL only
        lol_markets = filter_by_sport(markets_df, 'lol')
        
        if lol_markets.empty:
            return []
        
        orders = []
        
        # Trade spreads > 0.05 in LoL markets
        wide_spreads = lol_markets[
            (lol_markets['yes_spread'] >= 0.05) | 
            (lol_markets['no_spread'] >= 0.05)
        ]
        
        for _, market in wide_spreads.iterrows():
            if market['yes_spread'] >= market['no_spread']:
                orders.append({
                    'ticker': market['ticker'],
                    'side': 'yes',
                    'action': 'buy',
                    'count': 1,
                    'price': int(market['yes_bid_dollars'] * 100)
                })
            else:
                orders.append({
                    'ticker': market['ticker'],
                    'side': 'no',
                    'action': 'buy',
                    'count': 1,
                    'price': int(market['no_bid_dollars'] * 100)
                })
        
        return orders


class MomentumStrategy(BaseStrategy):
    """
    Simple momentum trading strategy
    
    Buys sides with recent volume momentum
    (In production, track historical volumes across cycles)
    """
    
    def __init__(self, client, name: str = "Momentum"):
        super().__init__(client, name)
        self.last_volumes = {}
    
    def analyze(self, markets_df: pd.DataFrame) -> List[Dict[str, Any]]:
        """
        Track volume changes and trade increasing volume markets
        """
        orders = []
        
        # Filter high volume markets
        high_vol = markets_df[markets_df['volume'] > 50]
        
        for _, market in high_vol.iterrows():
            ticker = market['ticker']
            current_vol = market['volume']
            
            # Track momentum (simplified - would need real historical data)
            if ticker not in self.last_volumes:
                self.last_volumes[ticker] = current_vol
                continue
            
            prev_vol = self.last_volumes[ticker]
            self.last_volumes[ticker] = current_vol
            
            # If volume increasing, buy YES (market getting more active)
            if current_vol > prev_vol * 1.1:  # 10% increase
                orders.append({
                    'ticker': ticker,
                    'side': 'yes',
                    'action': 'buy',
                    'count': 1,
                    'price': int(market['yes_bid_dollars'] * 100)
                })
        
        return orders
