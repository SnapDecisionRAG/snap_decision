import pandas as pd
import feedparser

class InjuriesScraper:
    def __init__(self):
        self.url = 'https://www.draftsharks.com/rss/injury-news'
        self.csv_path = '../../data/sql/injuries.csv'
        self.injuries = []

    def get_existing_injuries(self):
        try:
            existing_entries = pd.read_csv(self.csv_path)
            return set(existing_entries['published'].tolist())
        except FileNotFoundError:
            return set() # for first run of scraper

    def scrape_rss_feed(self):
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
            self.injuries.append(info)

    def save_to_csv(self):
        if not self.injuries:
            print('No new injuries to save')
            return None
        
        new_df = pd.DataFrame(self.injuries)
        
        try:
            existing_df = pd.read_csv(self.csv_path)
            new_df = pd.concat([new_df, existing_df], ignore_index=True)
        except FileNotFoundError:
            pass

        new_df.to_csv(self.csv_path, index=False)

        print(f"Scraping complete!")
        print(f"Total entries found: {len(self.injuries)}")
        print(f"Saved to: {self.csv_path}")

        return new_df

def main():
    scraper = InjuriesScraper()
    scraper.scrape_rss_feed()
    scraper.save_to_csv()

if __name__ == "__main__":
    main()
