import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By as selenium_by
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as selenium_ec
from bs4 import BeautifulSoup

class ESPNProjectionScraper:
    def __init__(self, headless=True):
        self.url = "https://fantasy.espn.com/football/players/projections"
        self.positions = {'QB', 'RB', 'WR', 'TE', 'K', 'D/ST'}
        self.players = []

        chrome_options = webdriver.chrome.options.Options()
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--mute-audio')
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')

        if headless: chrome_options.add_argument('--headless')

        self.browser = webdriver.Chrome(options=chrome_options)

    def wait_for_page_to_load(self, timeout=30):
        try:
            WebDriverWait(self.browser, timeout).until(
                selenium_ec.presence_of_element_located(
                    (selenium_by.CSS_SELECTOR, '.jsx-2175038926.full-projection-table')
                )
            )

            time.sleep(2)
            return True
        
        except Exception as e:
            print(f'Page could not be scraped: {e}')
            return False

    def extract_players_from_page(self):
        players = []
        soup = BeautifulSoup(self.browser.page_source, 'html.parser')
        selectors = {
            'container': 'div.jsx-2175038926.player-info-section.flex',
            'name_selector': 'a.AnchorLink.link.clr-link.pointer',
            'position_selector': 'span.position-eligibility',
            'team_selector': 'span.player-teamname',
            'stats_selector': 'tr[data-idx="1"] td.Table__TD:not(.player-year-col)',
        }

        containers = soup.select(selectors['container'])
        for container in containers:
            try:
                player = {}
                defense_detector = container.find_all('span', string=lambda x: 'D/ST' in x)
                is_defense = True if defense_detector else False

                if is_defense:
                    name_link = container.select_one('a.AnchorLink.link.clr-link.pointer')
                    team_name = name_link.get_text(strip=True)[:-5]
                    
                    player['name'] = f"{team_name} D/ST"
                    player['position'] = 'D/ST'
                    player['team'] = team_name
                else:
                    name_element = container.select_one(selectors['name_selector'])
                    player['name'] = name_element.get_text(strip=True)

                    position_element = container.select_one(selectors['position_selector'])
                    position_text = position_element.get_text(strip=True)
                    if ',' in position_text:
                        positions = [pos.strip() for pos in position_text.split(',')]
                        for pos in positions:
                            if pos in self.positions:
                                player['position'] = pos
                                break
                    else:
                        player['position'] = position_text

                    team_element = container.select_one(selectors['team_selector'])
                    player['team'] = team_element.get_text(strip=True)

                stats = container.select(selectors['stats_selector'])
                for table_data in stats:
                    stat = table_data.select_one('div')
                    player[stat.get('title')] = stat.get_text(strip=True)

                players.append(player)

            except Exception as e:
                print(f'error getting player: {e}')
                
        return players
    
    def go_to_next_page(self): # Refactor this to remove side effect?
        try:
            button = self.browser.find_element(selenium_by.CSS_SELECTOR, '.Pagination__Button--next')
            if button.is_enabled():
                self.browser.execute_script('arguments[0].scrollIntoView();', button)
                time.sleep(.5)
                button.click()
                return True
            return False
        except Exception as e:
            print(f'error loading next page: {e}')
            return False

    def scrape_all_pages(self, max_pages=25):
        try:
            self.browser.get(self.url)
            current_page = 1

            while current_page <= max_pages:
                if not self.wait_for_page_to_load():
                    print('Failed to load page, trying anyway...')

                current_page_players = self.extract_players_from_page()
                if not current_page_players and current_page == 1:
                    print('No players found on page 1 - ESPN structure may have changed')
                    break

                if current_page_players:
                    self.players.extend(current_page_players)
                    print(f"Page {current_page}: Added {len(current_page_players)} players")
                else:
                    print(f"No players found on page {current_page}")

                if current_page < max_pages:
                    went_to_next_page = self.go_to_next_page()
                    if went_to_next_page:
                        if not self.wait_for_page_to_load(timeout=10):
                            print("Page didn't load properly")
                            break
                        current_page += 1
                    else:
                        print('Reached last page')
                        break
                else:
                    print(f"Reached max page limit ({max_pages})")

            return self.players
        finally:
            self.browser.quit()

    def save_to_csv(self, filename='../../data/sql/this_weeks_projections.csv'):
        if not self.players:
            print('No players saved - ESPN structure may have changed')
            return None
        
        df = pd.DataFrame(self.players)
        df = df.drop_duplicates(subset=['name', 'position'], keep='first')
        df = df.sort_values(['position', 'name'])
        df.to_csv(filename, index=False)

        print(f"\nScraping complete!")
        print(f"Total players found: {len(df)}")
        print(f"Saved to: {filename}")

        position_counts = df['position'].value_counts()
        print(f"\nPlayers by Position:")
        for pos, count in position_counts.items():
            print(f"{pos}: {count}")

        return df
    
def main():
    print("ESPN Fantasy Football Player Scraper")
    print("=" * 50)

    scraper = ESPNProjectionScraper(headless=False)

    try:
        players = scraper.scrape_all_pages(max_pages=25)

        if players:
            scraper.save_to_csv('../../data/sql/this_weeks_projections.csv')
        else:
            print("No players scraped - check debug files")

    except Exception as e:
        print(f"Error during scraping: {e}")

if __name__ == "__main__":
    main()
