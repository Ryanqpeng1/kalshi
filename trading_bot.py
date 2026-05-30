"""
Main Kalshi Trading Bot
Runs trading strategies with time limits and monitoring
"""

import time
import signal
import logging
from typing import List, Type, Optional
from datetime import datetime, timedelta
import pandas as pd
from lol import KalshiClient, KalshiConfig
from markets import get_market_positions
from strategy import BaseStrategy
from config import API_KEY_ID, PRIVATE_KEY_PATH, ENVIRONMENT

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TradingBotConfig:
    """Configuration for trading bot"""
    
    def __init__(self):
        # Time limit in seconds (default 5 minutes)
        self.MAX_RUN_TIME = 300
        
        # Market update frequency (seconds)
        self.MARKET_UPDATE_INTERVAL = 5
        
        # Whether to actually place orders
        self.DRY_RUN = False
        
        # Log positions every N cycles
        self.LOG_POSITIONS_EVERY = 10
        
        # Environment
        self.ENVIRONMENT = ENVIRONMENT
        self.API_KEY_ID = API_KEY_ID
        self.PRIVATE_KEY_PATH = PRIVATE_KEY_PATH


class TradingBot:
    """
    Main trading bot that runs strategies
    
    Example usage:
        bot = TradingBot(config=TradingBotConfig())
        
        # Load strategy
        from my_strategies import SpreadTradingStrategy
        bot.add_strategy(SpreadTradingStrategy)
        
        # Run
        bot.run()
    """
    
    def __init__(self, config: TradingBotConfig = None):
        """
        Initialize trading bot
        
        Args:
            config: TradingBotConfig instance (uses defaults if None)
        """
        self.config = config or TradingBotConfig()
        
        # Initialize Kalshi client
        kalshi_config = KalshiConfig()
        kalshi_config.ENVIRONMENT = self.config.ENVIRONMENT
        kalshi_config.API_KEY_ID = self.config.API_KEY_ID
        kalshi_config.PRIVATE_KEY_PATH = self.config.PRIVATE_KEY_PATH
        
        self.client = KalshiClient(kalshi_config)
        self.strategies: List[BaseStrategy] = []
        self.active_orders: List[str] = []
        self.running = False
        self.start_time = None
        self.cycle_count = 0
        
        # Handle graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def add_strategy(self, strategy_class: Type[BaseStrategy], **kwargs) -> BaseStrategy:
        """
        Add a strategy to run
        
        Args:
            strategy_class: Strategy class (not instance)
            **kwargs: Arguments to pass to strategy constructor
        
        Returns:
            Strategy instance
        
        Example:
            bot.add_strategy(MyStrategy, name="My Strategy")
        """
        strategy = strategy_class(self.client, **kwargs)
        self.strategies.append(strategy)
        logger.info(f"Added strategy: {strategy}")
        return strategy
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logger.warning("Shutdown signal received, cleaning up...")
        self.running = False
    
    def _check_time_limit(self) -> bool:
        """Check if max run time exceeded"""
        elapsed = time.time() - self.start_time
        if elapsed > self.config.MAX_RUN_TIME:
            logger.warning(f"Max run time ({self.config.MAX_RUN_TIME}s) exceeded")
            return False
        return True
    
    def _get_balance(self) -> float:
        """Get account balance in dollars"""
        try:
            result = self.client.get_balance()
            return result.get('balance_in_cents', 0) / 100
        except Exception as e:
            logger.error(f"Failed to get balance: {e}")
            return 0
    
    def _update_markets(self) -> Optional[pd.DataFrame]:
        """Fetch latest market data"""
        try:
            markets = get_market_positions(volume_threshold=0.0, limit=200)
            return markets
        except Exception as e:
            logger.error(f"Failed to update markets: {e}")
            return None
    
    def _run_cycle(self, markets_df: pd.DataFrame):
        """Run single strategy cycle"""
        for strategy in self.strategies:
            try:
                logger.info(f"Running {strategy.name}...")
                
                # Analyze markets
                orders = strategy.analyze(markets_df)
                
                if not orders:
                    logger.info(f"{strategy.name}: No orders to place")
                    continue
                
                logger.info(f"{strategy.name}: Generated {len(orders)} orders")
                
                # Execute orders
                if not self.config.DRY_RUN:
                    new_orders = strategy.execute_orders(orders)
                    self.active_orders.extend(new_orders)
                else:
                    logger.info(f"[DRY RUN] Would place {len(orders)} orders")
                
            except Exception as e:
                logger.error(f"Error running {strategy.name}: {e}")
    
    def run(self):
        """
        Run trading bot
        
        Continuously fetches market data and runs strategies until time limit exceeded
        or shutdown signal received.
        """
        if not self.strategies:
            logger.error("No strategies added. Use add_strategy() first.")
            return
        
        self.running = True
        self.start_time = time.time()
        
        logger.info("=" * 60)
        logger.info(f"Trading Bot Starting")
        logger.info(f"  Strategies: {len(self.strategies)}")
        logger.info(f"  Max Run Time: {self.config.MAX_RUN_TIME}s")
        logger.info(f"  Update Interval: {self.config.MARKET_UPDATE_INTERVAL}s")
        logger.info(f"  Dry Run: {self.config.DRY_RUN}")
        logger.info(f"  Starting Balance: ${self._get_balance():.2f}")
        logger.info("=" * 60)
        
        try:
            while self.running and self._check_time_limit():
                self.cycle_count += 1
                
                # Update market data
                markets_df = self._update_markets()
                if markets_df is None or markets_df.empty:
                    logger.warning("No market data, retrying...")
                    time.sleep(self.config.MARKET_UPDATE_INTERVAL)
                    continue
                
                logger.info(f"Cycle {self.cycle_count}: {len(markets_df)} markets fetched")
                
                # Run strategies
                self._run_cycle(markets_df)
                
                # Log positions occasionally
                if self.cycle_count % self.config.LOG_POSITIONS_EVERY == 0:
                    balance = self._get_balance()
                    logger.info(f"Current Balance: ${balance:.2f}")
                
                # Wait before next cycle
                time.sleep(self.config.MARKET_UPDATE_INTERVAL)
        
        except Exception as e:
            logger.error(f"Bot error: {e}", exc_info=True)
        
        finally:
            self._shutdown()
    
    def _shutdown(self):
        """Clean shutdown"""
        logger.info("=" * 60)
        logger.info("Trading Bot Shutting Down")
        
        # Cancel active orders if configured
        if self.active_orders and not self.config.DRY_RUN:
            logger.info(f"Cancelling {len(self.active_orders)} active orders...")
            for strategy in self.strategies:
                cancelled = strategy.cancel_orders(self.active_orders)
                logger.info(f"Cancelled {cancelled} orders")
        
        # Final stats
        elapsed = time.time() - self.start_time
        logger.info(f"Total Runtime: {elapsed:.1f}s")
        logger.info(f"Total Cycles: {self.cycle_count}")
        logger.info(f"Final Balance: ${self._get_balance():.2f}")
        logger.info("=" * 60)
        
        self.running = False


if __name__ == '__main__':
    # Example: Create and run bot with no strategies
    # (Add strategies in your script that imports this)
    
    config = TradingBotConfig()
    config.MAX_RUN_TIME = 60  # 1 minute for testing
    config.DRY_RUN = True  # Don't actually place orders
    
    bot = TradingBot(config=config)
    logger.info("Trading bot initialized (no strategies loaded)")
    logger.info("Import TradingBot and add_strategy() to use")
