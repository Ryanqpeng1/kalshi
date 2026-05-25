#!/usr/bin/env python3
"""
Setup wizard for Kalshi trading bot
Helps you configure API credentials interactively
"""

import os
import sys
from pathlib import Path

def print_header(text):
    print("\n" + "="*60)
    print(f"  {text}")
    print("="*60)

def get_input(prompt, default=None):
    """Get user input with optional default"""
    if default:
        prompt = f"{prompt} [{default}]: "
    else:
        prompt = f"{prompt}: "
    
    value = input(prompt).strip()
    return value if value else default

def validate_file_path(path):
    """Validate that a file exists"""
    if os.path.exists(path):
        return True
    return False

def main():
    print_header("Kalshi Trading Bot Setup")
    
    print("\nThis wizard will help you configure your Kalshi API credentials.")
    print("You'll need:")
    print("  1. API Key ID (from https://kalshi.com/account/profile)")
    print("  2. Private Key file (downloaded from Kalshi)")
    
    # Get API Key ID
    print_header("Step 1: API Key ID")
    api_key_id = get_input("Enter your API Key ID")
    
    if not api_key_id:
        print("❌ API Key ID is required")
        sys.exit(1)
    
    # Get private key path
    print_header("Step 2: Private Key File")
    print("This is the .key file you downloaded from Kalshi")
    
    while True:
        key_path = get_input("Enter path to your private key file")
        
        if not key_path:
            print("❌ Private key path is required")
            continue
        
        if validate_file_path(key_path):
            print(f"✓ Found: {key_path}")
            break
        else:
            print(f"❌ File not found: {key_path}")
            print("   Make sure the path is correct (absolute or relative)")
            continue
    
    # Get environment
    print_header("Step 3: Environment")
    print("Choose where to trade:")
    print("  1. demo (recommended for testing)")
    print("  2. production (real money)")
    
    while True:
        env_choice = get_input("Enter choice (1 or 2)", "1")
        
        if env_choice == "1":
            environment = "demo"
            break
        elif env_choice == "2":
            confirm = get_input("⚠️  Are you sure? This will trade with REAL MONEY (yes/no)", "no")
            if confirm.lower() == "yes":
                environment = "production"
                break
        else:
            print("❌ Invalid choice. Enter 1 or 2")
    
    print(f"✓ Using {environment} environment")
    
    # Summary
    print_header("Configuration Summary")
    print(f"API Key ID:      {api_key_id}")
    print(f"Private Key:     {key_path}")
    print(f"Environment:     {environment}")
    
    # Save to config
    confirm = get_input("\nSave this configuration? (yes/no)", "yes")
    
    if confirm.lower() != "yes":
        print("Cancelled.")
        sys.exit(0)
    
    # Update config.py
    config_path = "config.py"
    
    try:
        with open(config_path, 'r') as f:
            content = f.read()
        
        # Replace values
        content = content.replace(
            "API_KEY_ID = 'your-api-key-id-here'",
            f"API_KEY_ID = '{api_key_id}'"
        )
        content = content.replace(
            "PRIVATE_KEY_PATH = 'path/to/your/kalshi-key.key'",
            f"PRIVATE_KEY_PATH = '{key_path}'"
        )
        content = content.replace(
            "ENVIRONMENT = 'demo'",
            f"ENVIRONMENT = '{environment}'"
        )
        
        with open(config_path, 'w') as f:
            f.write(content)
        
        print_header("✓ Configuration Saved")
        print(f"Updated {config_path}")
        print("\nYou can now run:")
        print("  python place_order.py")
        print("  python get_balance.py")
        print("  python browse_markets.py")
        
    except Exception as e:
        print(f"❌ Failed to update config: {e}")
        sys.exit(1)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nCancelled.")
        sys.exit(0)
