import pytest
import sys
import os
import json
import time
import threading
import requests
import subprocess
from unittest.mock import patch, MagicMock

# Add the parent directory to the path so we can import the app module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the app but patch Flask-Session to avoid serialization issues
with patch('flask_session.Session'):
    from app import app

class TestDesktopIntegration:
    """Test the integration between the desktop application and the Flask server."""
    
    @pytest.fixture
    def server_thread(self):
        """Start the Flask server in a separate thread for testing."""
        def run_server():
            app.config['TESTING'] = True
            app.config['SESSION_TYPE'] = None  # Disable Flask-Session for testing
            app.run(host='127.0.0.1', port=5001, debug=False, use_reloader=False)
        
        # Start the server in a separate thread
        thread = threading.Thread(target=run_server)
        thread.daemon = True
        thread.start()
        
        # Wait for the server to start
        time.sleep(2)
        
        yield
        
        # No need to stop the thread as it's a daemon thread
    
    def test_health_endpoint(self, server_thread):
        """Test that the health endpoint returns the expected response."""
        try:
            response = requests.get('http://127.0.0.1:5001/health', timeout=5)
            
            # Check status code
            assert response.status_code == 200
            
            # Parse the JSON response
            data = response.json()
            
            # Check that the response contains the expected fields
            assert 'status' in data
            assert 'message' in data
            assert 'timestamp' in data
            
            # Check the values
            assert data['status'] == 'ok'
            assert data['message'] == 'Server is running'
            
            print("Health endpoint test passed successfully!")
        except requests.exceptions.ConnectionError:
            pytest.fail("Could not connect to the server. Make sure it's running on port 5001.")
    
    def test_desktop_server_connection(self, server_thread):
        """
        Test that the desktop application can connect to the server.
        
        This test simulates what the desktop app does when checking server connection.
        """
        try:
            # This is similar to what the desktop app does in checkServerConnection()
            response = requests.get('http://127.0.0.1:5001/health', timeout=2)
            
            assert response.status_code == 200
            data = response.json()
            assert data['status'] == 'ok'
            
            # If we get here, the desktop app would transition from splash screen to main app
            print("Desktop server connection test passed successfully!")
        except requests.exceptions.ConnectionError:
            pytest.fail("Desktop app would show offline screen: Could not connect to the server.")
        except requests.exceptions.Timeout:
            pytest.fail("Desktop app would show offline screen: Connection to server timed out.")
    
    def test_splash_to_main_transition(self, server_thread):
        """
        Test the transition from splash screen to main application.
        
        This test simulates the logic in the desktop app's checkServerConnection function.
        """
        # Initial state - app would be showing splash screen
        server_running = False
        
        try:
            # Try to connect to the health endpoint (what the desktop app does)
            response = requests.get('http://127.0.0.1:5001/health', timeout=2)
            
            if response.status_code == 200:
                # Server is running, app would transition to main screen
                server_running = True
        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
            # Connection failed, app would stay on splash or show offline screen
            server_running = False
        
        # Assert that the server is running and app would transition
        assert server_running, "Application would not transition from splash screen to main application"
        print("Splash to main transition test passed successfully!")

if __name__ == "__main__":
    # This allows running the test directly with python
    pytest.main(["-v", __file__])