#!/usr/bin/env python3
"""
Test script for TieShop Bot
"""

import os
import sys
import asyncio
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_imports():
    """Test all imports"""
    print("Testing imports...")
    try:
        from bot_translations import get_text
        print("✓ bot_translations import: OK")
    except Exception as e:
        print(f"✗ bot_translations import error: {e}")
        return False
    
    try:
        from database import get_all_active_ties, migrate_ties_from_json
        print("✓ database import: OK")
    except Exception as e:
        print(f"✗ database import error: {e}")
        return False
    
    try:
        from telegram import Update
        from telegram.ext import Application
        print("✓ telegram import: OK")
    except Exception as e:
        print(f"✗ telegram import error: {e}")
        return False
    
    return True

def test_environment():
    """Test environment variables"""
    print("\nTesting environment variables...")
    
    BOT_TOKEN = os.getenv('BOT_TOKEN')
    ADMIN_IDS = os.getenv('ADMIN_IDS')
    PAYMENT_LINK = os.getenv('PAYMENT_LINK')
    
    if not BOT_TOKEN:
        print("✗ BOT_TOKEN is not set!")
        return False
    else:
        print(f"✓ BOT_TOKEN: {BOT_TOKEN[:10]}...")
    
    if not ADMIN_IDS:
        print("✗ ADMIN_IDS is not set!")
        return False
    else:
        print(f"✓ ADMIN_IDS: {ADMIN_IDS}")
    
    if not PAYMENT_LINK:
        print("✗ PAYMENT_LINK is not set!")
        return False
    else:
        print(f"✓ PAYMENT_LINK: {PAYMENT_LINK}")
    
    return True

def test_database():
    """Test database operations"""
    print("\nTesting database...")
    try:
        from database import migrate_ties_from_json, get_all_active_ties
        migrate_ties_from_json()
        ties = get_all_active_ties()
        print(f"✓ Database migration successful, {len(ties)} ties loaded")
        return True
    except Exception as e:
        print(f"✗ Database error: {e}")
        return False

def test_bot_creation():
    """Test bot application creation"""
    print("\nTesting bot creation...")
    try:
        from telegram.ext import Application
        BOT_TOKEN = os.getenv('BOT_TOKEN')
        app = Application.builder().token(BOT_TOKEN).build()
        print("✓ Bot application created successfully")
        return True
    except Exception as e:
        print(f"✗ Bot creation error: {e}")
        return False

async def test_bot_handlers():
    """Test bot handlers setup"""
    print("\nTesting bot handlers...")
    try:
        from bot_v2 import TieShopBot
        bot = TieShopBot()
        print("✓ Bot handlers setup successful")
        return True
    except Exception as e:
        print(f"✗ Bot handlers error: {e}")
        return False

def main():
    """Run all tests"""
    print("=== TieShop Bot Test ===")
    
    tests = [
        test_imports,
        test_environment,
        test_database,
        test_bot_creation,
    ]
    
    all_passed = True
    for test in tests:
        if not test():
            all_passed = False
    
    # Test async function
    try:
        result = asyncio.run(test_bot_handlers())
        if not result:
            all_passed = False
    except Exception as e:
        print(f"✗ Async test error: {e}")
        all_passed = False
    
    print("\n=== Test Results ===")
    if all_passed:
        print("✓ All tests passed! Bot should work correctly.")
    else:
        print("✗ Some tests failed. Check the errors above.")
    
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
