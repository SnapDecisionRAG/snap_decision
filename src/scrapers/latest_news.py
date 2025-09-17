import pandas as pd
import feedparser

class NewsScraper:
    def __init__(self):
        self.url = 'https://www.draftsharks.com/rss/latest-news'
        self.csv_path = '../../data/sql/latest_news.csv'
        self.news = []

    def get_existing_news(self):
        try:
            existing_news = pd.read_csv(self.csv_path)
            return set(existing_news['published'].tolist())
        except FileNotFoundError:
            return set() # for first run of scraper

    def scrape_rss_feed(self):
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
            self.news.append(info)

    def save_to_csv(self):
        if not self.news:
            print('No new news to save')
            return None
        
        new_df = pd.DataFrame(self.news)
        
        try:
            existing_df = pd.read_csv(self.csv_path)
            new_df = pd.concat([new_df, existing_df], ignore_index=True)
        except FileNotFoundError:
            pass

        new_df.to_csv(self.csv_path, index=False)

        print(f"Scraping complete!")
        print(f"Total entries found: {len(self.news)}")
        print(f"Saved to: {self.csv_path}")

        return new_df

def main():
    scraper = NewsScraper()
    scraper.scrape_rss_feed()
    scraper.save_to_csv()

if __name__ == "__main__":
    main()
