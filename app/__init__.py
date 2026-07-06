import os
import logging
from flask import Flask
from app.config import Config
from app.database import db

def create_app(config_class=Config):
    # Initialize Flask app
    # Set template and static folders inside the package
    app = Flask(
        __name__, 
        template_folder=os.path.join(os.path.dirname(__file__), 'templates'),
        static_folder=os.path.join(os.path.dirname(__file__), 'static')
    )
    
    app.config.from_object(config_class)
    
    # Initialize Database
    db.init_app(app)
    
    # Configure Logging
    logging.basicConfig(
        level=logging.INFO,
        format='[%(asctime)s] %(levelname)s in %(module)s: %(message)s'
    )
    
    # Register blueprints
    from app.routes import main_bp, predict_bp, scan_bp, compare_bp
    app.register_blueprint(main_bp)
    app.register_blueprint(predict_bp)
    app.register_blueprint(scan_bp)
    app.register_blueprint(compare_bp)
    
    # Ensure database tables exist (SQLite fallback support)
    with app.app_context():
        # Only auto-create tables if database URI is sqlite (useful for quick local setup)
        if 'sqlite' in app.config['SQLALCHEMY_DATABASE_URI']:
            db.create_all()
            
    # Register custom error handlers
    from flask import render_template
    
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('404.html'), 404
        
    @app.errorhandler(500)
    def internal_server_error(e):
        return render_template('500.html'), 500
            
    return app


# Create the package-level app instance for WSGI/Gunicorn entrypoint
app = create_app()

