from flask import Flask
from config import Config
from app.extensions import db, scheduler
import os

def create_app():
    base_dir = os.path.abspath(os.path.dirname(__file__)) # Gets path to /app
    template_dir = os.path.join(base_dir, 'templates') 
    static_dir = os.path.join(base_dir, 'static') 

    app = Flask(__name__, template_folder=template_dir, static_folder=static_dir)
    app.config.from_object(Config)

    # Initialize Extensions
    db.init_app(app)
    
    # Register Blueprints
    from app.routes.auth import auth_bp
    from app.routes.student import student_bp
    from app.routes.teacher import teacher_bp
    from app.routes.admin import admin_bp

    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(student_bp, url_prefix='/student')
    app.register_blueprint(teacher_bp, url_prefix='/teacher')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    
    # Redirect root to auth login for convenience
    @app.route('/')
    def index():
        from flask import redirect, url_for
        return redirect(url_for('auth.login'))

    # Start Scheduler (if not in debug/reloader mode to avoid duplicates)
    if not app.debug or os.environ.get('WERKZEUG_RUN_MAIN') == 'true':
        from app.services.scheduler_jobs import init_scheduler
        init_scheduler(app, scheduler)

    return app