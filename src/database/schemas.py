# src/database/schemas.py

HISTORICAL_STATS_SCHEMA = """
CREATE TABLE historical_stats (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    player_name TEXT NOT NULL,
    position TEXT NOT NULL,
    team TEXT,
    season INTEGER,
    week INTEGER,
    game_date DATE,
    fantasy_points REAL,
    ppr_points REAL,
    dk_points REAL,
    fd_points REAL,
    game_number INTEGER,
    age TEXT,
    opponent TEXT,
    result TEXT,
    -- Passing stats
    passing_completions INTEGER,
    passing_attempts INTEGER,
    passing_yards INTEGER,
    passing_tds INTEGER,
    interceptions INTEGER,
    -- Rushing stats
    rushing_attempts INTEGER,
    rushing_yards INTEGER,
    rushing_tds INTEGER,
    -- Receiving stats
    receptions INTEGER,
    receiving_yards INTEGER,
    receiving_tds INTEGER,
    targets INTEGER,
    -- Snap counts
    off_snaps INTEGER,
    off_percent REAL,
    def_snaps INTEGER,
    def_percent REAL,
    st_snaps INTEGER,
    st_percent REAL,
    -- Kicking stats
    field_goals_made INTEGER,
    field_goals_attempted INTEGER,
    extra_points_made INTEGER,
    extra_points_attempted INTEGER,
    -- Defense stats
    sacks REAL,
    def_interceptions REAL,
    fumble_recoveries REAL,
    safeties REAL,
    defensive_tds REAL,
    points_allowed REAL,
    yards_allowed REAL
);
"""

PROJECTIONS_SCHEMA = """
CREATE TABLE projections (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    player_name TEXT NOT NULL,
    position TEXT NOT NULL,
    team TEXT,
    fantasy_points REAL,
    -- Passing stats
    pass_comp_att TEXT,
    passing_yards TEXT,
    passing_tds TEXT,
    interceptions_thrown TEXT,
    -- Rushing stats
    rushing_attempts TEXT,
    rushing_yards TEXT,
    rushing_tds TEXT,
    rushing_ypa TEXT,
    -- Receiving stats
    receptions TEXT,
    receiving_yards TEXT,
    receiving_tds TEXT,
    targets TEXT,
    receiving_ypc TEXT,
    -- Kicking stats
    fg_made_att_0_39 TEXT,
    fg_made_att_40_49 TEXT,
    fg_made_att_50_plus TEXT,
    fg_made_att_total TEXT,
    xp_made_att TEXT,
    -- Defense stats
    sacks TEXT,
    def_interceptions TEXT,
    fumble_recoveries TEXT,
    return_tds REAL,
    points_allowed REAL,
    yards_allowed REAL,
    fumbles_forced TEXT,
    assisted_tackles TEXT,
    total_tackles TEXT,
    passes_defensed TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

ACTUAL_SCORES_SCHEMA = """
CREATE TABLE actual_scores (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    week INTEGER,
    player_name TEXT NOT NULL,
    position TEXT NOT NULL,
    opponent TEXT,
    status TEXT,
    fantasy_points REAL,
    -- Passing stats
    pass_comp_att TEXT,
    passing_yards TEXT,
    passing_tds TEXT,
    interceptions_thrown TEXT,
    -- Rushing stats
    rushing_attempts TEXT,
    rushing_yards TEXT,
    rushing_tds TEXT,
    -- Receiving stats
    receptions TEXT,
    receiving_yards TEXT,
    receiving_tds TEXT,
    targets TEXT,
    -- Special offensive stats
    two_point_conversions TEXT,
    fumbles_lost TEXT,
    return_tds TEXT,
    -- Defense stats
    def_interceptions REAL,
    fumble_recoveries REAL,
    sacks REAL,
    safeties REAL,
    blocked_kicks REAL,
    points_allowed REAL,
    yards_allowed REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

WEATHER_SCHEMA = """
CREATE TABLE weather (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    week INTEGER,
    forecast_date DATE,
    away_team TEXT,
    home_team TEXT,
    game_date DATE,
    start_time TEXT,
    stadium TEXT,
    covered_dome BOOLEAN,
    precipitation_percent_chance JSON,
    temperature JSON,
    humidity JSON,
    dewpoint JSON,
    wind_direction JSON,
    wind_mph JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

INJURIES_SCHEMA = """
CREATE TABLE injuries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    player_name TEXT,
    title TEXT,
    published TEXT,
    link TEXT,
    summary TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

LATEST_NEWS_SCHEMA = """
CREATE TABLE latest_news (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    player_or_team TEXT,
    title TEXT,
    published TEXT,
    link TEXT,
    summary TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

SCHEDULE_SCHEMA = """
CREATE TABLE schedule (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    week INTEGER,
    game_date DATE,
    day_of_week TEXT,
    away_team TEXT,
    home_team TEXT,
    time_et TEXT,
    network TEXT,
    location TEXT,
    bye_teams TEXT
);
"""

PLAYERS_SCHEMA = """
CREATE TABLE players (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    player_name TEXT NOT NULL,
    position TEXT NOT NULL,
    team TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(player_name, position)
);
"""

SCRAPERS_LAST_RUN_SCHEMA = """
CREATE TABLE scrapers_last_run (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    scraper_name TEXT NOT NULL,
    last_run TIMESTAMP NOT NULL,
    status TEXT,
    records_processed INTEGER,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

SCORING_TEMPLATE_SCHEMA = """
CREATE TABLE scoring_template (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    scoring_type TEXT,
    stat_category TEXT,
    stat_name TEXT,
    standard_points REAL,
    ppr_points REAL,
    half_ppr_points REAL,
    six_pt_passing_td REAL,
    te_premium REAL,
    superflex_notes TEXT
);
"""

SCHEMAS = {
    'historical_stats': HISTORICAL_STATS_SCHEMA,
    'projections': PROJECTIONS_SCHEMA,
    'actual_scores': ACTUAL_SCORES_SCHEMA,
    'weather': WEATHER_SCHEMA,
    'injuries': INJURIES_SCHEMA,
    'latest_news': LATEST_NEWS_SCHEMA,
    'schedule': SCHEDULE_SCHEMA,
    'players': PLAYERS_SCHEMA,
    'scrapers_last_run': SCRAPERS_LAST_RUN_SCHEMA,
    'scoring_template': SCORING_TEMPLATE_SCHEMA
}

INDEXES = [
    "CREATE INDEX idx_historical_player_week ON historical_stats(player_name, week);",
    "CREATE INDEX idx_historical_position ON historical_stats(position);",
    "CREATE INDEX idx_historical_season ON historical_stats(season);",
    "CREATE INDEX idx_projections_player ON projections(player_name);",
    "CREATE INDEX idx_actual_player_week ON actual_scores(player_name, week);",
    "CREATE INDEX idx_weather_week ON weather(week);",
    "CREATE INDEX idx_weather_teams ON weather(away_team, home_team);",
    "CREATE INDEX idx_schedule_week ON schedule(week);",
    "CREATE INDEX idx_players_position ON players(position);",
    "CREATE INDEX idx_scraper_name ON scrapers_last_run(scraper_name);"
]
