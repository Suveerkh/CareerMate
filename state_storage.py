"""
A simple file-based storage for OAuth state tokens
"""

import os
import json
import time
from pathlib import Path

# Directory to store state tokens
STATE_DIR = os.path.join(os.path.dirname(__file__), "oauth_states")

# Ensure the directory exists
os.makedirs(STATE_DIR, exist_ok=True)

def save_state(state_token, expiry_seconds=300):
    """
    Save a state token with an expiry time
    
    Args:
        state_token: The state token to save
        expiry_seconds: Number of seconds until the token expires (default: 5 minutes)
    """
    print(f"Saving state token: {state_token}")
    
    expiry_time = time.time() + expiry_seconds
    
    state_data = {
        "token": state_token,
        "expires_at": expiry_time
    }
    
    # Save to a file named after the state token
    file_path = os.path.join(STATE_DIR, f"{state_token}.json")
    print(f"Saving state token to file: {file_path}")
    
    try:
        with open(file_path, 'w') as f:
            json.dump(state_data, f)
        
        # Verify the file was created
        if os.path.exists(file_path):
            print(f"State token file created successfully: {file_path}")
        else:
            print(f"Failed to create state token file: {file_path}")
    except Exception as e:
        print(f"Error saving state token: {str(e)}")
    
    return state_token

def verify_state(state_token):
    """
    Verify if a state token exists and is valid
    
    Args:
        state_token: The state token to verify
        
    Returns:
        bool: True if the token is valid, False otherwise
    """
    if not state_token:
        print("State token is empty")
        return False
    
    file_path = os.path.join(STATE_DIR, f"{state_token}.json")
    print(f"Looking for state token file: {file_path}")
    
    # Check if the file exists
    if not os.path.exists(file_path):
        print(f"State token file not found: {file_path}")
        # List all files in the directory for debugging
        print(f"Files in {STATE_DIR}: {os.listdir(STATE_DIR)}")
        return False
    
    try:
        with open(file_path, 'r') as f:
            state_data = json.load(f)
        
        print(f"State token data: {state_data}")
        
        # Check if the token has expired
        if time.time() > state_data.get("expires_at", 0):
            print(f"State token has expired: {state_token}")
            # Remove the expired token file
            os.remove(file_path)
            return False
        
        print(f"State token is valid: {state_token}")
        # Token is valid, remove it to prevent reuse
        os.remove(file_path)
        return True
    except Exception as e:
        print(f"Error verifying state token: {str(e)}")
        return False

def cleanup_expired_states():
    """
    Clean up expired state tokens
    """
    current_time = time.time()
    
    for file_name in os.listdir(STATE_DIR):
        if not file_name.endswith('.json'):
            continue
        
        file_path = os.path.join(STATE_DIR, file_name)
        
        try:
            with open(file_path, 'r') as f:
                state_data = json.load(f)
            
            if current_time > state_data.get("expires_at", 0):
                os.remove(file_path)
        except Exception as e:
            print(f"Error cleaning up state token {file_name}: {str(e)}")