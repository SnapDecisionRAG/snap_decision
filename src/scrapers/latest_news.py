import pandas as pd
import feedparser
import os
from src.config import SQL_DATA_DIR

class NewsScraper:
    def __init__(self, db_manager):
        self.db = db_manager
        self.url = 'https://www.draftsharks.com/rss/latest-news'
        self.csv_path = SQL_DATA_DIR / 'latest_news.csv'
        self.news = []

    def get_existing_news(self):
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT published FROM latest_news")
                existing_entries = cursor.fetchall()
                return set(row['published'] for row in existing_entries)
        except Exception:
            return set() # for first run of scraper

    def scrape_rss_feed(self):
        try:
            feed = feedparser.parse(self.url)
            entries = feed.entries
            existing_news = self.get_existing_news()

            for entry in entries:
                if entry['published'] in existing_news:
                    print('Duplicate found, all new entries scraped')
                    break

                info = {}
                info['player_or_team'] = entry['media_keywords'].split(', ')[1]
                info['title'] = entry['title']
                info['published'] = entry['published']
                info['link'] = entry['link']
                info['summary'] = entry['summary']
                self.news.insert(0, info)

            return True
        
        except Exception as e:
            print(f"Error scraping RSS feed: {e}")
            return False

    def save_to_csv(self):
        if not self.news:
            print('No new news to save')
            return None
        
        df = pd.DataFrame(self.news)
        df.to_csv(self.csv_path, mode='a', header=not os.path.exists(self.csv_path), index=False)

        print(f"Scraping complete!")
        print(f"Total entries found: {len(self.news)}")
        print(f"Saved to: {self.csv_path}")

    def save_to_db(self):
        if not self.news:
            raise ValueError('No news to save to db')
        
        with self.db.get_connection() as conn:
            cursor = conn.cursor()

            insert_query = """
                INSERT INTO latest_news (
                    player_or_team, title, published, link, summary
                ) VALUES (?, ?, ?, ?, ?)
            """

            news_reports = []
            for news_item in self.news:
                news_reports.append((
                    news_item['player_or_team'],
                    news_item['title'],
                    news_item['published'],
                    news_item['link'],
                    news_item['summary']
                ))

            cursor.executemany(insert_query, news_reports)
            conn.commit()
            print(f"Inserted {len(news_reports)} news reports into database")

    def run(self):
        try:
            print("Starting latest news scraper...")

            success = self.scrape_rss_feed()
            if not success:
                raise Exception("Failed to scrape news RSS feed")
            
            if self.news:
                self.save_to_csv()
                self.save_to_db()
                print(f"News scraper completed successfully")
                return len(self.news)
            else:
                print("No new news reports found")
                return 0

        except Exception as e:
            print(f"News scraper failed: {e}")
            return 0
