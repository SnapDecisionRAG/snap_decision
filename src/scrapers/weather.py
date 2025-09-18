import re
import time
import os
import pandas as pd
from datetime import datetime, date
from selenium import webdriver
from selenium.webdriver.common.by import By as selenium_by
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as selenium_ec
from bs4 import BeautifulSoup

class WeatherScraper:
    def __init__(self, headless=False):
        self.url = "https://rotogrinders.com/weather/nfl"
        self.csv_path = '../../data/sql/weather.csv'
        self.date = date.today().strftime("%Y-%m-%d")
        self.forecasts = []

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
            self.browser.get(self.url)
            WebDriverWait(self.browser, timeout).until(
                selenium_ec.presence_of_element_located(
                    (
                        selenium_by.CSS_SELECTOR,
                        '.module .weather-gametime, .module .weather-column-empty'
                    )
                )
            )

            time.sleep(2)
            return True

        except Exception as e:
            print(f'Page could not be scraped: {e}')
            return False

    def scrape_forecasts(self):
        self.wait_for_page_to_load()
        soup = BeautifulSoup(self.browser.page_source, 'html.parser')

        week_text = soup.select_one('.module-body.content p').get_text()
        week = re.search(r'Week (\d+)', week_text).group(1)

        games = soup.select('.module:has(.module-header)')
        for game in games:
            forecast = {}

            forecast['week'] = week
            forecast['forecast_date'] = self.date

            teams = game.select('.team-nameplate-mascot')
            forecast['away_team'] = teams[0].get_text().strip()
            forecast['home_team'] = teams[1].get_text().strip()

            date_time = game.select_one('.game-weather-time').get_text().strip()
            date_time = date_time.split(' ')
            raw_date = date_time[0]
            month, day = raw_date.split('/')
            year = datetime.now().year
            formatted_date = f"{year}-{month.zfill(2)}-{day.zfill(2)}"
            forecast['date'] = formatted_date
            forecast['start_time'] = f"{date_time[1]} {date_time[2]}"

            stadium = game.select_one('.game-weather-stadium')
            forecast['stadium'] = stadium.get_text().strip().replace('AT ', '')

            if game.select_one('.weather-column-empty'):
                forecast['covered_dome'] = True
                self.forecasts.append(forecast)
                continue
            forecast['covered_dome'] = False

            hourly_rows = game.select('tr')

            forecast_times = []
            time_row = hourly_rows[1].select('td')
            for table_data in time_row:
                forecast_times.append(table_data.get_text().strip())

            precip_row = hourly_rows[2].select('span.weather-column-precip')
            precip_dict = {}
            for ind, ele in enumerate(precip_row):
                precip_dict[forecast_times[ind]] = int(ele.get_text().strip()[:-1])
            forecast['precipitation_percent_chance'] = precip_dict

            temp_row = hourly_rows[3].select('td span:last-child')
            temp_dict = {}
            for ind, ele in enumerate(temp_row):
                temp_dict[forecast_times[ind]] = int(ele.get_text().strip()[:-1])
            forecast['temperature'] = temp_dict

            humidity_row = hourly_rows[4].select('td span')
            humidity_dict = {}
            for ind, ele in enumerate(humidity_row):
                humidity_dict[forecast_times[ind]] = int(ele.get_text().strip()[:-1])
            forecast['humidity'] = humidity_dict

            dewpoint_row = hourly_rows[5].select('td span')
            dewpoint_dict = {}
            for ind, ele in enumerate(dewpoint_row):
                dewpoint_dict[forecast_times[ind]] = int(ele.get_text().strip()[:-1])
            forecast['dewpoint'] = dewpoint_dict

            wind_row = hourly_rows[6].select('.weather-column-wind')
            wind_row = [div.select('span') for div in wind_row]
            wind_direction = {}
            wind_mph = {}
            for ind, values in enumerate(wind_row):
                wind_direction[forecast_times[ind]] = values[0].get_text().strip()
                wind_mph[forecast_times[ind]] = int(values[1].get_text().strip()[:-4])
            forecast['wind_direction'] = wind_direction
            forecast['wind_mph'] = wind_mph

            self.forecasts.append(forecast)

    def save_to_csv(self):
        if not self.forecasts:
            print('No forecasts found, Roto Grinders may have changed their site')
            return None

        df = pd.DataFrame(self.forecasts)
        df.to_csv(self.csv_path, mode='a', header=not os.path.exists(self.csv_path), index=False)

        print(f"Scraping complete!")
        print(f"Total entries found: {len(self.forecasts)}")
        print(f"Saved to: {self.csv_path}")


def main():
    scraper = WeatherScraper()
    scraper.scrape_forecasts()
    scraper.save_to_csv()

if __name__ == "__main__":
    main()
