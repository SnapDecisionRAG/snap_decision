from datetime import datetime, date, timedelta

def get_current_week(db_manager):
    today = date.today()

    with db_manager.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT week, MAX(game_date) as last_game_date
            FROM schedule
            GROUP BY week
            ORDER BY week
        """)

        weeks = cursor.fetchall()

        for i, week_data in enumerate(weeks):
            week_num = week_data['week']
            last_game_date = datetime.strptime(week_data['last_game_date'], '%Y-%m-%d').date()

            if i == 0:
                week_start = last_game_date - timedelta(days=6)
            else:
                last_week_end = datetime.strptime(weeks[i-1]['last_game_date'], '%Y-%m-%d').date()
                week_start = last_week_end + timedelta(days=1)

            if week_start <= today <= last_game_date:
                return week_num

        return None

def daily_needs_to_run(db_manager, scraper_name, min_hour=10):
    now = datetime.now()
    if now.hour < min_hour:
        return False
    
    today = date.today()
    with db_manager.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT last_run
            FROM scrapers_last_run
            WHERE scraper_name = ?
            AND last_run >= ?
        """, (scraper_name, today))

        result = cursor.fetchone()
        return result is None

def get_week_range(db_manager, week):
    with db_manager.get_connection() as conn:
        cursor = conn.cursor()

        cursor.execute("""
            SELECT week, MAX(game_date) as last_game_date
            FROM schedule
            WHERE week = ?
        """, (week,))

        result = cursor.fetchone()
        if not result or not result['last_game_date']:
            raise ValueError(f"No games found for week {week}")
        
        week_end = datetime.strptime(result['last_game_date'], '%Y-%m-%d').date()

        cursor.execute("""
            SELECT week, MAX(game_date) as last_game_date
            FROM schedule
            WHERE week = ?
        """, (week - 1,))

        prev_result = cursor.fetchone()
        if prev_result and prev_result['last_game_date']: # needed null check
            prev_week_end = (
                datetime.strptime(prev_result['last_game_date'], '%Y-%m-%d').date()
            )
            week_start = prev_week_end + timedelta(days=1)
        else:
            week_start = week_end - timedelta(days=6)

        return week_start, week_end

def need_to_scrape_scores(db_manager, week):
    try:
        _, week_end = get_week_range(db_manager, week)
        today = datetime.today()

        if today.date() <= week_end:
            return False
        
        tuesday_after = week_end + timedelta(days=1)

        can_scrape = today.date() > tuesday_after or (today.date() == tuesday_after and today.hour >= 10)
        if not can_scrape:
            return False

        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT last_run, status 
                FROM scrapers_last_run 
                WHERE scraper_name = ? 
                ORDER BY last_run DESC 
                LIMIT 1
            """, (f"actual_scores_week_{week}",))

            result = cursor.fetchone()

            if result and result['status'] == 'success':
                return False

        return True
        
    except Exception as e:
        return False
