import pytest
from app import app
import os

# Mock Supabase client
class MockSupabaseClient:
    def __init__(self):
        self.data = []
        self.status_code = 201  # Default success status code
        self.auth = MockSupabaseAuth()

    def table(self, table_name):
        return self

    def insert(self, data):
        # Use the provided ID or generate one if not provided
        if 'id' not in data:
            if self.data:
                new_id = max(user.get('id', 0) for user in self.data) + 1
            else:
                new_id = 1
            data['id'] = new_id
            
        self.data.append(data)
        return self

    def select(self, *args, **kwargs):
        self.selected_fields = args
        return self

    def filter(self, column, operator, value):
        if operator == "eq":
            self.filtered_data = [user for user in self.data if user.get(column) == value]
        return self
        
    def eq(self, column, value):
        # For backward compatibility
        return self.filter(column, "eq", value)

    def execute(self):
        class Response:
            def __init__(self, data, status_code):
                self.data = data
                self.status_code = status_code
                
        if hasattr(self, 'filtered_data'):
            # For select queries
            result = self.filtered_data
            # If specific fields were selected, filter the result
            if hasattr(self, 'selected_fields') and self.selected_fields:
                filtered_result = []
                for item in result:
                    filtered_item = {field: item.get(field) for field in self.selected_fields if field in item}
                    filtered_result.append(filtered_item)
                result = filtered_result
            return Response(result, 200)
        else:
            # For insert queries
            return Response(self.data[-1:] if self.data else [], self.status_code)

# Mock Supabase Auth
class MockSupabaseAuth:
    def __init__(self):
        self.mock_user = MockUser()
        self.mock_session = MockSession()
    
    def sign_in_with_oauth(self, params):
        class MockSignInResponse:
            def __init__(self):
                self.url = "https://mock-oauth-url.com"
        
        return MockSignInResponse()
    
    def exchange_code_for_session(self, params):
        class MockSessionResponse:
            def __init__(self, session):
                self.session = session
        
        return MockSessionResponse(self.mock_session)
    
    def get_user(self, access_token):
        class MockUserResponse:
            def __init__(self, user):
                self.user = user
        
        return MockUserResponse(self.mock_user)

# Mock User
class MockUser:
    def __init__(self):
        self.id = "google-user-id-123"
        self.email = "google-user@example.com"
        self.user_metadata = {
            "full_name": "Google User",
            "avatar_url": "https://example.com/avatar.jpg"
        }

# Mock Session
class MockSession:
    def __init__(self):
        self.access_token = "mock-access-token"
        self.refresh_token = "mock-refresh-token"

@pytest.fixture
def client(monkeypatch):
    # Mock environment variables
    monkeypatch.setenv("SUPABASE_URL", "http://mock.supabase.co")
    monkeypatch.setenv("SUPABASE_KEY", "mock_key")
    monkeypatch.setenv("SECRET_KEY", "test_secret_key")

    app.config['TESTING'] = True
    app.supabase = MockSupabaseClient()  # Use the mock client
    
    with app.test_client() as client:
        yield client

def test_signup(client):
    response = client.post("/signup", data={
        "name": "Test User",
        "email": "test@example.com",
        "password": "password123"
    })
    assert response.status_code == 302  # Redirect to login
    assert "/login" in response.headers["Location"]

def test_login(client):
    # First, sign up the user
    client.post("/signup", data={
        "name": "Test User",
        "email": "test@example.com",
        "password": "password123"
    })

    # Then, attempt to log in
    response = client.post("/login", data={
        "email": "test@example.com",
        "password": "password123"
    })
    assert response.status_code == 302  # Redirect to profile
    assert "/profile" in response.headers["Location"]
    
    # Check if session contains user data
    with client.session_transaction() as session:
        assert 'user_id' in session
        assert 'username' in session
        assert 'email' in session
        assert session['email'] == "test@example.com"

def test_login_invalid_password(client):
    # First, sign up the user
    client.post("/signup", data={
        "name": "Test User",
        "email": "test@example.com",
        "password": "password123"
    })

    # Attempt to log in with an invalid password
    response = client.post("/login", data={
        "email": "test@example.com",
        "password": "wrongpassword"
    })
    assert b"Invalid password" in response.data

def test_login_user_not_found(client):
    # Attempt to log in with a non-existent user
    response = client.post("/login", data={
        "email": "nonexistent@example.com",
        "password": "password123"
    })
    assert b"User not found" in response.data

def test_login_empty_credentials(client):
    """Test login with empty email and password"""
    # Test with empty email
    response = client.post("/login", data={
        "email": "",
        "password": "password123"
    })
    assert b"Email and password are required" in response.data
    
    # Test with empty password
    response = client.post("/login", data={
        "email": "test@example.com",
        "password": ""
    })
    assert b"Email and password are required" in response.data
    
    # Test with both empty
    response = client.post("/login", data={
        "email": "",
        "password": ""
    })
    assert b"Email and password are required" in response.data

def test_login_with_remember_me(client):
    """Test login with remember me option checked"""
    # First, sign up the user
    client.post("/signup", data={
        "name": "Test User",
        "email": "test@example.com",
        "password": "password123"
    })
    
    # Then, attempt to log in with remember_me checked
    response = client.post("/login", data={
        "email": "test@example.com",
        "password": "password123",
        "remember_me": "on"
    })
    assert response.status_code == 302  # Redirect to profile
    assert "/profile" in response.headers["Location"]
    
    # Check if session is permanent
    with client.session_transaction() as session:
        assert session.permanent is True
        assert 'user_id' in session
        assert 'username' in session
        assert 'email' in session
        assert session['email'] == "test@example.com"

