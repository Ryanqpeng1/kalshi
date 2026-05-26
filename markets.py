"""
Market utilities for Kalshi trading bot
Provides functions to fetch and analyze market data
"""

import pandas as pd
from typing import Optional
from lol import KalshiClient, KalshiConfig
from config import API_KEY_ID, PRIVATE_KEY_PATH, ENVIRONMENT


def get_market_positions(volume_threshold: float = 0.0, limit: int = 100) -> pd.DataFrame:
    """
    Get all available market positions with trading activity
    
    Args:
        volume_threshold: Minimum volume to include (default 0.0, set to >0 for active markets only)
        limit: Maximum number of markets to fetch (default 100)
    
    Returns:
        DataFrame with columns:
            - ticker: Market ticker
            - title: Market title/description
            - volume: Trading volume in contracts
            - yes_bid_dollars: YES bid price in dollars
            - yes_ask_dollars: YES ask price in dollars
            - yes_spread: YES bid-ask spread
            - no_bid_dollars: NO bid price in dollars
            - no_ask_dollars: NO ask price in dollars
            - no_spread: NO bid-ask spread
            - status: Market status (open, paused, settled)
            - category: Series ticker/category
    
    Example:
        >>> df = get_market_positions(volume_threshold=10.0)
        >>> print(df[['ticker', 'title', 'volume']])
    """
    config = KalshiConfig()
    config.ENVIRONMENT = ENVIRONMENT
    config.API_KEY_ID = API_KEY_ID
    config.PRIVATE_KEY_PATH = PRIVATE_KEY_PATH
    
    client = KalshiClient(config)
    
    try:
        # Fetch all markets
        markets = client.get_markets(limit=limit)
        
        # Filter for volume > threshold
        filtered_markets = [
            m for m in markets 
            if float(m.get('volume_fp', 0)) > volume_threshold
        ]
        
        # Convert to DataFrame
        data = []
        for market in filtered_markets:
            yes_bid = float(market.get('yes_bid_dollars', 0))
            yes_ask = float(market.get('yes_ask_dollars', 0))
            no_bid = float(market.get('no_bid_dollars', 0))
            no_ask = float(market.get('no_ask_dollars', 0))
            
            data.append({
                'ticker': market.get('ticker'),
                'title': market.get('title'),
                'volume': float(market.get('volume_fp', 0)),
                'yes_bid_dollars': yes_bid,
                'yes_ask_dollars': yes_ask,
                'yes_spread': yes_ask - yes_bid,
                'no_bid_dollars': no_bid,
                'no_ask_dollars': no_ask,
                'no_spread': no_ask - no_bid,
                'status': market.get('status'),
                'category': market.get('series_ticker'),
                'result': market.get('result'),
                'created_at': market.get('created_at'),
                'expires_at': market.get('expires_at'),
            })
        
        df = pd.DataFrame(data)
        
        # Sort by volume descending
        if not df.empty:
            df = df.sort_values('volume', ascending=False).reset_index(drop=True)
        
        return df
    
    except Exception as e:
        print(f"Error fetching markets: {e}")
        return pd.DataFrame()


def get_lol_positions(volume_threshold: float = 0.0, limit: int = 100) -> pd.DataFrame:
    """
    Get all available League of Legends market positions
    
    Filters for markets with KXLOL ticker prefix (Kalshi's sports market classification).
    League of Legends markets follow the pattern KXLOL[event-details].
    
    Args:
        volume_threshold: Minimum volume to include (default 0.0, set to >0 for active LoL markets only)
        limit: Maximum number of markets to fetch (default 100)
    
    Returns:
        DataFrame with same structure as get_market_positions(), filtered for LoL markets
            - ticker, title, volume, yes_bid_dollars, yes_ask_dollars, yes_spread
            - no_bid_dollars, no_ask_dollars, no_spread, status, category, etc.
    
    Example:
        >>> df = get_lol_positions(volume_threshold=1.0)
        >>> print(df[['ticker', 'title', 'volume']])
    """
    config = KalshiConfig()
    config.ENVIRONMENT = ENVIRONMENT
    config.API_KEY_ID = API_KEY_ID
    config.PRIVATE_KEY_PATH = PRIVATE_KEY_PATH
    
    client = KalshiClient(config)
    
    try:
        # Fetch all markets
        markets = client.get_markets(limit=limit)
        
        # Filter for LoL markets by ticker prefix (KXLOL is sports classification for League of Legends)
        lol_markets = [
            m for m in markets 
            if m.get('ticker', '').startswith('KXLOL')
        ]
        
        # Filter for volume > threshold
        filtered_markets = [
            m for m in lol_markets 
            if float(m.get('volume_fp', 0)) > volume_threshold
        ]
        
        # Convert to DataFrame
        data = []
        for market in filtered_markets:
            yes_bid = float(market.get('yes_bid_dollars', 0))
            yes_ask = float(market.get('yes_ask_dollars', 0))
            no_bid = float(market.get('no_bid_dollars', 0))
            no_ask = float(market.get('no_ask_dollars', 0))
            
            data.append({
                'ticker': market.get('ticker'),
                'title': market.get('title'),
                'volume': float(market.get('volume_fp', 0)),
                'yes_bid_dollars': yes_bid,
                'yes_ask_dollars': yes_ask,
                'yes_spread': yes_ask - yes_bid,
                'no_bid_dollars': no_bid,
                'no_ask_dollars': no_ask,
                'no_spread': no_ask - no_bid,
                'status': market.get('status'),
                'category': market.get('series_ticker'),
                'result': market.get('result'),
                'created_at': market.get('created_at'),
                'expires_at': market.get('expires_at'),
            })
        
        df = pd.DataFrame(data)
        
        # Sort by volume descending
        if not df.empty:
            df = df.sort_values('volume', ascending=False).reset_index(drop=True)
        
        return df
    
    except Exception as e:
        print(f"Error fetching LoL markets: {e}")
        return pd.DataFrame()


