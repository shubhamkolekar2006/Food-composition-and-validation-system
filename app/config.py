import os

# Load environment variables from .env file if present
BASE_DIR = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
env_path = os.path.join(BASE_DIR, '.env')
if os.path.exists(env_path):
    with open(env_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, val = line.split('=', 1)
                os.environ[key.strip()] = val.strip().strip('"').strip("'")

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'food-validation-secret-key-129847')
    
    # PostgreSQL configuration with SQLite fallback
    DATABASE_URL = os.environ.get('DATABASE_URL')
    if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
        # Fix for Heroku/Render postgres prefix issue if present
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
        
    SQLALCHEMY_DATABASE_URI = DATABASE_URL or 'sqlite:///products.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # ML Model configuration
    BASE_DIR = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
    ML_MODEL_PATH = os.environ.get('ML_MODEL_PATH', os.path.join(BASE_DIR, 'ml', 'model.pkl'))
    
    # Gemini API Configuration
    GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY') or os.environ.get('GOOGLE_API_KEY')