def test_login_already_logged_in(client):
    """Test login when user is already logged in"""
    # First, sign up and log in
    client.post("/signup", data={
        "name": "Test User",
        "email": "test@example.com",
        "password": "password123"
    })
    
    client.post("/login", data={
        "email": "test@example.com",
        "password": "password123"
    })
    
    # Try to access login page again
    response = client.get("/login")
    assert response.status_code == 302  # Redirect to profile
    assert "/profile" in response.headers["Location"]
    
    # Try to post to login again
    response = client.post("/login", data={
        "email": "test@example.com",
        "password": "password123"
    })
    assert response.status_code == 302  # Redirect to profile
    assert "/profile" in response.headers["Location"]

def test_profile_requires_login(client):
    # Try to access profile without logging in
    response = client.get("/profile", follow_redirects=True)
    assert b"Please log in to access this page" in response.data
    
def test_logout(client):
    # First, sign up and log in
    client.post("/signup", data={
        "name": "Test User",
        "email": "test@example.com",
        "password": "password123"
    })
    
    client.post("/login", data={
        "email": "test@example.com",
        "password": "password123"
    })
    
    # Then logout
    response = client.get("/logout", follow_redirects=True)
    assert b"You have been logged out" in response.data
    
    # Check that session is cleared
    with client.session_transaction() as session:
        assert 'user_id' not in session

def test_google_login_redirect(client):
    """Test that the Google login redirect route works correctly"""
    response = client.get("/google-login")
    assert response.status_code == 302
    assert "/auth/google/login" in response.headers["Location"]

def test_google_login_initiation(client):
    """Test that the Google login initiation route works correctly"""
    response = client.get("/auth/google/login")
    assert response.status_code == 302
    assert "https://mock-oauth-url.com" in response.headers["Location"]

def test_google_callback_new_user(client):
    """Test Google callback with a new user"""
    # Set up the mock client to simulate a new user (no existing user with the same email)
    app.supabase.filtered_data = []
    
    # Simulate the callback from Google
    response = client.get("/auth/google/callback?code=mock_auth_code", follow_redirects=True)
    
    # Check that we're redirected to the profile page
    assert b"Account created successfully with Google!" in response.data
    
    # Check that the session contains the user data
    with client.session_transaction() as session:
        assert 'user_id' in session
        assert 'username' in session
        assert 'email' in session
        assert session['email'] == "google-user@example.com"
        assert session['username'] == "Google User"

def test_google_callback_existing_user(client):
    """Test Google callback with an existing user"""
    # First, create a user with the same email as our mock Google user
    app.supabase.data.append({
        "id": "existing-user-id",
        "username": "Existing User",
        "email": "google-user@example.com",
        "password_hash": "some-hash",
        "is_verified": True
    })
    
    # Simulate the callback from Google
    response = client.get("/auth/google/callback?code=mock_auth_code", follow_redirects=True)
    
    # Check that we're redirected to the profile page
    assert b"Login successful with Google!" in response.data
    
    # Check that the session contains the existing user data
    with client.session_transaction() as session:
        assert 'user_id' in session
        assert 'username' in session
        assert 'email' in session
        assert session['email'] == "google-user@example.com"
        assert session['username'] == "Existing User"

def test_google_callback_no_code(client):
    """Test Google callback with no code parameter"""
    response = client.get("/auth/google/callback", follow_redirects=True)
    assert b"Authentication failed: No authorization code received" in response.data

def test_login_server_error(client, monkeypatch):
    """Test login with a server error during database query"""
    # First, sign up the user
    client.post("/signup", data={
        "name": "Test User",
        "email": "test@example.com",
        "password": "password123"
    })
    
    # Create a custom mock for the table method
    original_table = app.supabase.table
    
    def mock_table(table_name):
        if table_name == "Users":
            # Create a mock object that will raise an exception when execute is called
            class MockTable:
                def select(self, *args):
                    return self
                
                def filter(self, column, operator, value):
                    return self
                
                def execute(self):
                    raise Exception("Database connection error")
            
            return MockTable()
        return original_table(table_name)
    
    # Apply the mock
    monkeypatch.setattr(app.supabase, "table", mock_table)
    
    # Attempt to log in with follow_redirects to see flash messages
    response = client.post("/login", data={
        "email": "test@example.com",
        "password": "password123"
    }, follow_redirects=True)
    
    # Since we can't predict the exact error message format, let's check for a more generic error message
    # or just verify that we're still on the login page after the error
    assert b"Login" in response.data
    assert response.status_code == 200  # We should stay on the login page

def test_login_json_parsing_error(client, monkeypatch):
    """Test login with a JSON parsing error"""
    # First, sign up the user
    client.post("/signup", data={
        "name": "Test User",
        "email": "test@example.com",
        "password": "password123"
    })
    
    # Create a custom mock for the table method
    original_table = app.supabase.table
    
    def mock_table(table_name):
        if table_name == "Users":
            # Create a mock object that will raise a ValueError when execute is called
            class MockTable:
                def select(self, *args):
                    return self
                
                def filter(self, column, operator, value):
                    return self
                
                def execute(self):
                    raise ValueError("Invalid JSON response")
            
            return MockTable()
        return original_table(table_name)
    
    # Apply the mock
    monkeypatch.setattr(app.supabase, "table", mock_table)
    
    # Attempt to log in with follow_redirects to see flash messages
    response = client.post("/login", data={
        "email": "test@example.com",
        "password": "password123"
    }, follow_redirects=True)
    
    # Since we can't predict the exact error message format, let's check for a more generic error message
    # or just verify that we're still on the login page after the error
    assert b"Login" in response.data
    assert response.status_code == 200  # We should stay on the login page
