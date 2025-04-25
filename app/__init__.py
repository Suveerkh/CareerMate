from flask import Flask
from supabase import create_client
from dotenv import load_dotenv
import os

# Load environment variables from the .env file
load_dotenv()

# Flask app initialization
app = Flask(__name__)

# Supabase credentials (replace with your actual credentials in the .env file)
SUPABASE_URL = os.getenv('SUPABASE_URL')  # Get Supabase URL from environment variable
SUPABASE_KEY = os.getenv('SUPABASE_KEY')  # Get Supabase API key from environment variable

# Initialize Supabase client
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Secret key for session management, loaded from environment variable
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY')  # Get Flask secret key from .env

# Import routes after initializing the app
from app import routes
