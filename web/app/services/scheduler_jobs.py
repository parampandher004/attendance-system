from datetime import datetime, date
from app.extensions import db
from app.models import WeeklyPeriod, Period, TeacherSubject

def init_scheduler(app, scheduler):
    """
    Registers the jobs with the scheduler.
    We pass 'app' so the jobs can access the application context (db).
    """
    # Run everyday at 5:00 AM (or whenever you prefer)
    scheduler.add_job(func=generate_today_periods, trigger="cron", hour=5, minute=0, args=[app])
    
    # Run every minute to update status (scheduled -> running -> completed)
    scheduler.add_job(func=update_period_status, trigger="interval", minutes=1, args=[app])
    
    scheduler.start()

def generate_today_periods(app):
    """
    Copies the Weekly Schedule (Template) into actual Periods for today.
    """
    with app.app_context():
        today = date.today()
        day_of_week = int(today.strftime("%w")) # 0=Sunday, 1=Monday...

        # Check if periods already generated for today to avoid duplicates
        existing = Period.query.filter_by(date=today).first()
        if existing:
            print(f"Periods for {today} already exist. Skipping generation.")
            return

        # Fetch template periods for this day of week
        weekly_templates = WeeklyPeriod.query.filter_by(day=day_of_week).all()
        
        new_periods = []
        for wp in weekly_templates:
            new_period = Period(
                teacher_subject_id=wp.teacher_subject_id,
                day=day_of_week,
                start_time=wp.start_time,
                end_time=wp.end_time,
                date=today,
                is_manual=0,
                status='scheduled'
            )
            db.session.add(new_period)
        
        if new_periods:
            db.session.commit()
            print(f"Generated {len(new_periods)} periods for {today}.")

def update_period_status(app):
    """
    Updates the status of periods based on current time.
    """
    with app.app_context():
        now = datetime.now()
        current_time = now.time()
        today = date.today()

        # 1. scheduled -> running
        # (It is today, start time has passed, end time hasn't passed)
        running_query = Period.query.filter(
            Period.date == today,
            Period.status == 'scheduled',
            Period.start_time <= current_time,
            Period.end_time >= current_time
        )
        for p in running_query.all():
            p.status = 'running'

        # 2. scheduled/running -> completed
        # (It is today, and end time has passed)
        completed_query = Period.query.filter(
            Period.date == today,
            Period.status.in_(['scheduled', 'running']),
            Period.end_time < current_time
        )
        for p in completed_query.all():
            p.status = 'completed'

        db.session.commit()