def get_sport_positions(sport_ticker: str, volume_threshold: float = 0.0, limit: int = 100) -> pd.DataFrame:
    """
    Get market positions for any sport
    
    Kalshi uses ticker prefixes to classify sports:
    - KXNBA: NBA Basketball
    - KXMLB: MLB Baseball  
    - KXNFL: NFL Football
    - KXUFC: UFC Fighting
    - KXLOL: League of Legends esports
    - KXTENNISMATCH: Tennis matches
    - etc.
    
    Args:
        sport_ticker: Sport classification prefix (e.g., 'KXNBA', 'KXLOL', 'KXMLB')
        volume_threshold: Minimum volume to include (default 0.0)
        limit: Maximum number of markets to fetch (default 100)
    
    Returns:
        DataFrame with market positions for specified sport
    
    Example:
        >>> nba = get_sport_positions('KXNBA', volume_threshold=10.0)
        >>> lol = get_sport_positions('KXLOL', volume_threshold=1.0)
    """
    config = KalshiConfig()
    config.ENVIRONMENT = ENVIRONMENT
    config.API_KEY_ID = API_KEY_ID
    config.PRIVATE_KEY_PATH = PRIVATE_KEY_PATH
    
    client = KalshiClient(config)
    
    try:
        # Fetch all markets
        markets = client.get_markets(limit=limit)
        
        # Filter for sport by ticker prefix
        sport_markets = [
            m for m in markets 
            if m.get('ticker', '').startswith(sport_ticker)
        ]
        
        # Filter for volume > threshold
        filtered_markets = [
            m for m in sport_markets 
            if float(m.get('volume_fp', 0)) > volume_threshold
        ]
        
        # Convert to DataFrame
        data = []
        for market in filtered_markets:
            yes_bid = float(market.get('yes_bid_dollars', 0))
            yes_ask = float(market.get('yes_ask_dollars', 0))
            no_bid = float(market.get('no_bid_dollars', 0))
            no_ask = float(market.get('no_ask_dollars', 0))
            
            data.append({
                'ticker': market.get('ticker'),
                'title': market.get('title'),
                'volume': float(market.get('volume_fp', 0)),
                'yes_bid_dollars': yes_bid,
                'yes_ask_dollars': yes_ask,
                'yes_spread': yes_ask - yes_bid,
                'no_bid_dollars': no_bid,
                'no_ask_dollars': no_ask,
                'no_spread': no_ask - no_bid,
                'status': market.get('status'),
                'category': market.get('series_ticker'),
                'result': market.get('result'),
                'created_at': market.get('created_at'),
                'expires_at': market.get('expires_at'),
            })
        
        df = pd.DataFrame(data)
        
        # Sort by volume descending
        if not df.empty:
            df = df.sort_values('volume', ascending=False).reset_index(drop=True)
        
        return df
    
    except Exception as e:
        print(f"Error fetching {sport_ticker} markets: {e}")
        return pd.DataFrame()


def get_active_markets(volume_threshold: float = 1.0) -> pd.DataFrame:
    """
    Convenience function to get only active markets (volume > threshold)
    
    Args:
        volume_threshold: Minimum volume threshold (default 1.0)
    
    Returns:
        DataFrame of active markets sorted by volume
    """
    return get_market_positions(volume_threshold=volume_threshold)


def get_market_spread(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate bid-ask spread for all markets in DataFrame
    
    Args:
        df: DataFrame from get_market_positions()
    
    Returns:
        DataFrame with additional columns:
            - yes_spread: YES bid-ask spread in cents
            - no_spread: NO bid-ask spread in cents
            - mid_price_yes: Midpoint of YES market
            - mid_price_no: Midpoint of NO market
    """
    df = df.copy()
    df['yes_spread'] = (df['yes_ask_dollars'] - df['yes_bid_dollars']) * 100
    df['no_spread'] = (df['no_ask_dollars'] - df['no_bid_dollars']) * 100
    df['mid_price_yes'] = (df['yes_bid_dollars'] + df['yes_ask_dollars']) / 2 * 100
    df['mid_price_no'] = (df['no_bid_dollars'] + df['no_ask_dollars']) / 2 * 100
    return df


if __name__ == '__main__':
    # Example usage
    print("Fetching all markets with volume > 0...")
    df = get_market_positions(volume_threshold=0.0)
    
    if not df.empty:
        print(f"\nFound {len(df)} markets")
        print("\nTop 10 markets by volume:")
        print(df[['ticker', 'title', 'volume', 'yes_bid_dollars', 'status']].head(10).to_string())
        
        print("\n\nActive markets (volume > 1):")
        active = get_active_markets(volume_threshold=1.0)
        if not active.empty:
            print(f"Found {len(active)} active markets")
            print(active[['ticker', 'title', 'volume']].head(10).to_string())
    else:
        print("No markets found")
