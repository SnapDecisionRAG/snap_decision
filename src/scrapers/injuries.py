import pandas as pd
import os
import feedparser
from src.config import SQL_DATA_DIR

class InjuriesScraper:
    def __init__(self, db_manager):
        self.db = db_manager
        self.url = 'https://www.draftsharks.com/rss/injury-news'
        self.csv_path = SQL_DATA_DIR / 'injuries.csv'
        self.injuries = []

    def get_existing_injuries(self):
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT published FROM injuries")
                existing_entries = cursor.fetchall()
                return set(row['published'] for row in existing_entries)
        except Exception:
            return set() # for first run of scraper

    def scrape_rss_feed(self):
        try:
            feed = feedparser.parse(self.url)
            entries = feed.entries
            existing_entries = self.get_existing_injuries()

            for entry in entries:
                if entry['published'] in existing_entries:
                    print('Duplicate found, all new entries scraped')
                    break

                info = {}
                info['player'] = entry['media_keywords'].split(', ')[2]
                info['title'] = entry['title']
                info['published'] = entry['published']
                info['link'] = entry['link']
                info['summary'] = entry['summary']
                self.injuries.insert(0, info)

            return True

        except Exception as e:
            print(f"Error scraping RSS feed: {e}")
            return False

    def save_to_csv(self):
        if not self.injuries:
            print('No new injuries to save')
            return None
        
        df = pd.DataFrame(self.injuries)
        df.to_csv(self.csv_path, mode='a', header=not os.path.exists(self.csv_path), index=False)

        print(f"Scraping complete!")
        print(f"Total entries found: {len(self.injuries)}")
        print(f"Saved to: {self.csv_path}")

    def save_to_db(self):
        if not self.injuries:
            raise ValueError('No injuries to save to db')
        
        with self.db.get_connection() as conn:
            cursor = conn.cursor()

            insert_query = """
                INSERT INTO injuries (
                    player_name, title, published, link, summary
                ) VALUES (?, ?, ?, ?, ?)
            """

            injury_data = []
            for injury in self.injuries:
                injury_data.append((
                    injury['player'],
                    injury['title'],
                    injury['published'],
                    injury['link'],
                    injury['summary']
                ))

            cursor.executemany(insert_query, injury_data)
            conn.commit()
            print(f"Inserted {len(injury_data)} injury reports into database")

    def run(self):
        try:
            print("Starting injury reports scraper...")

            success = self.scrape_rss_feed()
            if not success:
                raise Exception("Failed to scrape injury RSS feed")
            
            if self.injuries:
                self.save_to_csv()
                self.save_to_db()
                print(f"Injury scraper completed successfully")
                return len(self.injuries)
            else:
                print("No new injury reports found")
                return 0

        except Exception as e:
            print(f"Injury scraper failed: {e}")
            return 0
