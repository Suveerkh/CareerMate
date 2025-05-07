import pytest
import sys
import os
import json
from datetime import datetime
from unittest.mock import patch, MagicMock

# Add the parent directory to the path so we can import the app module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app import app

# Mock career categories
MOCK_CAREER_CATEGORIES = [
    {"id": 1, "name": "Technology", "description": "Careers in technology and computing"},
    {"id": 2, "name": "Healthcare", "description": "Careers in healthcare and medicine"},
    {"id": 3, "name": "Business", "description": "Careers in business and management"}
]

# Mock Supabase client
class MockSupabaseClient:
    def __init__(self):
        self.data = []
        self.status_code = 200
        
    def table(self, table_name):
        return self
        
    def select(self, *args):
        return self
        
    def filter(self, column, operator, value):
        return self
        
    def order(self, column, desc=False):
        return self
        
    def execute(self):
        class Response:
            def __init__(self):
                self.data = []
                self.status_code = 200
        return Response()

@pytest.fixture
def client(monkeypatch):
    # Mock environment variables
    monkeypatch.setenv("SUPABASE_URL", "http://mock.supabase.co")
    monkeypatch.setenv("SUPABASE_KEY", "mock_key")
    
    app.config['TESTING'] = True
    app.config['SECRET_KEY'] = 'test_key'
    
    # Disable Flask-Session to avoid session serialization issues
    app.config['SESSION_TYPE'] = None
    
    # Mock the Supabase client
    app.supabase = MockSupabaseClient()
    
    # Mock the init_supabase function to do nothing
    def mock_init_supabase():
        pass
    
    # Apply the mock if init_supabase exists in the app module
    if hasattr(app, 'init_supabase'):
        monkeypatch.setattr(app, 'init_supabase', mock_init_supabase)
    
    # Mock CAREER_CATEGORIES if it exists in the app module
    if hasattr(app, 'CAREER_CATEGORIES'):
        monkeypatch.setattr(app, 'CAREER_CATEGORIES', MOCK_CAREER_CATEGORIES)
    else:
        # If CAREER_CATEGORIES is imported from another module, we need to patch it
        monkeypatch.setattr('app.CAREER_CATEGORIES', MOCK_CAREER_CATEGORIES)
    
    # Mock the news updater function to do nothing
    if hasattr(app, 'start_news_updater'):
        monkeypatch.setattr(app, 'start_news_updater', lambda: None)
    
    with app.test_client() as client:
        # Use Flask's built-in session instead of Flask-Session
        with client.session_transaction() as session:
            session['user_id'] = 'test_user'
            session['username'] = 'Test User'
            session['email'] = 'test@example.com'
        yield client

def test_home_page(client):
    """Test that the home page loads correctly."""
    response = client.get('/')
    assert response.status_code == 200
    assert b'CareerMate' in response.data

def test_careers_page(client):
    """Test that the careers page loads correctly."""
    response = client.get('/careers')
    assert response.status_code == 200
    assert b'Career Categories' in response.data

def test_profile_page(client):
    """Test that the profile page loads correctly."""
    response = client.get('/profile')
    assert response.status_code == 200
    assert b'Profile' in response.data

def test_login_page_redirect(client):
    """Test that the login page redirects to profile when already logged in."""
    response = client.get('/login')
    assert response.status_code == 302
    assert '/profile' in response.headers['Location']

def test_signup_page_redirect(client):
    """Test that the signup page redirects to profile when already logged in."""
    response = client.get('/signup')
    assert response.status_code == 302
    assert '/profile' in response.headers['Location']

if __name__ == "__main__":
    # This allows running the test directly with python
    pytest.main(["-v", __file__])