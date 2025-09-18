import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By as selenium_by
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as selenium_ec
from bs4 import BeautifulSoup

class ESPNScoresScraper:
    def __init__(self, headless=False):
        self.url = 'https://fantasy.espn.com/football/leaders'
        self.positions = {'QB', 'RB', 'WR', 'TE', 'K', 'D/ST'}
        self.players = []

        chrome_options = webdriver.chrome.options.Options()
        if headless:
            chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument(
            '--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) ' +
            'AppleWebKit/537.36'
        )

        self.browser = webdriver.Chrome(options=chrome_options)

    def wait_for_page_to_load(self, timeout=30):
        try:
            WebDriverWait(self.browser, timeout).until(
                selenium_ec.presence_of_element_located(
                    (selenium_by.CSS_SELECTOR, '.Table__TBODY')
                )
            )

            time.sleep(2)
            return True
        
        except Exception as e:
            print(f'Page could not be loaded: {e}')
            return False
        
    def click_dst_position(self):
        try:
            dst_label = WebDriverWait(
                self.browser,
                timeout=10,
                poll_frequency=0.1
            ).until(selenium_ec.element_to_be_clickable(
                (selenium_by.XPATH, "//label[contains(text(), 'D/ST')]")
            ))

            self.browser.execute_script(
                'arguments[0].scrollIntoView();',
                dst_label
            )

            self.browser.execute_script('arguments[0].click();', dst_label)

            time.sleep(2)
            return True
        except Exception as e:
            print(f'Error clicking D/ST position: {e}')
            return False
        
    def extract_players_from_page(self, week):
        players = []
        soup = BeautifulSoup(self.browser.page_source, 'html.parser')
        selectors = {
            'row': 'tr.Table__TR.Table__TR--lg.Table__odd',
            'name_selector': 'a.AnchorLink.link.clr-link.pointer',
            'position_selector': 'span.playerinfo__playerpos',
            'stats_selector': 'td.Table__TD',
        }

        table_rows = soup.select(selectors['row'])
        player_row_groups = {}
        
        for row in table_rows:
            data_idx = row.get('data-idx')
            if data_idx not in player_row_groups:
                player_row_groups[data_idx] = []
            player_row_groups[data_idx].append(row)

        print(f'Found {len(player_row_groups)} player rows')

        for data_idx in player_row_groups.keys():
            try:
                player = {'week': week}
                player_cells = []
                
                for row in player_row_groups[data_idx]:
                    player_cells.extend(row.select('td.Table__TD'))

                player_name = None
                player_pos = None

                for cell in player_cells:
                    name_link = cell.select_one(selectors['name_selector'])
                    player_name = name_link.get_text(strip=True)

                    position = cell.select_one(selectors['position_selector'])
                    player_pos = position.get_text(strip=True)

                    break

                player['name'] = player_name

                if ',' in player_pos:
                    positions = [pos.strip() for pos in player_pos.split(',')]
                    for pos in positions:
                        if pos in self.positions:
                            player['position'] = pos
                            break
                else:
                    player['position'] = player_pos

                header_rows = soup.select('tr.Table__sub-header')
                all_headers = []

                for header in header_rows:
                    all_headers.extend(
                        [div.get('title') for div in header.select('div')
                        if div.get('title')]
                    )

                ignored_columns = ['Player', 'Type', 'Action']
                stat_headers = [h for h in all_headers
                                if h not in ignored_columns]
                stats = player_cells[3:]

                for idx, cell in enumerate(stats):
                    player[stat_headers[idx]] = cell.get_text(strip=True)

                players.append(player)

            except Exception as e:
                print(f'Error processing player row: {e}')
                continue

        return players
    
    def go_to_next_page(self):
        try:
            button = self.browser.find_element(
                selenium_by.CSS_SELECTOR,
                '.Pagination__Button--next'
            )
            if button.is_enabled():
                self.browser.execute_script(
                    'arguments[0].scrollIntoView();',
                    button
                )
                time.sleep(.5)
                button.click()
                return True
            return False
        except Exception as e:
            print(f'error loading next page: {e}')
            return False
        
    def scrape_week(self, week, max_pages=25):
        url = (
            f'{self.url}?statSplit=singleScoringPeriod&scoringPeriodId={week}'
        )
        print(f'\nScraping Week {week}: {url}')

        try:
            self.browser.get(url)
            current_page = 1

            while current_page <= max_pages:
                print(f'Offensive Players Week {week}, Page {current_page}...')

                if not self.wait_for_page_to_load():
                    print('Failed to load page, trying anyway...')

                current_page_players = self.extract_players_from_page(week)
                
                if not current_page_players and current_page == 1:
                    print('No players on first page - may be an issue')
                    break

                if current_page_players:
                    self.players.extend(current_page_players)
                    print(f'Added {len(current_page_players)} players')
                else:
                    print(f"No offensive players found on page {current_page}")

                if current_page < max_pages:
                    went_to_next_page = self.go_to_next_page()
                    if went_to_next_page:
                        if not self.wait_for_page_to_load(timeout=10):
                            print("Next page did not load properly")
                            break
                        current_page += 1
                    else:
                        print(f'Reached last page for week {week}')
                        break
                else:
                    print(f'Reached max page limit ({max_pages})')
                    break
            
            time.sleep(2)
            self.click_dst_position()
            print(f'Defense Week {week}, Page 1...')

            if not self.wait_for_page_to_load():
                print('Failed to load page, trying anyway...')

            current_page_players = self.extract_players_from_page(week)
            
            if current_page_players:
                self.players.extend(current_page_players)
                print(f'Added {len(current_page_players)} defenses')
            else:
                print(f"No defenses found - may be an issue")

            return self.players

        except Exception as e:
            print(f'Error scraping week {week}: {e}')

    def save_to_csv(self, filename='data/sql/actual_scores.csv'):
        if not self.players:
            print('No players to save')
            return None
        
        df = pd.DataFrame(self.players)
        df = df.drop_duplicates(subset=['name', 'position'], keep='first')
        df.to_csv(filename, index=False)

        print(f'\n=== SCRAPING COMPLETE ===')
        print(f'Total player records: {len(df)}')
        print(f'Saved to: {filename}')

        week_counts = df['week'].value_counts()
        for week, count in week_counts.items():
            print(f'Week {week}: {count}')

        # position_counts = df['position'].value_counts()
        # print(f"\nPlayers by Position:")
        # for pos, count in position_counts.items():
        #     print(f"{pos}: {count}")

        return df
    
    def close(self):
        if self.browser:
            self.browser.quit()
    
def main():
    print('ESPN Fantasy Football Actual Score Scraper')
    print('=' * 60)

    scraper = ESPNScoresScraper(headless=False)

    try:
        players = scraper.scrape_week(week=2, max_pages=25)

        if players:
            df = scraper.save_to_csv('../../data/sql/actual_scores_wk2.csv')

            position_counts = df['position'].value_counts()
            print(f"\nPosition breakdown:")
            for pos, count in position_counts.items():
                print(f"{pos}: {count}")
        else:
            print('No players scraped - check the page structure')

    except Exception as e:
        print(f'Error during scraping: {e}')

    finally:
        scraper.close()

if __name__ == '__main__':
    main()
