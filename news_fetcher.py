"""
News Fetcher Module

This module fetches educational news from various sources and updates the news data
that will be displayed on the news.html page.
"""

import os
import json
import time
import datetime
import requests
import logging
from bs4 import BeautifulSoup
import schedule
import threading
import random

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("news_fetcher.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("news_fetcher")

# File to store news data
NEWS_DATA_FILE = os.path.join(os.path.dirname(__file__), 'static', 'data', 'news_data.json')

# Ensure the data directory exists
os.makedirs(os.path.dirname(NEWS_DATA_FILE), exist_ok=True)

# News API key
NEWS_API_KEY = os.getenv('NEWS_API_KEY', '864af831be454b7abe9f5fbd08d2ccb1')

# Categories for classification
CATEGORIES = {
    'higher-education': ['university', 'college', 'higher education', 'academic', 'campus', 'degree'],
    'technology': ['edtech', 'technology', 'digital', 'online learning', 'e-learning', 'virtual'],
    'policy': ['policy', 'regulation', 'government', 'law', 'legislation', 'reform'],
    'career': ['career', 'job', 'employment', 'skill', 'professional', 'workforce', 'internship']
}

def classify_news(title, description):
    """Classify news into categories based on keywords in title and description"""
    text = (title + ' ' + description).lower()
    article_categories = []
    
    for category, keywords in CATEGORIES.items():
        for keyword in keywords:
            if keyword.lower() in text:
                article_categories.append(category)
                break
    
    return article_categories

def fetch_from_news_api():
    """Fetch education news from News API"""
    if not NEWS_API_KEY:
        logger.warning("NEWS_API_KEY not set. Skipping News API fetch.")
        return []
    
    try:
        # Use a more specific query focused on education-related news
        query = (
            "(education OR university OR college OR \"higher education\" OR \"online learning\" OR \"education technology\") "
            "AND (career OR degree OR student OR graduate OR admission OR scholarship OR course OR curriculum OR "
            "\"skill development\" OR \"vocational training\" OR \"job market\" OR \"employment\" OR \"internship\")"
        )
        url = f"https://newsapi.org/v2/everything?q={query}&sortBy=publishedAt&apiKey={NEWS_API_KEY}&language=en&pageSize=20"
        response = requests.get(url)
        data = response.json()
        
        if data.get('status') != 'ok':
            logger.error(f"News API error: {data.get('message', 'Unknown error')}")
            return []
        
        articles = []
        for article in data.get('articles', []):
            # Skip articles without title or description
            if not article.get('title') or not article.get('description'):
                continue
                
            # Format the date
            published_date = article.get('publishedAt')
            if published_date:
                try:
                    date_obj = datetime.datetime.strptime(published_date, "%Y-%m-%dT%H:%M:%SZ")
                    formatted_date = date_obj.strftime("%B %d, %Y")
                except ValueError:
                    formatted_date = published_date
            else:
                formatted_date = "Unknown date"
            
            # Classify the article
            categories = classify_news(article.get('title', ''), article.get('description', ''))
            
            articles.append({
                'title': article.get('title'),
                'description': article.get('description'),
                'url': article.get('url'),
                'image_url': article.get('urlToImage'),
                'source': article.get('source', {}).get('name', 'Unknown source'),
                'published_date': formatted_date,
                'categories': categories
            })
        
        return articles
    except Exception as e:
        logger.error(f"Error fetching from News API: {str(e)}")
        return []

def fetch_from_google_news():
    """Fetch education news by scraping Google News"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        # Use more specific education-related queries
        education_queries = [
            "higher education career",
            "university degree programs",
            "college admissions",
            "education technology career",
            "scholarship opportunities",
            "student career development",
            "vocational training programs",
            "online learning degrees",
            "education job market"
        ]
        
        all_articles = []
        
        # Fetch articles for each query
        for query in education_queries:
            encoded_query = requests.utils.quote(query)
            url = f"https://news.google.com/search?q={encoded_query}&hl=en-US&gl=US&ceid=US:en"
            
            try:
                response = requests.get(url, headers=headers)
                
                if response.status_code != 200:
                    logger.error(f"Google News error for query '{query}': Status code {response.status_code}")
                    continue
                
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Find article elements
                article_elements = soup.select('article')
                
                for article in article_elements[:5]:  # Limit to 5 articles per query
                    try:
                        # Extract title and link
                        title_element = article.select_one('h3 a')
                        if not title_element:
                            continue
                            
                        title = title_element.text
                        
                        # Google News uses relative URLs
                        relative_url = title_element.get('href', '')
                        if relative_url:
                            article_url = f"https://news.google.com{relative_url.replace('./', '/')}"
                        else:
                            continue
                        
                        # Extract source and time
                        source_time = article.select_one('div[class*="TVFRme"]')
                        source = "Unknown source"
                        published_time = "Recent"
                        
                        if source_time:
                            source_element = source_time.select_one('a')
                            time_element = source_time.select_one('time')
                            
                            if source_element:
                                source = source_element.text
                            
                            if time_element:
                                published_time = time_element.text
                        
                        # We don't get descriptions from Google News easily, so create a placeholder
                        description = f"Latest education news about {query} from {source}. Click to read more."
                        
                        # Classify the article
                        categories = classify_news(title, description)
                        
                        # Check if this article is already in our list (by URL)
                        if not any(a.get('url') == article_url for a in all_articles):
                            all_articles.append({
                                'title': title,
                                'description': description,
                                'url': article_url,
                                'image_url': None,  # Google News doesn't provide images in the listing
                                'source': source,
                                'published_date': published_time,
                                'categories': categories,
                                'query': query  # Store the query used to find this article
                            })
                    except Exception as e:
                        logger.error(f"Error processing Google News article for query '{query}': {str(e)}")
                        continue
            except Exception as e:
                logger.error(f"Error fetching from Google News for query '{query}': {str(e)}")
                continue
        
        return all_articles
    except Exception as e:
        logger.error(f"Error in Google News fetcher: {str(e)}")
        return []

def fetch_from_education_websites():
    """Fetch news from education-focused websites"""
    # This is a simplified example. In a real implementation, you would
    # create specific scrapers for each education website.
    education_sites = [
        {
            'name': 'Inside Higher Ed',
            'url': 'https://www.insidehighered.com/',
            'article_selector': 'article.views-row',
            'title_selector': 'h2 a',
            'description_selector': 'div.field-summary',
            'link_selector': 'h2 a',
            'date_selector': 'div.field-date'
        },
        {
            'name': 'Education Week',
            'url': 'https://www.edweek.org/',
            'article_selector': 'article.promo',
            'title_selector': 'h3 a',
            'description_selector': 'p.description',
            'link_selector': 'h3 a',
            'date_selector': 'span.date-display-single'
        }
    ]
    
    all_articles = []
    
    for site in education_sites:
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            response = requests.get(site['url'], headers=headers, timeout=10)
            
            if response.status_code != 200:
                logger.error(f"Error fetching from {site['name']}: Status code {response.status_code}")
                continue
            
            soup = BeautifulSoup(response.text, 'html.parser')
            articles = soup.select(site['article_selector'])
            
            for article in articles[:5]:  # Limit to 5 articles per site
                try:
                    title_element = article.select_one(site['title_selector'])
                    description_element = article.select_one(site['description_selector'])
                    link_element = article.select_one(site['link_selector'])
                    date_element = article.select_one(site['date_selector'])
                    
                    if not title_element or not link_element:
                        continue
                    
                    title = title_element.text.strip()
                    
                    # Handle relative URLs
                    link = link_element.get('href', '')
                    if link and not link.startswith(('http://', 'https://')):
                        link = site['url'].rstrip('/') + '/' + link.lstrip('/')
                    
                    description = description_element.text.strip() if description_element else f"Latest education news from {site['name']}. Click to read more."
                    published_date = date_element.text.strip() if date_element else "Recent"
                    
                    # Classify the article
                    categories = classify_news(title, description)
                    
                    all_articles.append({
                        'title': title,
                        'description': description,
                        'url': link,
                        'image_url': None,
                        'source': site['name'],
                        'published_date': published_date,
                        'categories': categories
                    })
                except Exception as e:
                    logger.error(f"Error processing article from {site['name']}: {str(e)}")
                    continue
        except Exception as e:
            logger.error(f"Error fetching from {site['name']}: {str(e)}")
            continue
    
    return all_articles

def is_education_related(article):
    """Check if an article is education-related based on its title and description"""
    education_keywords = [
        'education', 'university', 'college', 'school', 'student', 'academic', 
        'learning', 'teaching', 'degree', 'course', 'study', 'research', 
        'professor', 'teacher', 'faculty', 'campus', 'scholarship', 'career',
        'graduate', 'undergraduate', 'phd', 'masters', 'bachelor', 'curriculum',
        'exam', 'admission', 'enrollment', 'classroom', 'lecture', 'seminar',
        'education technology', 'edtech', 'online learning', 'e-learning',
        'higher education', 'vocational training', 'skill development'
    ]
    
    text = (article.get('title', '') + ' ' + article.get('description', '')).lower()
    
    for keyword in education_keywords:
        if keyword.lower() in text:
            return True
    
    # If the article already has categories, check if any are education-related
    categories = article.get('categories', [])
    education_categories = ['higher-education', 'technology', 'policy', 'career']
    
    for category in categories:
        if category in education_categories:
            return True
    
    return False

def update_news_data():
    """Fetch news from all sources and update the news data file"""
    current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    logger.info(f"Starting news update at {current_time}...")
    
    # Fetch news from different sources
    news_api_articles = fetch_from_news_api()
    google_news_articles = fetch_from_google_news()
    education_website_articles = fetch_from_education_websites()
    
    # Log the number of articles fetched from each source
    logger.info(f"Fetched {len(news_api_articles)} articles from News API")
    logger.info(f"Fetched {len(google_news_articles)} articles from Google News")
    logger.info(f"Fetched {len(education_website_articles)} articles from education websites")
    
    # Combine all articles
    all_articles = news_api_articles + google_news_articles + education_website_articles
    
    # Filter to keep only education-related articles
    education_articles = [article for article in all_articles if is_education_related(article)]
    logger.info(f"Filtered to {len(education_articles)} education-related articles")
    
    # Load existing news data to preserve recent articles
    existing_news_data = load_news_data()
    existing_articles = existing_news_data.get('articles', [])
    
    # Add timestamp to new articles for expiration tracking
    current_timestamp = datetime.datetime.now().timestamp()
    for article in education_articles:
        article['added_timestamp'] = current_timestamp
    
    # Process existing articles to keep those less than 24 hours old
    kept_existing_articles = []
    seen_titles = set()
    
    # Add titles of new articles to seen_titles to avoid duplicates
    for article in education_articles:
        seen_titles.add(article['title'])
    
    # Keep existing articles that are less than 24 hours old and not duplicates
    for article in existing_articles:
        # Skip if title is already in new articles
        if article['title'] in seen_titles:
            continue
        
        # Check if article has timestamp and is less than 24 hours old
        if 'added_timestamp' in article:
            article_time = article['added_timestamp']
            age_hours = (current_timestamp - article_time) / 3600
            
            if age_hours < 24:  # Keep if less than 24 hours old
                seen_titles.add(article['title'])
                kept_existing_articles.append(article)
        else:
            # Add timestamp to articles that don't have one
            article['added_timestamp'] = current_timestamp
            seen_titles.add(article['title'])
            kept_existing_articles.append(article)
    
    # Combine new and kept existing articles
    combined_articles = education_articles + kept_existing_articles
    
    # Sort by date (most recent first) - using added_timestamp as a fallback
    # This is a simplified approach since we have different date formats
    random.shuffle(combined_articles)  # For now, just shuffle them
    
    # Limit to 50 articles (increased from 30 to accommodate keeping older articles)
    combined_articles = combined_articles[:50]
    
    # Create the news data object
    news_data = {
        'last_updated': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'articles': combined_articles
    }
    
    # Save to file
    try:
        with open(NEWS_DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(news_data, f, ensure_ascii=False, indent=2)
        end_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        logger.info(f"News data updated successfully at {end_time} with {len(combined_articles)} articles")
        logger.info(f"Next update scheduled in 1 hour")
    except Exception as e:
        logger.error(f"Error saving news data: {str(e)}")

def load_news_data():
    """Load news data from file"""
    try:
        if os.path.exists(NEWS_DATA_FILE):
            with open(NEWS_DATA_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            logger.warning(f"News data file not found at {NEWS_DATA_FILE}")
            return {'last_updated': None, 'articles': []}
    except Exception as e:
        logger.error(f"Error loading news data: {str(e)}")
        return {'last_updated': None, 'articles': []}

def run_scheduler():
    """Run the scheduler in a separate thread"""
    # Update news immediately on startup
    update_news_data()
    
    # Schedule regular updates every hour
    schedule.every(1).hour.do(update_news_data)
    
    while True:
        schedule.run_pending()
        time.sleep(60)

def start_news_updater():
    """Start the news updater in a background thread"""
    thread = threading.Thread(target=run_scheduler, daemon=True)
    thread.start()
    logger.info("News updater started in background thread")
    return thread

if __name__ == "__main__":
    # When run directly, update the news once
    update_news_data()