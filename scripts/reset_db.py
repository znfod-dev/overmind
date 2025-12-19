#!/usr/bin/env python3
"""A command-line script to completely reset the database."""

import asyncio
import sys
from pathlib import Path

# Add project root to the Python path to allow imports from 'app'
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Now that the path is set, we can import our app components
from app.database.config import engine, Base
from app.core.logging_config import logger

# Import all models so Base knows about them
from app.models import ai_config, diary, subscription, user  # noqa


async def reset_database():
    """Drops all tables and recreates them."""
    logger.info("Connecting to the database...")
    async with engine.begin() as conn:
        logger.warning("DROPPING all existing tables...")
        await conn.run_sync(Base.metadata.drop_all)
        logger.info("All tables dropped.")

        logger.info("CREATING all tables from scratch...")
        await conn.run_sync(Base.metadata.create_all)
        logger.info("All tables created successfully.")

    logger.info("Database reset complete. Closing connection.")
    await engine.dispose()


if __name__ == "__main__":
    # A simple confirmation prompt for safety
    print("This script will completely WIPE and RESET the database.")
    print(f"TARGET DATABASE: {engine.url}")
    confirm = input("Are you absolutely sure you want to continue? (yes/no): ")

    if confirm.lower() == 'yes':
        print("Proceeding with database reset...")
        try:
            asyncio.run(reset_database())
        except Exception as e:
            logger.error(f"An error occurred during database reset: {e}")
            sys.exit(1)
    else:
        print("Database reset cancelled.")
