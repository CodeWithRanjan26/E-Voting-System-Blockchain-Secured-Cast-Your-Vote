from flask import Flask

# Create the Flask application object
app = Flask(__name__)
app.secret_key = "test_secret_123"

# Import blueprints AFTER creating the app
from app.views import views
from app.service import service

# Register blueprints
app.register_blueprint(views)                  # Website UI routes
app.register_blueprint(service, url_prefix="/api")  # Blockchain service routes
