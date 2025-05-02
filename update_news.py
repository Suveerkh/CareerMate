#!/usr/bin/env python3
"""
Script to manually update the news data.
Run this script to fetch fresh news data without restarting the application.
"""

from news_fetcher import update_news_data, load_news_data
import logging
import datetime
import os

if __name__ == "__main__":
    # Configure logging to show on console
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Get the current time
    start_time = datetime.datetime.now()
    print(f"Starting news update at {start_time.strftime('%Y-%m-%d %H:%M:%S')}...")
    
    # Check if we have existing news data
    news_data = load_news_data()
    if news_data.get('articles'):
        print(f"Current news data has {len(news_data.get('articles', []))} articles")
        print(f"Last updated: {news_data.get('last_updated', 'Unknown')}")
    else:
        print("No existing news data found or file is empty")
    
    # Update the news data
    print("\nFetching fresh news data...")
    update_news_data()
    
    # Check the updated news data
    updated_news = load_news_data()
    print(f"\nNews data update complete!")
    print(f"Now have {len(updated_news.get('articles', []))} articles")
    print(f"Last updated: {updated_news.get('last_updated', 'Unknown')}")
    
    # Calculate and display the time taken
    end_time = datetime.datetime.now()
    time_taken = (end_time - start_time).total_seconds()
    print(f"\nTime taken: {time_taken:.2f} seconds")