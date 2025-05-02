# simple_google_auth.py
# A simplified Google OAuth implementation for CareerMate

import os
import json
import secrets
import datetime
import uuid
import requests
from flask import url_for, redirect, session, flash, request, jsonify
from urllib.parse import urlencode
from state_storage import save_state, verify_state

def get_google_auth_url():
    """Generate a Google OAuth URL"""
    client_id = os.getenv("GOOGLE_CLIENT_ID")
    if not client_id:
        raise ValueError("GOOGLE_CLIENT_ID environment variable is not set")
    
    # Generate a state token to prevent CSRF
    state = secrets.token_urlsafe(16)
    # Store the state token in our file-based storage instead of the session
    save_state(state)
    
    # Define the OAuth parameters
    params = {
        "client_id": client_id,
        "redirect_uri": "http://localhost:5001/auth/google/callback",
        "response_type": "code",
        "scope": "email profile openid",
        "state": state,
        "access_type": "offline",
        "prompt": "select_account"
    }
    
    # Build the authorization URL
    auth_url = "https://accounts.google.com/o/oauth2/auth?" + urlencode(params)
    
    return auth_url

def start_google_login():
    """Initiates the Google OAuth login flow"""
    try:
        # Make sure session is permanent to persist across requests
        session.permanent = True
        
        auth_url = get_google_auth_url()
        print(f"Google OAuth URL: {auth_url}")
        
        print(f"Session state token: {session.get('google_oauth_state')}")
        
        # Make sure the session is saved
        session.modified = True
        
        return redirect(auth_url)
    except Exception as e:
        print(f"Error initiating Google login: {str(e)}")
        import traceback
        traceback.print_exc()
        flash(f"Error initiating Google login: {str(e)}", "error")
        return redirect(url_for("login"))

def handle_google_callback(app):
    """Handles the callback from Google OAuth"""
    try:
        # Check for errors
        if "error" in request.args:
            error = request.args.get("error")
            flash(f"Authentication failed: {error}", "error")
            return redirect(url_for("login"))
        
        # Get the authorization code
        code = request.args.get("code")
        if not code:
            flash("Authentication failed: No authorization code received", "error")
            return redirect(url_for("login"))
        
        # Verify state token to prevent CSRF
        state = request.args.get("state")
        
        print(f"Callback received state: {state}")
        
        # Verify the state token using our file-based storage
        if not state or not verify_state(state):
            flash("Authentication failed: Invalid state parameter", "error")
            return redirect(url_for("login"))
        
        # Exchange the code for tokens
        client_id = os.getenv("GOOGLE_CLIENT_ID")
        client_secret = os.getenv("GOOGLE_CLIENT_SECRET")
        
        token_url = "https://oauth2.googleapis.com/token"
        token_data = {
            "code": code,
            "client_id": client_id,
            "client_secret": client_secret,
            "redirect_uri": "http://localhost:5001/auth/google/callback",
            "grant_type": "authorization_code"
        }
        
        token_response = requests.post(token_url, data=token_data)
        token_json = token_response.json()
        
        if "error" in token_json:
            flash(f"Authentication failed: {token_json['error']}", "error")
            return redirect(url_for("login"))
        
        # Get the user info using the access token
        access_token = token_json["access_token"]
        userinfo_url = "https://www.googleapis.com/oauth2/v3/userinfo"
        userinfo_response = requests.get(
            userinfo_url,
            headers={"Authorization": f"Bearer {access_token}"}
        )
        
        userinfo = userinfo_response.json()
        
        # Extract user information
        email = userinfo.get("email")
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
            
            # Check if this is a verification from profile
            if 'verification_user_id' in session:
                verification_user_id = session.pop('verification_user_id')
                
                # Update the user's auth_provider to "google"
                app.supabase.table("Users").update({
                        "last_login": str(datetime.datetime.now()),
                    "auth_provider": "google"
                }).filter("id", "eq", verification_user_id).execute()
                
                flash("Welcome back! You've been logged in with Google.", "success")
                
                flash("Account verified successfully with Google!", "success")
            else:
                # Just a regular login, update last login time
                app.supabase.table("Users").update({
                    "last_login": str(datetime.datetime.now())
                    }).filter("id", "eq", user_id).execute()
                
                flash("Welcome back! You've been logged in with Google.", "success")
            
            # Set session variables
            session['user_id'] = user_id
            session['username'] = username
            session['email'] = email
        else:
            # User doesn't exist, create a new account
            user_id = str(uuid.uuid4())
            
            # Get name from Google profile
            given_name = userinfo.get("given_name", "")
            family_name = userinfo.get("family_name", "")
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