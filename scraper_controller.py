#!/usr/bin/env python3

import sys
from datetime import datetime, date

from src.sql_database.sql_db_manager import SQLDBManager
from src.sql_database.sql_static_data_loader import SQLStaticDataLoader
from src.utils.scraper_utils import get_current_week, daily_needs_to_run, need_to_scrape_scores

from src.scrapers.weather import WeatherScraper
from src.scrapers.injuries import InjuriesScraper
from src.scrapers.latest_news import NewsScraper
from src.scrapers.espn_projection_scraper import ESPNProjectionScraper
from src.scrapers.espn_scores_scraper import ESPNScoresScraper

class ScraperController:
    def __init__(self):
        self.db = SQLDBManager()

        if self._is_first_run():
            print("First run detected - Loading static data...")
            SQLStaticDataLoader(self.db)

        self.execution_log = {
            'timestamp': datetime.now(),
            'scrapers_run': [],
            'scrapers_skipped': [],
            'errors': [],
        }

    def _is_first_run(self):
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM schedule")
            row_count = cursor.fetchone()[0]
            return row_count == 0

    def insert_scraper_run(
        self,
        scraper_name,
        status,
        records_processed=0,
        error_message=None
    ):
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO scrapers_last_run
                (scraper_name, last_run, status, records_processed, error_message)
                VALUES (?, ?, ?, ?, ?)
            """, (scraper_name, datetime.now(), status, records_processed, error_message))

            conn.commit()

    def run_weather_scraper(self):
        scraper_name = 'weather'

        try:
            week = get_current_week(self.db)
            if week == None:
                self.execution_log['errors'].append(f"{scraper_name}: Could not determine current week")
                return False

            print(f"\n{'='*50}")
            print(f"Running Weather Scraper for Week {week}")
            print(f"{'='*50}")

            number_records = WeatherScraper(self.db, week).run()

            if number_records:
                self.insert_scraper_run(scraper_name, "success", number_records)
                self.execution_log['scrapers_run'].append(f"{scraper_name} (Week {week})")
                print(f"✅ Weather scraper completed")
                return True
            else:
                self.insert_scraper_run(scraper_name, "no_data", 0, "No weather data found")
                self.execution_log['scrapers_skipped'].append(f"{scraper_name}: No data available")
                print(f"⚠️ Weather scraper: No data available")
                return False

        except Exception as e:
            error_message = f"Weather scraper error: {e}"
            self.insert_scraper_run(scraper_name, "error", 0, error_message)
            self.execution_log['errors'].append(error_message)
            print(f"❌ {error_message}")
            return False

    def run_projections_scraper(self):
        scraper_name = 'projections'

        try:
            week = get_current_week(self.db)
            if week == None:
                self.execution_log['errors'].append(f"{scraper_name}: Could not determine current week")
                return False

            print(f"\n{'='*50}")
            print(f"Running Projection Scraper for Week {week}")
            print(f"{'='*50}")

            number_records = ESPNProjectionScraper(self.db, week).run()

            if number_records:
                self.insert_scraper_run(scraper_name, "success", number_records)
                self.execution_log['scrapers_run'].append(f"{scraper_name} (Week {week})")
                print(f"✅ Projections scraper completed")
                return True
            else:
                self.insert_scraper_run(scraper_name, "no_data", 0, "No Projections data found")
                self.execution_log['scrapers_skipped'].append(f"{scraper_name}: No data available")
                print(f"⚠️ Projections scraper: No data available")
                return False

        except Exception as e:
            error_message = f"Projections scraper error: {e}"
            self.insert_scraper_run(scraper_name, "error", 0, error_message)
            self.execution_log['errors'].append(error_message)
            print(f"❌ {error_message}")
            return False
        
    def run_scores_scraper(self, week):
        scraper_name = f'actual_scores_week_{week}'

        try:
            if week == None:
                self.execution_log['errors'].append(f"{scraper_name}: Could not determine current week")
                return False

            print(f"\n{'='*50}")
            print(f"Running Scores Scraper for Week {week}")
            print(f"{'='*50}")

            number_records = ESPNScoresScraper(self.db, week).run()

            if number_records:
                self.insert_scraper_run(scraper_name, "success", number_records)
                self.execution_log['scrapers_run'].append(f"{scraper_name}")
                print(f"✅ Scores scraper completed")
                return True
            else:
                self.insert_scraper_run(scraper_name, "no_data", 0, "No Scores found")
                self.execution_log['scrapers_skipped'].append(f"{scraper_name}: No data available")
                print(f"⚠️ Scores scraper: No data available")
                return False

        except Exception as e:
            error_message = f"Scores scraper error: {e}"
            self.insert_scraper_run(scraper_name, "error", 0, error_message)
            self.execution_log['errors'].append(error_message)
            print(f"❌ {error_message}")
            return False
        
    def run_injuries_scraper(self):
        scraper_name = 'injuries'

        try:
            print(f"\n{'='*50}")
            print(f"Running Injuries Scraper")
            print(f"{'='*50}")

            number_records = InjuriesScraper(self.db).run()

            if number_records:
                self.insert_scraper_run(scraper_name, "success", number_records)
                self.execution_log['scrapers_run'].append(f"{scraper_name} ({number_records} new reports)")
                print(f"✅ Injuries scraper completed")
                return True
            else:
                self.insert_scraper_run(scraper_name, "no_data", 0, "No new injury reports found")
                self.execution_log['scrapers_skipped'].append(f"{scraper_name}: No new data")
                print(f"⚠️ Injuries scraper: No new reports")
                return False

        except Exception as e:
            error_message = f"Injury scraper error: {e}"
            self.insert_scraper_run(scraper_name, "error", 0, error_message)
            self.execution_log['errors'].append(error_message)
            print(f"❌ {error_message}")
            return False

    def run_news_scraper(self):
        scraper_name = 'latest_news'

        try:
            print(f"\n{'='*50}")
            print(f"Running News Scraper")
            print(f"{'='*50}")

            number_records = NewsScraper(self.db).run()

            if number_records:
                self.insert_scraper_run(scraper_name, "success", number_records)
                self.execution_log['scrapers_run'].append(f"{scraper_name} ({number_records} new reports)")
                print(f"✅ News scraper completed")
                return True
            else:
                self.insert_scraper_run(scraper_name, "no_data", 0, "No new news reports found")
                self.execution_log['scrapers_skipped'].append(f"{scraper_name}: No new data")
                print(f"⚠️ News scraper: No new reports")
                return False

        except Exception as e:
            error_message = f"News scraper error: {e}"
            self.insert_scraper_run(scraper_name, "error", 0, error_message)
            self.execution_log['errors'].append(error_message)
            print(f"❌ {error_message}")
            return False

def main():
    try:
        controller = ScraperController()

        if daily_needs_to_run(controller.db, "weather"):
            controller.run_weather_scraper()

        if daily_needs_to_run(controller.db, "projections"):
            controller.run_projections_scraper()

        current_week = get_current_week(controller.db)
        for week in range(1, current_week + 1):
            if need_to_scrape_scores(controller.db, week):
                controller.run_scores_scraper(week)

        controller.run_injuries_scraper()
        controller.run_news_scraper()

    except Exception as e:
        print(f"Error running scrapers: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
