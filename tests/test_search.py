import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app import app

# Set up testing configuration
app.config['TESTING'] = True
app.config['SECRET_KEY'] = 'test_key'

# Create a test client
client = app.test_client()

# Create a test session with a logged-in user
with client.session_transaction() as session:
    session['user_id'] = 'test_user'
    session['username'] = 'Test User'
    session['email'] = 'test@example.com'

# Test the search functionality
response = client.get('/search?q=developer')
print('Search response status:', response.status_code)

if response.status_code == 200:
    response_text = response.data.decode()
    print('Search response contains "Web Developer":', 'Web Developer' in response_text)
    print('Search response contains search results section:', 'Search Results for' in response_text)
else:
    print('Search failed with status code:', response.status_code)
    print('Response headers:', response.headers)