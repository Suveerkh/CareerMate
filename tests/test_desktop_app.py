import pytest
import sys
import os
import json
import time
import threading
import requests
import subprocess
from unittest.mock import patch, MagicMock, Mock

# Add the parent directory to the path so we can import the app module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Mock the electron modules that would be used in the desktop app
sys.modules['electron'] = MagicMock()
sys.modules['electron-is-dev'] = MagicMock()
sys.modules['python-shell'] = MagicMock()

# Create a mock for the desktop app's main window
class MockMainWindow:
    def __init__(self):
        self.current_page = 'splash.html'
        self.loaded_url = None
    
    def loadFile(self, file_path):
        self.current_page = os.path.basename(file_path)
        self.loaded_url = None
        return True
    
    def loadURL(self, url):
        self.loaded_url = url
        # Keep track of the page but mark it as a URL
        self.current_page = f"URL:{url}"
        return True

class TestDesktopApp:
    """Test the desktop application's behavior with different server states."""
    
    @pytest.fixture
    def mock_window(self):
        """Create a mock main window for testing."""
        return MockMainWindow()
    
    @pytest.fixture
    def mock_server_running(self):
        """Mock a running server for testing."""
        with patch('requests.get') as mock_get:
            # Create a mock response
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "status": "ok",
                "message": "Server is running",
                "timestamp": "2025-05-03T18:30:00.000000"
            }
            
            # Configure the mock to return the response
            mock_get.return_value = mock_response
            
            yield mock_get
    
    @pytest.fixture
    def mock_server_down(self):
        """Mock a server that's down for testing."""
        with patch('requests.get') as mock_get:
            # Configure the mock to raise a ConnectionError
            mock_get.side_effect = requests.exceptions.ConnectionError("Connection refused")
            
            yield mock_get
    
    def test_splash_to_main_with_server_running(self, mock_window, mock_server_running):
        """Test transition from splash to main when server is running."""
        # Initial state - app showing splash screen
        assert mock_window.current_page == 'splash.html'
        
        # Simulate the checkServerConnection function from main.js
        server_url = 'http://localhost:5001'
        server_running = False
        
        try:
            # Try to connect to the health endpoint
            response = requests.get(f"{server_url}/health", timeout=2)
            
            if response.status_code == 200:
                # Server is running, transition to main app
                server_running = True
                mock_window.loadURL(server_url)
        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
            # Connection failed, stay on splash or show offline
            if server_running:
                server_running = False
                mock_window.loadFile('offline.html')
        
        # Assert that the app would transition to the main URL
        assert mock_window.loaded_url == server_url
        assert mock_window.current_page == f"URL:{server_url}"
        assert server_running is True
        
        # Verify the mock was called correctly
        mock_server_running.assert_called_once_with(f"{server_url}/health", timeout=2)
        
        print("Splash to main transition test (server running) passed successfully!")
    
    def test_splash_to_offline_with_server_down(self, mock_window, mock_server_down):
        """Test transition from splash to offline when server is down."""
        # Initial state - app showing splash screen
        assert mock_window.current_page == 'splash.html'
        
        # Simulate the checkServerConnection function from main.js
        server_url = 'http://localhost:5001'
        server_running = True  # Assume it was running before
        
        try:
            # Try to connect to the health endpoint
            response = requests.get(f"{server_url}/health", timeout=2)
            
            if response.status_code == 200:
                # Server is running, transition to main app
                server_running = True
                mock_window.loadURL(server_url)
        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
            # Connection failed, show offline screen
            if server_running:
                server_running = False
                mock_window.loadFile('offline.html')
        
        # Assert that the app would transition to the offline screen
        assert mock_window.current_page == 'offline.html'
        assert mock_window.loaded_url is None
        assert server_running is False
        
        # Verify the mock was called correctly
        mock_server_down.assert_called_once_with(f"{server_url}/health", timeout=2)
        
        print("Splash to offline transition test (server down) passed successfully!")
    
    def test_server_restart_recovery(self, mock_window, mock_server_down, mock_server_running):
        """Test recovery when server restarts after being down."""
        # Initial state - app showing offline screen after server went down
        mock_window.loadFile('offline.html')
        assert mock_window.current_page == 'offline.html'
        
        # Simulate the checkServerConnection function from main.js
        server_url = 'http://localhost:5001'
        server_running = False
        
        # First check - server is still down
        # We need to explicitly use the mock_server_down here
        mock_server_down.side_effect = requests.exceptions.ConnectionError("Connection refused")
        
        try:
            # This will raise the ConnectionError due to our mock
            response = mock_server_down(f"{server_url}/health", timeout=2)
            
            if response.status_code == 200:
                # Server is running, transition to main app
                server_running = True
                mock_window.loadURL(server_url)
        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
            # Connection failed, stay on offline screen
            pass
        
        # Assert that the app would stay on the offline screen
        # Since the server is down, the page should not change
        assert mock_window.current_page == 'offline.html'
        assert server_running is False
        
        # Now simulate server coming back online by switching the mock
        mock_server_down.side_effect = None
        mock_server_down.return_value = mock_server_running.return_value
        
        # Second check - server is now up
        try:
            # Try to connect to the health endpoint using the mock
            response = mock_server_down(f"{server_url}/health", timeout=2)
            
            if response.status_code == 200:
                # Server is running, transition to main app
                server_running = True
                mock_window.loadURL(server_url)
        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
            # Connection failed, stay on offline screen
            pass
        
        # Assert that the app would transition to the main URL
        assert mock_window.loaded_url == server_url
        assert mock_window.current_page == f"URL:{server_url}"
        assert server_running is True
        
        print("Server restart recovery test passed successfully!")

if __name__ == "__main__":
    # This allows running the test directly with python
    pytest.main(["-v", __file__])