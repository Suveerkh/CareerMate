# google_auth.py
# Direct Google OAuth implementation for CareerMate

import os
import json
import secrets
import datetime
import uuid
from flask import url_for, redirect, session, flash, request
from google.oauth2 import id_token
from google_auth_oauthlib.flow import Flow
from google.auth.transport import requests as google_requests

import pathlib

def get_base_url():
    """Get the base URL for the application (development or production)"""
    if os.getenv('RENDER'):
        # Running on Render
        return f"https://{os.getenv('RENDER_EXTERNAL_HOSTNAME', 'your-app-name.onrender.com')}"
    else:
        # Running locally
        return "http://localhost:5001"

def create_client_secrets_file():
    """Create a client_secrets.json file for Google OAuth if it doesn't exist"""
    client_secrets_path = os.path.join(os.path.dirname(__file__), "client_secrets.json")
    
    # Only create if it doesn't exist
    if not os.path.exists(client_secrets_path):
        client_id = os.getenv("GOOGLE_CLIENT_ID")
        client_secret = os.getenv("GOOGLE_CLIENT_SECRET")
        
        if not client_id or not client_secret:
            print("Warning: Google OAuth credentials not found in environment variables")
            return None
            
        client_config = {
            "web": {
                "client_id": client_id,
                "project_id": "careermate",
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                "client_secret": client_secret,
                "redirect_uris": [
                    "http://localhost:5001/auth/google/callback",
                    "http://127.0.0.1:5001/auth/google/callback",
                    f"{get_base_url()}/auth/google/callback",
                    f"{get_base_url()}/supabase/callback"
                ]
            }
        }
        
        with open(client_secrets_path, "w") as f:
            json.dump(client_config, f)
            
        print(f"Created client_secrets.json at {client_secrets_path}")
    
    return client_secrets_path

def get_google_flow(redirect_uri):
    """Create and configure a Google OAuth flow"""
    client_secrets_path = create_client_secrets_file()
    if not client_secrets_path:
        return None
        
    flow = Flow.from_client_secrets_file(
        client_secrets_file=client_secrets_path,
        scopes=[
            "https://www.googleapis.com/auth/userinfo.profile",
            "https://www.googleapis.com/auth/userinfo.email",
            "openid"
        ],
        redirect_uri=redirect_uri
    )
    
    return flow

def start_google_login(app):
    """
    Initiates the Google OAuth login flow directly (not through Supabase)
    """
    try:
        # Generate a state token to prevent CSRF
        state = secrets.token_urlsafe(16)
        session["google_oauth_state"] = state
        
        # Get the OAuth flow with the exact redirect URI that's registered in Google Cloud Console
        # Use the absolute URL with the correct host
        redirect_uri = f"{get_base_url()}/auth/google/callback"
        flow = get_google_flow(redirect_uri)
        if not flow:
            flash("Google OAuth is not properly configured", "error")
            return redirect(url_for("login"))
            
        # Generate the authorization URL
        auth_url, _ = flow.authorization_url(
            access_type="offline",
            include_granted_scopes="true",
            state=state,
            prompt="select_account"
        )
        
        print(f"Google OAuth URL: {auth_url}")
        
        # Redirect to Google's OAuth page
        return redirect(auth_url)
    except Exception as e:
        print(f"Error initiating Google login: {str(e)}")
        import traceback
        traceback.print_exc()
        flash(f"Error initiating Google login: {str(e)}", "error")
        return redirect(url_for("login"))

def handle_google_callback(app):
    """
    Handles the callback from Google OAuth and stores user in Supabase
    """
    try:
        # Debug: Print all query parameters
        print(f"Google callback received with parameters: {request.args}")
        
        # Check for errors
        if "error" in request.args:
            error = request.args.get("error")
            flash(f"Authentication failed: {error}", "error")
            return redirect(url_for("login"))
            
        # Verify state token to prevent CSRF
        state = request.args.get("state")
        stored_state = session.pop("google_oauth_state", None)
        
        if not state or state != stored_state:
            flash("Authentication failed: Invalid state parameter", "error")
            return redirect(url_for("login"))
            
        # Get the authorization code
        code = request.args.get("code")
        if not code:
            flash("Authentication failed: No authorization code received", "error")
            return redirect(url_for("login"))
            
        # Exchange the code for credentials
        # Use the exact same redirect URI as in the authorization request
        redirect_uri = f"{get_base_url()}/auth/google/callback"
        flow = get_google_flow(redirect_uri)
        flow.fetch_token(code=code)
        
        # Get the ID token
        credentials = flow.credentials
        id_info = id_token.verify_oauth2_token(
            credentials.id_token, 
            google_requests.Request(),
            os.getenv("GOOGLE_CLIENT_ID")
        )
        
        print(f"Google user info: {id_info}")
        
        # Extract user information
        email = id_info.get("email")
        if not email:
            flash("Failed to retrieve email from Google", "error")
            return redirect(url_for("login"))
            
        # Initialize Supabase
        if hasattr(app, 'init_supabase'):
            app.init_supabase()
        else:
            # If init_supabase is a global function
            from app import init_supabase
            init_supabase()
        
        # Check if user exists in our database
        existing_user = app.supabase.table("Users").select("*").filter("email", "eq", email).execute()
        
        if existing_user.data and len(existing_user.data) > 0:
            # User exists, update login information
            user_id = existing_user.data[0]["id"]
            username = existing_user.data[0]["username"]
            
            # Update last login time
            app.supabase.table("Users").update({
                "last_login": str(datetime.datetime.now())
            }).filter("id", "eq", user_id).execute()
            
            # Set session variables
            session['user_id'] = user_id
            session['username'] = username
            session['email'] = email
            
            flash("Welcome back! You've been logged in with Google.", "success")
        else:
            # User doesn't exist, create a new account
            user_id = str(uuid.uuid4())
            
            # Get name from Google profile
            given_name = id_info.get("given_name", "")
            family_name = id_info.get("family_name", "")
            full_name = f"{given_name} {family_name}".strip()
            
            # If no name is available, use email as username
            username = full_name if full_name else email.split('@')[0]
            
            # Insert new user
            new_user = {
                "id": user_id,
                "username": username,
                "email": email,
                "is_verified": True,  # Google accounts are pre-verified
                "created_at": str(datetime.datetime.now()),
                "last_login": str(datetime.datetime.now()),
                "auth_provider": "google"
            }
            
            app.supabase.table("Users").insert(new_user).execute()
            
            # Set session variables
            session['user_id'] = user_id
            session['username'] = username
            session['email'] = email
            
            flash("Account created successfully with Google!", "success")
        
        return redirect(url_for('profile'))
        
    except Exception as e:
        print(f"Error during Google authentication: {str(e)}")
        import traceback
        traceback.print_exc()
        flash(f"Error during Google authentication: {str(e)}", "error")
        return redirect(url_for('login'))