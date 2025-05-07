import pytest
import sys
import os
import json
from unittest.mock import patch, MagicMock

# Add the parent directory to the path so we can import the app module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the app but patch Flask-Session to avoid serialization issues
with patch('flask_session.Session'):
    from app import app

# Create mock data for testing
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
        self.auth = MockAuth()
        
    def table(self, table_name):
        return self
        
    def select(self, *args):
        return self
        
    def filter(self, column, operator, value):
        return self
        
    def order(self, column, desc=False):
        return self
        
    def limit(self, count):
        return self
        
    def execute(self):
        class Response:
            def __init__(self):
                self.data = []
                self.status_code = 200
        return Response()

class MockAuth:
    def __init__(self):
        pass
        
    def sign_up(self, email, password):
        return {"user": {"id": "test-user-id"}, "session": None}
        
    def sign_in_with_password(self, credentials):
        return {"user": {"id": "test-user-id"}, "session": None}

@pytest.fixture
def client():
    # Configure app for testing
    app.config['TESTING'] = True
    app.config['SECRET_KEY'] = 'test_key'
    app.config['WTF_CSRF_ENABLED'] = False  # Disable CSRF for testing
    
    # Disable Flask-Session
    app.config['SESSION_TYPE'] = None
    
    # Mock the Supabase client
    app.supabase = MockSupabaseClient()
    
    # Mock any global variables or functions
    if hasattr(app, 'CAREER_CATEGORIES'):
        app._original_categories = app.CAREER_CATEGORIES
        app.CAREER_CATEGORIES = MOCK_CAREER_CATEGORIES
    
    # Create a test client
    with app.test_client() as client:
        # Set up a test session
        with app.app_context():
            with client.session_transaction() as session:
                session['user_id'] = 'test-user-id'
                session['username'] = 'Test User'
                session['email'] = 'test@example.com'
        yield client
    
    # Restore original values if needed
    if hasattr(app, '_original_categories'):
        app.CAREER_CATEGORIES = app._original_categories

def test_home_route(client):
    """Test that the home page loads successfully."""
    response = client.get('/')
    # Home page might redirect to login or load directly
    assert response.status_code in [200, 302]

def test_login_route(client):
    """Test that the login page loads successfully."""
    # Since we're already logged in via the session, this should redirect
    response = client.get('/login')
    assert response.status_code == 302  # Redirect

def test_signup_route(client):
    """Test that the signup page loads successfully."""
    # Clear the session first to test signup page
    with client.session_transaction() as session:
        session.clear()
    
    response = client.get('/signup')
    assert response.status_code == 200  # Should load the signup page

def test_logout_route(client):
    """Test that the logout route works."""
    response = client.get('/logout', follow_redirects=True)
    assert response.status_code == 200

def test_careers_route(client):
    """Test that the careers page loads successfully."""
    response = client.get('/careers')
    assert response.status_code in [200, 302]  # May load or redirect

if __name__ == "__main__":
    # This allows running the test directly with python
    pytest.main(["-v", __file__])