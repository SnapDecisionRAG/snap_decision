import time
import re
import hashlib
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By as selenium_by
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as selenium_ec
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from src.config import VECTOR_DATA_DIR

class LatestBuzzScraper:
    def __init__(self, db_manager, headless=True):
        self.db = db_manager
        self.url = "https://www.espn.com/fantasy/football/"
        self.csv_path = VECTOR_DATA_DIR / 'latest_buzz.csv'
        self.article_dates = {6, 0, 1}
        self.articles = []
        self.scraped_articles = set()

        chrome_options = webdriver.chrome.options.Options()
        chrome_options.add_argument('--max_old_space_size=4096')
        chrome_options.add_argument('--disable-extensions')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--mute-audio')
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')

        if headless: chrome_options.add_argument('--headless')

        self.browser = webdriver.Chrome(options=chrome_options)

    def wait_for_page_to_load(self, timeout=30):
        try:
            WebDriverWait(self.browser, timeout).until(
                selenium_ec.presence_of_element_located(
                    (selenium_by.CSS_SELECTOR, '#news-feed')
                )
            )

            time.sleep(2)
            return True

        except Exception as e:
            print(f'Page could not be scraped: {e}')
            return False

    def get_existing_articles(self):
        try:
            existing_articles = self.db.collection.get(
                where={'content_type': 'expert_analysis'},
                include=['metadatas']
            )

            existing_urls = set()
            metadatas = existing_articles.get('metadatas', [])

            for metadata in metadatas:
                url = metadata.get('url')
                if url: existing_urls.add(url)

            return existing_urls
        
        except Exception as e:
            print(f"Warning: Could not check existing articles: {e}")
            return set()


    def load_latest_buzz(self):
        try:
            self.browser.get(self.url)
            button = WebDriverWait(self.browser, timeout=10, poll_frequency=0.1).until(
                selenium_ec.element_to_be_clickable(
                    (selenium_by.CSS_SELECTOR, "a[data-track-nav_item='latest buzz']")
                )
            )
            button.click()
            return True
        except Exception as e:
            print(f'error loading Latest Buzz: {e}')
            return False

    def get_article_date(self, timestamp):
        date_obj = datetime.strptime(timestamp, "%b %d, %Y, %I:%M %p ET")
        return date_obj 
    
    def continue_scraping(self, article_date):
        today = datetime.now()
        days_since_tuesday = (today.weekday() - 1) % 7
        this_weeks_tuesday = today - timedelta(days=days_since_tuesday)
        this_weeks_sunday = this_weeks_tuesday - timedelta(days=2)
        last_saturday = this_weeks_sunday - timedelta(days=1)

        if article_date.date() == last_saturday.date():
            print('All relevant articles scraped')
            return False

        return True
    
    def scrape_this_article(self, article_date):
        today = datetime.now()
        days_since_tuesday = (today.weekday() - 1) % 7
        this_weeks_tuesday = today - timedelta(days=days_since_tuesday)
        this_weeks_sunday = this_weeks_tuesday - timedelta(days=2)
        return this_weeks_tuesday.date() >= article_date.date() >= this_weeks_sunday.date()

    def scrape(self, article):
        parsed_article = {}

        title = article.select_one('header.article-header h1')
        parsed_article['title'] = title.get_text().strip() if title else ''

        article_meta = article.select_one('.article-meta')
        if article_meta:
            timestamp = article_meta.select_one('span.timestamp')
            author = article_meta.select_one('div.author')

            timestamp_text = timestamp.get_text().strip() if timestamp else ''
            parsed_article['timestamp'] = timestamp_text

            author_text = author.get_text().strip() if author else ''
            if author_text and timestamp_text in author_text:
                author_text = author_text.replace(timestamp_text, '').strip()
            if author_text == 'ESPN Fantasy':
                parsed_article['author'] = 'ESPN Fantasy Staff'
            else:
                parsed_article['author'] = author_text
        else:
            parsed_article['timestamp'] = ''
            parsed_article['author'] =  ''

        body = article.select_one('div.article-body')
        if body:
            unwanted_selectors = [
                '.content-reactions', '.ad-slot', '.ad-wrapper', '.sponsored-links',
                '.taboola-container', 'footer', 'script', 'button', '.reactions-skeleton-loading',
                '.inline-track', 'aside.inline.float-r.inline-track', '.media-wrapper',
                '.video-player', '.play-button', '.social-share', '.share-tools', '.social-buttons',
                '.breadcrumb', '.navigation',
            ]
            for attribute in unwanted_selectors: # delete unwanted elements from DOM permanently
                for element in body.select(attribute):
                    element.decompose()
            parsed_article['body'] = body.get_text().strip()
        else:
            parsed_article['body'] = ''

        url = article.get('data-src')
        parsed_article['url'] = f"https://www.espn.com{url}" if url else ''

        return parsed_article


    def scrape_articles(self):
        existing_articles = self.get_existing_articles()

        while True:
            page_source = self.browser.page_source
            if len(page_source) > 5000000: # 5MB to prevent selenium/BeautifulSoup crash/hang
                print('All relevant articles scraped')
                break
            soup = BeautifulSoup(page_source, 'html.parser')

            loaded_articles = soup.select('#news-feed article.article')
            current_article = None
            for article in loaded_articles:
                url = article.get('data-src')
                if url and url not in self.scraped_articles:
                    full_url = f"https://www.espn.com{url}"
                    if full_url in existing_articles:
                        print(f"Article already exists in database, stopping scrape: {url}")
                        return self.articles

                    current_article = article
                    self.scraped_articles.add(url)
                    break

            if not current_article: # try once more in case didn't scroll far enough
                self.browser.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)
                soup = BeautifulSoup(self.browser.page_source, 'html.parser')
                loaded_articles = soup.select('#news-feed article.article')
                current_article = None
                for article in loaded_articles:
                    url = article.get('data-src')
                    if url and url not in self.scraped_articles:
                        full_url = f"https://www.espn.com{url}"
                        if full_url in existing_articles:
                            print(f"Article already exists in database, stopping scrape: {url}")
                            return self.articles

                        current_article = article
                        self.scraped_articles.add(url)
                        break
                
                if not current_article:
                    print("No more articles found")
                    break

            article_date = self.get_article_date(current_article.select_one('.timestamp').get_text())
            if not self.continue_scraping(article_date):
                break

            if self.scrape_this_article(article_date):
                self.articles.append(self.scrape(current_article))
                print(url)
                print(article_date)
            self.browser.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)

        return self.articles
    
    def save_to_csv(self):
        if not self.articles:
            print('No articles saved - ESPN structure may have changed')
            return None
        
        df = pd.DataFrame(self.articles)
        df = df.drop_duplicates(subset=['url'], keep='first')
        df.to_csv(self.csv_path, index=False)

        print(f"\nScraping complete!")
        print(f"Total articles found: {len(df)}")
        print(f"Saved to: {self.csv_path}")

        return df
    
    def save_to_db(self):
        if not self.articles:
            print('No articles to save to vector database')
            return False
        
        print('Processing articles for vector database...')

        documents = []
        for article in self.articles:
            if not article.get('body') or not article.get('body').strip():
                continue

            cleaned_content = self.clean_article_content(article['body'])
            if not cleaned_content.strip():
                continue

            doc_id = self.generate_article_id(article)
            timestamp = self.normalize_timestamp(article.get('timestamp', ''))
            doc = {
                'id': doc_id,
                'content': cleaned_content,
                'metadata': {
                    'content_type': 'expert_analysis',
                    'title': article.get('title', ''),
                    'author': article.get('author', ''),
                    'timestamp': timestamp,
                    'url': article.get('url'),
                    'source': 'espn_latest_buzz',
                    'static_content': False,
                }
            }

            documents.append(doc)

        if documents:
            return self.db.add_documents(documents)
        else:
            print('Failed to add articles to vector database')
            return False
        
    def clean_article_content(self, content):
        # Remove excessive whitespace
        content = re.sub(r'\n\s*\n\s*\n+', '\n\n', content)
        content = re.sub(r'\s+', ' ', content)
        
        # Remove common web artifacts
        content = re.sub(r'\bAdvertisement\b', '', content, flags=re.IGNORECASE)
        content = re.sub(r'\bRead More\b', '', content, flags=re.IGNORECASE)
        content = re.sub(r'\bSign Up\b', '', content, flags=re.IGNORECASE)
        content = re.sub(r'\bSubscribe\b', '', content, flags=re.IGNORECASE)
        
        # Clean up bullet points and formatting
        content = re.sub(r'^\s*•\s*', '', content, flags=re.MULTILINE)
        content = re.sub(r'^\s*-\s*', '', content, flags=re.MULTILINE)
        
        return content.strip()
    
    def normalize_timestamp(self, timestamp):
        if not timestamp:
            return datetime.now().isoformat()
        
        try:
            dt = datetime.strptime(timestamp, '%b %d, %Y, %I:%M %p ET')
            return dt.isoformat()
        except Exception:
            return datetime.now().isoformat()
        
    def generate_article_id(self, article):
        if article.get('url'):
            content_string = article['url']
        else:
            content_string = (
                f"{article.get('title', '')}{article.get('timestamp', '')}"
            )

        return f'buzz_{hashlib.md5(content_string.encode()).hexdigest()[:12]}'
    
    def run(self):
        try:
            print('Starting ESPN Fantasy Football Latest Buzz Scraper')
            print('=' * 50)

            self.load_latest_buzz()
            articles = self.scrape_articles()

            if articles:
                self.save_to_csv()
                self.save_to_db()
                print('Latest buzz scraper completed successfully')
                return len(articles)
            else:
                print('No articles scraped')
                return 0
            
        except Exception as e:
            print(f'Latest buzz scraper failed: {e}')
            return 0
        
        finally:
            if self.browser:
                self.browser.quit()
