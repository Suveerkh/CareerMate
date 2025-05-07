import requests
import socket

def check_internet_connection():
    """
    Check if there is an active internet connection.
    Returns True if connected, False otherwise.
    """
    try:
        # Try to connect to Google's DNS server
        socket.create_connection(("8.8.8.8", 53), timeout=3)
        return True
    except OSError:
        pass
    
    try:
        # Try to make a request to Google
        requests.get("https://www.google.com", timeout=3)
        return True
    except requests.RequestException:
        return False

def is_supabase_reachable(supabase_url):
    """
    Check if the Supabase server is reachable.
    Returns True if reachable, False otherwise.
    """
    if not supabase_url:
        return False
        
    try:
        # Try to make a request to the Supabase URL
        response = requests.get(supabase_url, timeout=5)
        return response.status_code < 500  # Any response that's not a server error
    except requests.RequestException:
        return False