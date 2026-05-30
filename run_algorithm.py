#!/usr/bin/env python3
"""
Kalshi Trading Algorithm - Main Executable

Run your trading strategies against live Kalshi markets

Usage:
    python run_algorithm.py                  # Run with default settings
    python run_algorithm.py --dry-run        # Simulate without placing orders
    python run_algorithm.py --time 600       # Run for 10 minutes
"""

import argparse
import sys
import logging
from trading_bot import TradingBot, TradingBotConfig
from example_strategies import SpreadTradingStrategy, HighVolumeStrategy, LOLOnlyStrategy

logger = logging.getLogger(__name__)


def main():
    """Main entry point"""
    
    parser = argparse.ArgumentParser(
        description='Kalshi Trading Algorithm',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run with default settings (5 min, spread strategy)
  python run_algorithm.py
  
  # Test strategy without placing actual orders
  python run_algorithm.py --dry-run
  
  # Run for 10 minutes with high volume strategy
  python run_algorithm.py --time 600 --strategy HighVolume
  
  # Run multiple strategies
  python run_algorithm.py --strategy Spread --strategy HighVolume --strategy LOLOnly
        """
    )
    
    parser.add_argument(
        '--time', 
        type=int, 
        default=300,
        help='Max run time in seconds (default: 300/5min)'
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Simulate trades without placing actual orders'
    )
    
    parser.add_argument(
        '--strategy',
        action='append',
        dest='strategies',
        choices=['Spread', 'HighVolume', 'LOLOnly'],
        default=['Spread'],
        help='Strategy to run (can specify multiple)'
    )
    
    parser.add_argument(
        '--interval',
        type=int,
        default=5,
        help='Market update interval in seconds (default: 5)'
    )
    
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )
    
    args = parser.parse_args()
    
    # Set logging level
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Build strategy mapping
    strategy_map = {
        'Spread': SpreadTradingStrategy,
        'HighVolume': HighVolumeStrategy,
        'LOLOnly': LOLOnlyStrategy,
    }
    
    # Create bot config
    config = TradingBotConfig()
    config.MAX_RUN_TIME = args.time
    config.DRY_RUN = args.dry_run
    config.MARKET_UPDATE_INTERVAL = args.interval
    
    # Initialize bot
    bot = TradingBot(config=config)
    
    # Add strategies
    logger.info(f"Loading {len(args.strategies)} strategy(ies)...")
    for strategy_name in args.strategies:
        if strategy_name in strategy_map:
            bot.add_strategy(strategy_map[strategy_name])
        else:
            logger.error(f"Unknown strategy: {strategy_name}")
            sys.exit(1)
    
    # Run bot
    try:
        bot.run()
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
