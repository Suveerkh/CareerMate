# github_auth.py
# GitHub OAuth implementation for CareerMate

import os
import json
import secrets
import datetime
import uuid
import requests
from flask import url_for, redirect, session, flash, request, jsonify
from urllib.parse import urlencode
from state_storage import save_state, verify_state

def get_github_auth_url():
    """Generate a GitHub OAuth URL"""
    client_id = os.getenv("GITHUB_CLIENT_ID", "Ov23liWQZyjkDqbYLy8S")  # Use default value if env var not set
    if not client_id:
        raise ValueError("GITHUB_CLIENT_ID environment variable is not set")
    
    # Generate a state token to prevent CSRF
    state = secrets.token_urlsafe(16)
    # Store the state token in our file-based storage
    save_state(state)
    
    # Define the OAuth parameters
    # Use a fixed redirect URI that matches what's registered in GitHub OAuth app settings
    redirect_uri = "http://localhost:5001/auth/github/callback"
    print(f"Using redirect URI: {redirect_uri}")
    
    params = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "state": state,
        "scope": "user:email"  # Request access to user's email
    }
    
    # Build the authorization URL
    auth_url = "https://github.com/login/oauth/authorize?" + urlencode(params)
    
    return auth_url

def start_github_login():
    """Initiates the GitHub OAuth login flow"""
    try:
        # Make sure session is permanent to persist across requests
        session.permanent = True
        
        auth_url = get_github_auth_url()
        print(f"GitHub OAuth URL: {auth_url}")
        
        # Make sure the session is saved
        session.modified = True
        
        return redirect(auth_url)
    except Exception as e:
        print(f"Error initiating GitHub login: {str(e)}")
        import traceback
        traceback.print_exc()
        flash(f"Error initiating GitHub login: {str(e)}", "error")
        return redirect(url_for("login"))

def handle_github_callback(app):
    """Handles the callback from GitHub OAuth"""
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
        
        # Exchange the code for an access token
        client_id = os.getenv("GITHUB_CLIENT_ID", "Ov23liWQZyjkDqbYLy8S")
        client_secret = os.getenv("GITHUB_CLIENT_SECRET", "fb8537db166dc7ab394d8c37aa21e70c1311d1c8")
        
        token_url = "https://github.com/login/oauth/access_token"
        # Use the same fixed redirect URI as in the authorization request
        redirect_uri = "http://localhost:5001/auth/github/callback"
        print(f"Using token exchange redirect URI: {redirect_uri}")
        
        token_data = {
            "client_id": client_id,
            "client_secret": client_secret,
            "code": code,
            "redirect_uri": redirect_uri
        }
        
        headers = {
            "Accept": "application/json"
        }
        
        token_response = requests.post(token_url, data=token_data, headers=headers)
        token_json = token_response.json()
        
        if "error" in token_json:
            flash(f"Authentication failed: {token_json['error']}", "error")
            return redirect(url_for("login"))
        
        # Get the access token
        access_token = token_json.get("access_token")
        if not access_token:
            flash("Authentication failed: No access token received", "error")
            return redirect(url_for("login"))
        
        # Get the user info using the access token
        userinfo_url = "https://api.github.com/user"
        headers = {
            "Authorization": f"token {access_token}",
            "Accept": "application/json"
        }
        
        userinfo_response = requests.get(userinfo_url, headers=headers)
        userinfo = userinfo_response.json()
        
        # GitHub might not provide email in the user profile if it's private
        # So we need to fetch emails separately
        email = userinfo.get("email")
        if not email:
            emails_url = "https://api.github.com/user/emails"
            emails_response = requests.get(emails_url, headers=headers)
            emails = emails_response.json()
            
            # Find the primary email
            for email_obj in emails:
                if email_obj.get("primary") and email_obj.get("verified"):
                    email = email_obj.get("email")
                    break
        
        if not email:
            flash("Failed to retrieve email from GitHub", "error")
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
                
                # Update the user's auth_provider to "github"
                app.supabase.table("Users").update({
                    "last_login": str(datetime.datetime.now()),
                    "auth_provider": "github"
                }).filter("id", "eq", verification_user_id).execute()
                
                flash("Account verified successfully with GitHub!", "success")
            else:
                # Just a regular login, update last login time
                app.supabase.table("Users").update({
                    "last_login": str(datetime.datetime.now())
                }).filter("id", "eq", user_id).execute()
                
                flash("Welcome back! You've been logged in with GitHub.", "success")
            
            # Set session variables
            session['user_id'] = user_id
            session['username'] = username
            session['email'] = email
        else:
            # User doesn't exist, create a new account
            user_id = str(uuid.uuid4())
            
            # Get name from GitHub profile
            name = userinfo.get("name")
            login = userinfo.get("login")
            
            # Use name if available, otherwise use login
            username = name if name else login
            
            # Insert new user
            new_user = {
                "id": user_id,
                "username": username,
                "email": email,
                "is_verified": True,  # GitHub accounts are pre-verified
                "created_at": str(datetime.datetime.now()),
                "last_login": str(datetime.datetime.now()),
                "auth_provider": "github"
            }
            
            app.supabase.table("Users").insert(new_user).execute()
            
            # Set session variables
            session['user_id'] = user_id
            session['username'] = username
            session['email'] = email
            
            flash("Account created successfully with GitHub!", "success")
        
        return redirect(url_for('profile'))
        
    except Exception as e:
        print(f"Error during GitHub authentication: {str(e)}")
        import traceback
        traceback.print_exc()
        flash(f"Error during GitHub authentication: {str(e)}", "error")
        return redirect(url_for('login'))