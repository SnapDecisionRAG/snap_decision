from datetime import datetime
from pathlib import Path
import pandas as pd

class StaticDataLoader:
    def __init__(self, db_manager):
        self.db = db_manager
        self.data_dir = Path("data/sql")

        if self._is_first_run():
            print("First run detected - Loading static data...")
            self.load_all_data()
        else:
            print("Static data already loaded")

    def _is_first_run(self):
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM schedule")
            row_count = cursor.fetchone()[0]
            return row_count == 0

    def load_all_data(self):
        print("Starting historical data loading process...")

        self.load_schedule()
        self.load_scoring_template()
        self.load_players()
        self.load_historical_stats()

        print("Data loading complete")

    def load_schedule(self):
        file = self.data_dir / "schedule.csv"
        if not file.exists():
            print(f"Warning: {file} not found, skipping schedule data")
            return

        print("Loading schedule data...")

        df = pd.read_csv(file)

        print(f"Found {len(df)} games in schedule")

        schedule = []
        for _, row in df.iterrows():
            schedule.append((
                row["week"],
                row["date"],
                row["day"],
                row["away_team"],
                row["home_team"],
                row["time_et"],
                row["location"],
                row["bye_teams"] if pd.notna(row["bye_teams"]) else None
            ))

        with self.db.get_connection() as conn:
            cursor = conn.cursor()

            insert_query = """
                INSERT INTO schedule (
                    week,
                    game_date,
                    day_of_week,
                    away_team,
                    home_team,
                    time_et,
                    international_location,
                    bye_teams
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """

            cursor.executemany(insert_query, schedule)
            conn.commit()

        print(f"Successfully loaded {len(schedule)} games into schedule table")

    def load_scoring_template(self):
        file = self.data_dir / "scoring_template.csv"
        if not file.exists():
            print(f"Warning: {file} not found, skipping scoring template data")
            return

        print("Loading scoring_template data...")

        df = pd.read_csv(file)

        print(f"Found {len(df)} scoring rules")

        scoring_data = []
        for _, row in df.iterrows():
            scoring_data.append((
                row["scoring_type"],
                row["stat_category"], 
                row["stat_name"],
                row["standard_points"],
                row["ppr_points"],
                row["half_ppr_points"],
            ))

        with self.db.get_connection() as conn:
            cursor = conn.cursor()

            insert_query = """
                INSERT INTO scoring_template (
                    scoring_type,
                    stat_category,
                    stat_name,
                    standard_points,
                    ppr_points,
                    half_ppr_points
                ) VALUES (?, ?, ?, ?, ?, ?)
            """
            cursor.executemany(insert_query, scoring_data)
            conn.commit()

        print(f"Successfully loaded {len(scoring_data)} scoring rules into scoring_template table")
        
    def load_players(self):
        file = self.data_dir / "all_current_players.csv"
        if not file.exists():
            print(f"Warning: {file} not found, skipping players data")
            return

        print("Loading players data...")

        df = pd.read_csv(file)

        print(f"Found {len(df)} players")

        players_data = []
        for _, row in df.iterrows():
            players_data.append((row["name"], row["position"], row["team"]))

        with self.db.get_connection() as conn:
            cursor = conn.cursor()

            insert_query = """
                INSERT INTO players (
                    player_name,
                    position,
                    team
                ) VALUES (?, ?, ?)
            """
            cursor.executemany(insert_query, players_data)
            conn.commit()

        print(f"Successfully loaded {len(players_data)} players into players table")

    def calculate_season(self, date_str):
        date_obj = datetime.strptime(date_str, "%Y-%m-%d")

        if date_obj.month >= 9:
            return date_obj.year
        elif date_obj.month <= 2:
            return date_obj.year - 1
        else:
            return date_obj.year
    
    def load_historical_stats(self):
        print("Loading historical stats...")

        position_files = {
            "qb.csv": "QB",
            "rb.csv": "RB",
            "wr.csv": "WR",
            "te.csv": "TE",
            "kicker.csv": "K",
        }

        for filename, position in position_files.items():
            file = self.data_dir / "historical_player_stats" / "raw" / filename
            if not file.exists():
                print(f"Warning: {file} not found, skipping {position} data")
                continue

            print(f"Loading {position} historical stats from {filename}...")

            try:
                df = pd.read_csv(file)

                print(f"Found {len(df)} {position} stat records")

                stats_data = []
                for _, row in df.iterrows():
                    season = self.calculate_season(row["Date"])
                    stats_data.append((
                        row["Player"],
                        position,
                        row.get("Tm", None),
                        season,
                        row.get("Week", None),
                        row["Date"],
                        row.get("FantPt", None),
                        row.get("PPR", None),
                        row.get("DK", None),
                        row.get("FD", None),
                        row.get("G#", None),
                        row.get("Age", None),
                        row.get("Opp", None),
                        row.get("Result", None),
                        row.get("Cmp", None),
                        row.get("Att", None),
                        row.get("Yds", None),
                        row.get("TD", None),
                        row.get("Int", None),
                        row.get("Att.1", None),
                        row.get("Yds.1", None),
                        row.get("TD.1", None),
                        row.get("Rec", None),
                        row.get("Yds.2", None),
                        row.get("TD.2", None),
                        row.get("Tgt", None),
                        row.get("Off", None),
                        row.get("Off%", None),
                        row.get("Def", None),
                        row.get("Def%", None),
                        row.get("ST", None),
                        row.get("ST%", None),
                        row.get("FGM", None),
                        row.get("FGA", None),
                        row.get("XPM", None),
                        row.get("XPA", None),
                        row.get('Sk', None),
                        row.get('Int.1', None),
                        row.get('FR', None),
                        row.get('Sfty', None),
                        row.get('TD.3', None),
                        row.get('PA', None),
                        row.get('YA', None),
                    ))

                with self.db.get_connection() as conn:
                    cursor = conn.cursor()

                    insert_query = """
                        INSERT INTO historical_stats (
                            player_name, position, team, season, week, game_date,
                            fantasy_points, ppr_points, dk_points, fd_points, game_number,
                            age, opponent, result,
                            passing_completions, passing_attempts, passing_yards, passing_tds, interceptions,
                            rushing_attempts, rushing_yards, rushing_tds,
                            receptions, receiving_yards, receiving_tds, targets,
                            off_snaps, off_percent, def_snaps, def_percent, st_snaps, st_percent,
                            field_goals_made, field_goals_attempted, extra_points_made, extra_points_attempted,
                            sacks, def_interceptions, fumble_recoveries, safeties, defensive_tds,
                            points_allowed, yards_allowed
                        ) VALUES (
                            ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                            ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                            ?, ?, ?, ?, ?, ?, ?, ?, ?
                        )
                    """

                    cursor.executemany(insert_query, stats_data)
                    conn.commit()

                print(f"Successfully loaded {len(stats_data)} records")

            except Exception as e:
                print(f"Error loading {filename}: {e}")
                continue

        print(f"Historical stats loading complete!")
