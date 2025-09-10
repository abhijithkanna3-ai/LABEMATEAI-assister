import os
import logging
from flask import Flask
from werkzeug.middleware.proxy_fix import ProxyFix

# Configure logging - reduce verbosity
logging.basicConfig(level=logging.WARNING)
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
logging.getLogger('matplotlib').setLevel(logging.WARNING)
logging.getLogger('urllib3').setLevel(logging.WARNING)

# Create the app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key-change-in-production")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Configure the database
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///labmate.db")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}

# Import models first to get db instance
import models
db = models.db

# Initialize the app with the extension
db.init_app(app)

with app.app_context():
    # Import routes and chatbot
    import routes
    import enhanced_chatbot  # Import enhanced chatbot module to initialize it
    
    # Create all tables
    db.create_all()
