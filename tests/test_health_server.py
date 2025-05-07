import pytest
import sys
import os
import json
from datetime import datetime

# Add the parent directory to the path so we can import the health_server module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from health_server import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_health_check(client):
    """Test that the health check endpoint returns the expected response."""
    response = client.get('/health')
    
    # Check status code
    assert response.status_code == 200
    
    # Parse the JSON response
    data = json.loads(response.data)
    
    # Check that the response contains the expected fields
    assert 'status' in data
    assert 'message' in data
    assert 'timestamp' in data
    
    # Check the values
    assert data['status'] == 'ok'
    assert data['message'] == 'Server is running'
    
    # Verify the timestamp is a valid ISO format
    try:
        datetime.fromisoformat(data['timestamp'])
    except ValueError:
        pytest.fail("Timestamp is not in valid ISO format")
    
    print("Health check test passed successfully!")

if __name__ == "__main__":
    # This allows running the test directly with python
    pytest.main(["-v", __file__])