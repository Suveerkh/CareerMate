# app.py

from flask import Flask, request, redirect, url_for, render_template, session, flash, jsonify
from supabase import create_client, Client
import hashlib
import os
import datetime
import uuid
import json
import requests
import random
from functools import wraps
from dotenv import load_dotenv
from flask_mail import Mail, Message
from itsdangerous import URLSafeTimedSerializer
from urllib.parse import urlencode
from flask_session import Session
from simple_google_auth import start_google_login, handle_google_callback
from github_auth import start_github_login, handle_github_callback
from state_storage import cleanup_expired_states
from news_fetcher import load_news_data, start_news_updater
from career_test import get_test_questions, calculate_career_matches, save_test_results, get_personality_insights, generate_pdf_report
from subscription_plans import (
    FEATURES, 
    get_user_subscriptions, 
    check_feature_access, 
    get_feature_tier, 
    get_feature_comparison, 
    purchase_feature, 
    cancel_subscription, 
    get_user_active_subscriptions
)

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)
# Set a secret key for session management
app.secret_key = os.getenv("SECRET_KEY", "dev_secret_key")
# Set session to be permanent and last for 30 days
app.permanent_session_lifetime = datetime.timedelta(days=30)

# Configure session to be more secure and reliable
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_COOKIE_SECURE'] = False  # Set to True in production with HTTPS
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_USE_SIGNER'] = True

# Initialize Flask-Session
Session(app)

# Add a custom filter for datetime formatting
@app.template_filter('datetimeformat')
def datetimeformat(value, format='%B %d, %Y'):
    if isinstance(value, str):
        try:
            value = datetime.datetime.fromisoformat(value)
        except ValueError:
            return value
    return value.strftime(format)

# Initialize Supabase client as None, will be set up later
app.supabase = None

# Clean up expired state tokens periodically
@app.before_request
def cleanup_before_request():
    # Only run cleanup occasionally to avoid overhead
    if random.random() < 0.1:  # 10% chance of running on each request
        cleanup_expired_states()

# Configure Flask-Mail
app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT', 587))
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_DEFAULT_SENDER')

mail = Mail(app)

# Initialize serializer for email verification tokens
ts = URLSafeTimedSerializer(app.secret_key)

# Context processor to add variables to all templates
@app.context_processor
def inject_now():
    return {'now': datetime.datetime.now()}

# Career categories and paths
CAREER_CATEGORIES = {
    "technology": {
        "name": "Technology",
        "careers": [
            {"id": "data-scientist", "title": "Data Scientist"},
            {"id": "software-engineer", "title": "Software Engineer"},
            {"id": "web-developer", "title": "Web Developer"},
            {"id": "cybersecurity-analyst", "title": "Cybersecurity Analyst"},
            {"id": "cloud-architect", "title": "Cloud Architect"}
        ]
    },
    "business": {
        "name": "Business",
        "careers": [
            {"id": "management-consultant", "title": "Management Consultant"},
            {"id": "financial-analyst", "title": "Financial Analyst"},
            {"id": "marketing-manager", "title": "Marketing Manager"},
            {"id": "project-manager", "title": "Project Manager"},
            {"id": "business-analyst", "title": "Business Analyst"}
        ]
    },
    "healthcare": {
        "name": "Healthcare",
        "careers": [
            {"id": "physician", "title": "Physician"},
            {"id": "nurse-practitioner", "title": "Nurse Practitioner"},
            {"id": "pharmacist", "title": "Pharmacist"},
            {"id": "physical-therapist", "title": "Physical Therapist"},
            {"id": "healthcare-administrator", "title": "Healthcare Administrator"}
        ]
    },
    "education": {
        "name": "Education",
        "careers": [
            {"id": "professor", "title": "Professor"},
            {"id": "school-counselor", "title": "School Counselor"},
            {"id": "education-administrator", "title": "Education Administrator"},
            {"id": "instructional-designer", "title": "Instructional Designer"},
            {"id": "special-education-teacher", "title": "Special Education Teacher"}
        ]
    }
}

# Degree programs data structure
DEGREE_PROGRAMS = {
    "students": {
        "name": "Undergraduate Degrees",
        "streams": {
            "science": {
                "name": "Science",
                "degrees": [
                    {"id": "btech", "title": "B.Tech", "template": "students_science_btech.html"},
                    {"id": "bsc", "title": "B.Sc", "template": "students_science_bsc.html"}
                ]
            },
            "commerce": {
                "name": "Commerce",
                "degrees": [
                    {"id": "bba", "title": "BBA", "template": "students_commerce_bba.html"},
                    {"id": "bcom", "title": "B.Com", "template": "students_commerce_bcom.html"}
                ]
            },
            "arts": {
                "name": "Arts",
                "degrees": [
                    {"id": "ba", "title": "B.A", "template": "students_arts_ba.html"}
                ]
            },
            "education": {
                "name": "Education",
                "degrees": [
                    {"id": "bed", "title": "B.Ed", "template": "students_education_bed.html"}
                ]
            }
        }
    },
    "graduates": {
        "name": "Graduate Degrees",
        "degrees": [
            {"id": "mba", "title": "MBA", "template": "graduates_mba.html"},
            {"id": "mca", "title": "MCA", "template": "graduates_mca.html"},
            {"id": "msc", "title": "M.Sc", "template": "graduates_msc.html"},
            {"id": "mcom", "title": "M.Com", "template": "graduates_mcom.html"},
            {"id": "ma", "title": "M.A", "template": "graduates_ma.html"},
            {"id": "med", "title": "M.Ed", "template": "graduates_med.html"},
            {"id": "pgdm", "title": "PGDM", "template": "graduates_pgdm.html"}
        ]
    },
    "postgraduates": {
        "name": "Post-Graduate Degrees",
        "degrees": [
            {"id": "phd", "title": "PhD", "template": "postgraduates_phd.html"},
            {"id": "postdoc", "title": "Post-Doctoral", "template": "postgraduates_postdoc.html"}
        ]
    }
}

def init_supabase():
    """Initialize the Supabase client if not already done"""
    if app.supabase is None:
        try:
            # Supabase credentials
            SUPABASE_URL = os.getenv("SUPABASE_URL")
            SUPABASE_KEY = os.getenv("SUPABASE_KEY")
            
            if not SUPABASE_URL or not SUPABASE_KEY:
                raise ValueError("Supabase credentials not found in environment variables")
                
            app.supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        except Exception as e:
            print(f"Error initializing Supabase client: {str(e)}")
            # Re-raise the exception to be handled by the caller
            raise

# Helper function to send verification email
def send_verification_email(email, token):
    msg = Message("Verify your email for CareerMate", recipients=[email])
    verify_url = url_for('verify_email', token=token, _external=True)
    msg.body = f"Please click the link to verify your email: {verify_url}"
    msg.html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Verify Your CareerMate Account</title>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background-color: #4285f4; color: white; padding: 20px; text-align: center; border-radius: 5px 5px 0 0; }}
            .content {{ padding: 20px; border: 1px solid #ddd; border-top: none; border-radius: 0 0 5px 5px; }}
            .button {{ display: inline-block; background-color: #4285f4; color: white; text-decoration: none; padding: 10px 20px; border-radius: 5px; margin: 20px 0; }}
            .footer {{ margin-top: 20px; font-size: 12px; color: #777; text-align: center; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>Welcome to CareerMate!</h1>
        </div>
        <div class="content">
            <p>Thank you for signing up with CareerMate. We're excited to help you on your career journey!</p>
            <p>Please verify your email address by clicking the button below:</p>
            <p style="text-align: center;">
                <a href="{verify_url}" class="button">Verify Email Address</a>
            </p>
            <p>If the button doesn't work, you can also copy and paste the following link into your browser:</p>
            <p style="word-break: break-all; font-size: 14px;">{verify_url}</p>
            <p>This link will expire in 24 hours.</p>
            <p>If you did not sign up for CareerMate, please ignore this email.</p>
        </div>
        <div class="footer">
            <p>&copy; {datetime.datetime.now().year} CareerMate. All rights reserved.</p>
        </div>
    </body>
    </html>
    """
    try:
        mail.send(msg)
        return True
    except Exception as e:
        print(f"Error sending email: {str(e)}")
        return False

# Login required decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Get career details by ID
def get_career_by_id(career_id):
    for category in CAREER_CATEGORIES.values():
        for career in category['careers']:
            if career['id'] == career_id:
                return career
    return None

# Get all careers
def get_all_careers():
    all_careers = []
    for category in CAREER_CATEGORIES.values():
        all_careers.extend(category['careers'])
    return all_careers

# Get all degrees
def get_all_degrees():
    all_degrees = []
    
    # Get undergraduate degrees (with streams)
    students = DEGREE_PROGRAMS.get("students", {})
    for stream_id, stream in students.get("streams", {}).items():
        for degree in stream.get("degrees", []):
            degree_copy = degree.copy()
            degree_copy["level"] = "students"
            degree_copy["stream"] = stream_id
            degree_copy["level_name"] = students.get("name", "Undergraduate")
            degree_copy["stream_name"] = stream.get("name", "")
            all_degrees.append(degree_copy)
    
    # Get graduate degrees (no streams)
    graduates = DEGREE_PROGRAMS.get("graduates", {})
    for degree in graduates.get("degrees", []):
        degree_copy = degree.copy()
        degree_copy["level"] = "graduates"
        degree_copy["level_name"] = graduates.get("name", "Graduate")
        all_degrees.append(degree_copy)
    
    # Get postgraduate degrees (no streams)
    postgraduates = DEGREE_PROGRAMS.get("postgraduates", {})
    for degree in postgraduates.get("degrees", []):
        degree_copy = degree.copy()
        degree_copy["level"] = "postgraduates"
        degree_copy["level_name"] = postgraduates.get("name", "Post-Graduate")
        all_degrees.append(degree_copy)
    
    return all_degrees


@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]
        
        # Validate input
        if not username or not email or not password:
            flash("All fields are required", "error")
            return render_template("signup.html")
            
        if len(password) < 6:
            flash("Password must be at least 6 characters long", "error")
            return render_template("signup.html")

        # Hash the password before saving
        hashed_password = hashlib.sha256(password.encode()).hexdigest()

        # Generate a unique ID for the user
        user_id = str(uuid.uuid4())

        # Insert the new user into the 'Users' table in Supabase
        data = {
            "id": user_id,
            "username": username,
            "email": email,
            "password_hash": hashed_password,
            "is_verified": True,  # Set to True by default since we're removing email verification
            "created_at": str(datetime.datetime.now()),
            "auth_provider": "local"  # Indicate this is a local account
        }

        # Initialize Supabase if not already done
        init_supabase()
        
        try:
            # Check if email already exists using filter
            try:
                existing_user = app.supabase.table("Users").select("email").filter("email", "eq", email).execute()
                
                if existing_user.data and len(existing_user.data) > 0:
                    flash("Email already registered", "error")
                    return render_template("signup.html")
            except Exception as check_error:
                # Log the error but continue with signup attempt
                print(f"Error checking existing user: {str(check_error)}")
                
            # Insert into Supabase
            try:
                print("Attempting to insert user data into Supabase...")
                response = app.supabase.table("Users").insert(data).execute()
                print(f"Response received: {response}")
                
                # Check for success or failure in response and redirect
                if hasattr(response, 'data') and response.data:
                    print(f"User created successfully with data: {response.data}")
                    
                    # Store user info in session
                    session['user_id'] = user_id
                    session['username'] = username
                    session['email'] = email
                    
                    flash("Account created successfully! You can now use all features of CareerMate.", "success")
                    return redirect(url_for("profile"))
                else:
                    print(f"Error in response: {response}")
                    flash("An error occurred during signup", "error")
                    return render_template("signup.html")
            except ValueError as json_error:
                # Handle JSON parsing errors
                print(f"JSON parsing error: {str(json_error)}")
                flash("Error processing the response from the server", "error")
                return render_template("signup.html")
                
        except Exception as e:
            flash(f"An error occurred: {str(e)}", "error")
            return render_template("signup.html")

    return render_template("signup.html")

@app.route("/verify-email/<token>")
def verify_email(token):
    try:
        # Verify the token (valid for 24 hours)
        email = ts.loads(token, salt="email-confirm-key", max_age=86400)
        
        # Initialize Supabase if not already done
        init_supabase()
        
        # Update user's verification status
        response = app.supabase.table("Users").update({"is_verified": True}).filter("email", "eq", email).execute()
        
        if hasattr(response, 'data') and response.data:
            flash("Email verified successfully! You can now log in.", "success")
        else:
            flash("Error verifying email. Please try again or contact support.", "error")
            
    except Exception as e:
        flash("Invalid or expired verification link. Please request a new one.", "error")
        
    return redirect(url_for("login"))

@app.route("/resend-verification", methods=["GET", "POST"])
def resend_verification():
    if request.method == "POST":
        email = request.form.get("email")
        
        if not email:
            flash("Email is required", "error")
            return render_template("resend_verification.html")
            
        # Initialize Supabase if not already done
        init_supabase()
        
        try:
            # Check if user exists and is not verified
            user = app.supabase.table("Users").select("id", "is_verified").filter("email", "eq", email).execute()
            
            if not user.data or len(user.data) == 0:
                # Don't reveal if email exists or not for security
                flash("If your email is registered, a verification link has been sent.", "info")
                return render_template("resend_verification.html")
                
            # Check if already verified
            if user.data[0].get("is_verified", False):
                flash("This email is already verified. Please log in.", "info")
                return redirect(url_for("login"))
                
            # Generate new verification token
            token = ts.dumps(email, salt='email-confirm-key')
            
            # Send verification email
            email_sent = send_verification_email(email, token)
            
            if email_sent:
                flash("Verification email has been resent. Please check your inbox.", "success")
            else:
                flash("Error sending verification email. Please try again later.", "error")
                
        except Exception as e:
            print(f"Error resending verification: {str(e)}")
            flash("An error occurred. Please try again later.", "error")
            
    return render_template("resend_verification.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    # Check if user is already logged in
    if 'user_id' in session:
        return redirect(url_for('profile'))
        
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        remember_me = 'remember_me' in request.form
        
        # Validate input
        if not email or not password:
            flash("Email and password are required", "error")
            return render_template("login.html")

        # Hash the password to match the stored hash
        hashed_password = hashlib.sha256(password.encode()).hexdigest()

        # Initialize Supabase if not already done
        init_supabase()

        try:
            # Check if the email and password match using filter
            try:
                user = app.supabase.table("Users").select("id", "username", "email", "password_hash", "is_verified", "current_status").filter("email", "eq", email).execute()

                if user.data and len(user.data) > 0:
                    # If user exists, check if the password hash matches
                    stored_password_hash = user.data[0]["password_hash"]
                    
                    if hashed_password == stored_password_hash:
                        # Make session permanent if remember_me is checked
                        if remember_me:
                            session.permanent = True
                            
                        # Store user info in session
                        session['user_id'] = user.data[0]["id"]
                        session['username'] = user.data[0]["username"]
                        session['email'] = user.data[0]["email"]
                        
                        flash("Login successful!", "success")
                        return redirect(url_for("profile"))  # Redirect to profile
                    else:
                        flash("Invalid password", "error")
                else:
                    flash("User not found", "error")
            except ValueError as json_error:
                # Handle JSON parsing errors
                flash("Error processing the response from the server", "error")
            except Exception as query_error:
                flash(f"Error querying user data: {str(query_error)}", "error")
        except Exception as e:
            flash(f"An error occurred: {str(e)}", "error")

    return render_template("login.html")

@app.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "POST":
        email = request.form.get("email")
        
        if not email:
            flash("Email is required", "error")
            return render_template("forgot_password.html")
            
        # Initialize Supabase if not already done
        init_supabase()
        
        try:
            # Check if user exists
            user = app.supabase.table("Users").select("id").filter("email", "eq", email).execute()
            
            if user.data and len(user.data) > 0:
                # Generate password reset token
                token = ts.dumps(email, salt='password-reset-key')
                
                # Send password reset email
                msg = Message("Reset Your CareerMate Password", recipients=[email])
                reset_url = url_for('reset_password', token=token, _external=True)
                msg.body = f"Please click the link to reset your password: {reset_url}"
                msg.html = f"""
                <h1>Reset Your CareerMate Password</h1>
                <p>Please click the link below to reset your password:</p>
                <p><a href="{reset_url}">Reset Password</a></p>
                <p>If you did not request a password reset, please ignore this email.</p>
                """
                
                try:
                    mail.send(msg)
                    flash("Password reset instructions have been sent to your email.", "success")
                except Exception as mail_error:
                    flash("Could not send password reset email. Please try again later.", "error")
            else:
                # Don't reveal if user exists or not for security
                flash("If your email is registered, you will receive password reset instructions.", "info")
                
        except Exception as e:
            flash("An error occurred. Please try again later.", "error")
            
    return render_template("forgot_password.html")


@app.route("/profile")
@login_required
def profile():
    # Get user data from session
    user_id = session.get('user_id')
    username = session.get('username')
    email = session.get('email')
    current_status = session.get('current_status', '')
    
    # Initialize Supabase if not already done
    init_supabase()
    
    # Check if user is authenticated with Google/GitHub and get created_at date
    try:
        user_data = app.supabase.table("Users").select("auth_provider, created_at").filter("id", "eq", user_id).execute()
        is_google_authenticated = False
        is_github_authenticated = False
        created_at = None
        
        if user_data.data and len(user_data.data) > 0:
            auth_provider = user_data.data[0].get('auth_provider')
            is_google_authenticated = auth_provider == 'google'
            is_github_authenticated = auth_provider == 'github'
            created_at_str = user_data.data[0].get('created_at')
            if created_at_str:
                # Convert string date to datetime object
                created_at = datetime.datetime.fromisoformat(created_at_str.replace('Z', '+00:00')) if isinstance(created_at_str, str) else created_at_str
    except Exception as e:
        print(f"Error checking user data: {str(e)}")
        is_google_authenticated = False
        is_github_authenticated = False
        created_at = None
    
    # Get user activities
    activities = []
    try:
        activities_response = app.supabase.table("UserActivities").select("*").filter("user_id", "eq", user_id).order("created_at", desc=True).limit(10).execute()
        
        if hasattr(activities_response, 'data') and activities_response.data:
            for activity in activities_response.data:
                # Convert string dates to datetime objects
                created_at = datetime.datetime.fromisoformat(activity["created_at"].replace('Z', '+00:00')) if isinstance(activity["created_at"], str) else activity["created_at"]
                
                # Add activity with datetime object
                activities.append({
                    "current_status": current_status,
                    **activity,
                    "created_at": created_at
                })
    except Exception as e:
        print(f"Error fetching user activities: {str(e)}")
        # Continue without activities if there's an error
    
    return render_template(
        "profile.html", 
        username=username, 
        email=email, 
        user_id=user_id, 
        is_google_authenticated=is_google_authenticated,
        is_github_authenticated=is_github_authenticated,
        activities=activities,
        CAREER_CATEGORIES=CAREER_CATEGORIES,
        created_at=created_at
    )

@app.route("/edit_profile", methods=["GET", "POST"])
@login_required
def edit_profile():
    # Get user data from session
    user_id = session.get('user_id')
    username = session.get('username')
    email = session.get('email')
    current_status = session.get('current_status', '')
    
    if request.method == "POST":
        # Get form data
        new_username = request.form.get("username")
        new_current_status = request.form.get("current_status", "")
        
        # Validate input
        if not new_username:
            flash("Username cannot be empty", "error")
            return render_template("edit_profile.html", username=username, email=email, current_status=current_status, CAREER_CATEGORIES=CAREER_CATEGORIES)
        
        # Initialize Supabase if not already done
        init_supabase()
        
        try:
            # Update user data in Supabase
            response = app.supabase.table("Users").update({
                "username": new_username,
                "current_status": new_current_status
            }).eq("id", user_id).execute()
            
            if hasattr(response, 'data') and response.data:
                # Update session data
                session['username'] = new_username
                session['current_status'] = new_current_status
                flash("Profile updated successfully!", "success")
                return redirect(url_for("profile"))
            else:
                flash("An error occurred while updating your profile", "error")
        except Exception as e:
            flash(f"An error occurred: {str(e)}", "error")
    
    return render_template("edit_profile.html", username=username, email=email, current_status=current_status, CAREER_CATEGORIES=CAREER_CATEGORIES)

@app.route("/reset-password/<token>", methods=["GET", "POST"])
def reset_password(token):
    try:
        # Verify the token (valid for 24 hours)
        email = ts.loads(token, salt="password-reset-key", max_age=86400)
    except Exception as e:
        flash("Invalid or expired reset link. Please request a new one.", "error")
        return redirect(url_for("forgot_password"))
        
    if request.method == "POST":
        password = request.form.get("password")
        confirm_password = request.form.get("confirm_password")
        
        if not password or not confirm_password:
            flash("All fields are required", "error")
            return render_template("reset_password.html", token=token)
            
        if password != confirm_password:
            flash("Passwords do not match", "error")
            return render_template("reset_password.html", token=token)
            
        if len(password) < 6:
            flash("Password must be at least 6 characters long", "error")
            return render_template("reset_password.html", token=token)
            
        # Hash the new password
        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        
        # Initialize Supabase if not already done
        init_supabase()
        
        try:
            # Update user's password
            response = app.supabase.table("Users").update({"password_hash": hashed_password}).filter("email", "eq", email).execute()
            
            if hasattr(response, 'data') and response.data:
                flash("Password reset successfully! You can now log in with your new password.", "success")
                return redirect(url_for("login"))
            else:
                flash("Error resetting password. Please try again or contact support.", "error")
                
        except Exception as e:
            flash(f"An error occurred: {str(e)}", "error")
            
    return render_template("reset_password.html", token=token)

@app.route("/careers")
@login_required
def careers():
    # Get all career categories
    categories = CAREER_CATEGORIES
    
    # Get query parameters for filtering
    level = request.args.get('level')
    stream = request.args.get('stream')
    course = request.args.get('course')
    
    # Redirect to specific templates based on query parameters
    if level == 'students':
        # Create degree path for students (includes stream)
        degree_path = f"{level}/{stream}/{course}"
        user_id = session.get('user_id')
        username = session.get('username')
        
        # Initialize Supabase if not already done
        init_supabase()
        
        # Get reviews for this degree path
        reviews = []
        try:
            # Get all reviews for this degree path
            reviews_response = app.supabase.table("Reviews").select("*").filter("degree_path", "eq", degree_path).order("created_at", desc=True).execute()
            
            if hasattr(reviews_response, 'data') and reviews_response.data:
                for review in reviews_response.data:
                    # Get username for each review
                    user_response = app.supabase.table("Users").select("username").filter("id", "eq", review["user_id"]).execute()
                    username_from_db = user_response.data[0]["username"] if user_response.data else "Anonymous"
                    
                    # Check if current user has liked this review
                    user_liked = False
                    if user_id:
                        liked_response = app.supabase.table("ReviewLikes").select("*").filter("user_id", "eq", user_id).filter("review_id", "eq", review["review_id"]).execute()
                        user_liked = hasattr(liked_response, 'data') and liked_response.data and len(liked_response.data) > 0
                    
                    # Convert string dates to datetime objects
                    created_at = datetime.datetime.fromisoformat(review["created_at"].replace('Z', '+00:00')) if isinstance(review["created_at"], str) else review["created_at"]
                    
                    # Add review with username to the list
                    reviews.append({
                        **review,
                        "username": username_from_db,
                        "user_liked": user_liked,
                        "created_at": created_at
                    })
        except Exception as e:
            print(f"Error fetching reviews: {str(e)}")
            # Continue without reviews if there's an error
        
        template_params = {
            "categories": categories,
            "reviews": reviews,
            "user_id": user_id,
            "username": username,
            "degree_path": degree_path
        }
        
        if stream == 'science':
            if course == 'btech':
                return render_template("students_science_btech.html", **template_params)
            elif course == 'bsc':
                return render_template("students_science_bsc.html", **template_params)
        elif stream == 'commerce':
            if course == 'bba':
                return render_template("students_commerce_bba.html", **template_params)
            elif course == 'bcom':
                return render_template("students_commerce_bcom.html", **template_params)
        elif stream == 'arts':
            if course == 'ba':
                return render_template("students_arts_ba.html", **template_params)
        elif stream == 'education':
            if course == 'bed':
                return render_template("students_education_bed.html", **template_params)

    elif level == 'graduates':
        # Check for specific graduate courses
        degree_path = f"{level}/{course}"
        user_id = session.get('user_id')
        username = session.get('username')
        
        # Initialize Supabase if not already done
        init_supabase()
        
        # Get reviews for this degree path
        reviews = []
        try:
            # Get all reviews for this degree path
            reviews_response = app.supabase.table("Reviews").select("*").filter("degree_path", "eq", degree_path).order("created_at", desc=True).execute()
            
            if hasattr(reviews_response, 'data') and reviews_response.data:
                for review in reviews_response.data:
                    # Get username for each review
                    user_response = app.supabase.table("Users").select("username").filter("id", "eq", review["user_id"]).execute()
                    username_from_db = user_response.data[0]["username"] if user_response.data else "Anonymous"
                    
                    # Check if current user has liked this review
                    user_liked = False
                    if user_id:
                        liked_response = app.supabase.table("ReviewLikes").select("*").filter("user_id", "eq", user_id).filter("review_id", "eq", review["review_id"]).execute()
                        user_liked = hasattr(liked_response, 'data') and liked_response.data and len(liked_response.data) > 0
                    
                    # Convert string dates to datetime objects
                    created_at = datetime.datetime.fromisoformat(review["created_at"].replace('Z', '+00:00')) if isinstance(review["created_at"], str) else review["created_at"]
                    
                    # Add review with username to the list
                    reviews.append({
                        **review,
                        "username": username_from_db,
                        "user_liked": user_liked,
                        "created_at": created_at
                    })
        except Exception as e:
            print(f"Error fetching reviews: {str(e)}")
            # Continue without reviews if there's an error
        
        template_params = {
            "categories": categories,
            "reviews": reviews,
            "user_id": user_id,
            "username": username,
            "degree_path": degree_path
        }
        
        if course == 'mba':
            return render_template("graduates_mba.html", **template_params)
        elif course == 'mca':
            return render_template("graduates_mca.html", **template_params)
        elif course == 'msc':
            return render_template("graduates_msc.html", **template_params)
        elif course == 'mcom':
            return render_template("graduates_mcom.html", **template_params)
        elif course == 'ma':
            return render_template("graduates_ma.html", **template_params)
        elif course == 'med':
            return render_template("graduates_med.html", **template_params)
        elif course == 'pgdm':
            return render_template("graduates_pgdm.html", **template_params)
        else:
            # Redirect to careers page if no specific graduate course is selected
            return redirect(url_for('careers'))
    elif level == 'postgraduates':
        # Check for specific postgraduate courses
        degree_path = f"{level}/{course}"
        user_id = session.get('user_id')
        username = session.get('username')
        
        # Initialize Supabase if not already done
        init_supabase()
        
        # Get reviews for this degree path
        reviews = []
        try:
            # Get all reviews for this degree path
            reviews_response = app.supabase.table("Reviews").select("*").filter("degree_path", "eq", degree_path).order("created_at", desc=True).execute()
            
            if hasattr(reviews_response, 'data') and reviews_response.data:
                for review in reviews_response.data:
                    # Get username for each review
                    user_response = app.supabase.table("Users").select("username").filter("id", "eq", review["user_id"]).execute()
                    username_from_db = user_response.data[0]["username"] if user_response.data else "Anonymous"
                    
                    # Check if current user has liked this review
                    user_liked = False
                    if user_id:
                        liked_response = app.supabase.table("ReviewLikes").select("*").filter("user_id", "eq", user_id).filter("review_id", "eq", review["review_id"]).execute()
                        user_liked = hasattr(liked_response, 'data') and liked_response.data and len(liked_response.data) > 0
                    
                    # Convert string dates to datetime objects
                    created_at = datetime.datetime.fromisoformat(review["created_at"].replace('Z', '+00:00')) if isinstance(review["created_at"], str) else review["created_at"]
                    
                    # Add review with username to the list
                    reviews.append({
                        **review,
                        "username": username_from_db,
                        "user_liked": user_liked,
                        "created_at": created_at
                    })
        except Exception as e:
            print(f"Error fetching reviews: {str(e)}")
            # Continue without reviews if there's an error
        
        template_params = {
            "categories": categories,
            "reviews": reviews,
            "user_id": user_id,
            "username": username,
            "degree_path": degree_path
        }
        
        if course == 'phd':
            return render_template("postgraduates_phd.html", **template_params)
        elif course == 'postdoc':
            return render_template("postgraduates_postdoc.html", **template_params)
        else:
            # Redirect to careers page if no specific postgraduate course is selected
            return redirect(url_for('careers'))
    
    # If no specific template matches, use the default careers template
    return render_template("careers.html", categories=categories)

@app.route("/careers/category/<category_id>")
@login_required
def career_category(category_id):
    # Get specific category
    if category_id in CAREER_CATEGORIES:
        category = CAREER_CATEGORIES[category_id]
        return render_template("career_category.html", category=category, category_id=category_id)
    else:
        flash("Category not found", "error")
        return redirect(url_for("careers"))

@app.route("/careers/path/<career_id>")
@login_required
def career_path(career_id):
    # Find the career by ID
    career = get_career_by_id(career_id)
    
    if career:
        # Get the category this career belongs to
        category_id = None
        for cat_id, category in CAREER_CATEGORIES.items():
            for c in category['careers']:
                if c['id'] == career_id:
                    category_id = cat_id
                    break
            if category_id:
                break
                
        return render_template("career_path.html", career=career, category_id=category_id)
    else:
        flash("Career path not found", "error")
        return redirect(url_for("careers"))

@app.route("/search", methods=["GET"])
@login_required
def search():
    query = request.args.get("q", "")
    
    if not query:
        return redirect(url_for("careers"))
    
    # Initialize results
    career_results = []
    degree_results = []
    
    # Search for careers matching the query
    all_careers = get_all_careers()
    for career in all_careers:
        if query.lower() in career['title'].lower():
            career_results.append(career)
    
    # Search for degrees matching the query
    all_degrees = get_all_degrees()
    for degree in all_degrees:
        if query.lower() in degree['title'].lower():
            degree_results.append(degree)
    
    return render_template(
        "search_results.html", 
        career_results=career_results, 
        degree_results=degree_results, 
        query=query
    )

# Reviews functionality
@app.route("/submit-review/<path:degree_path>", methods=["POST"])
@login_required
def submit_review(degree_path):
    """Submit a review for a degree program"""
    try:
        print(f"Received review submission for degree_path: {degree_path}")
        print(f"Form data: {request.form}")
        
        # Get form data
        rating = request.form.get("rating")
        review_text = request.form.get("review_text")
        pros = request.form.get("pros")
        cons = request.form.get("cons")
        current_status = request.form.get("current_status")
        
        print(f"Rating: {rating}, Review text: {review_text}, Current status: {current_status}")
        
        # Validate input
        if not rating or not review_text or not current_status:
            print("Validation failed: Rating, review text, and current status are required")
            return jsonify({"success": False, "message": "Rating, review text, and current status are required"}), 400
            
        # Convert rating to integer (1-5)
        try:
            rating = int(rating)
            if rating < 1 or rating > 5:
                print(f"Validation failed: Rating must be between 1 and 5, got {rating}")
                return jsonify({"success": False, "message": "Rating must be between 1 and 5"}), 400
        except ValueError:
            print(f"Validation failed: Invalid rating value: {rating}")
            return jsonify({"success": False, "message": "Invalid rating value"}), 400
            
        # Get user info
        user_id = session.get("user_id")
        print(f"User ID from session: {user_id}")
        
        # Initialize Supabase if not already done
        try:
            print("Initializing Supabase connection")
            init_supabase()
            print("Supabase connection initialized successfully")
        except Exception as supabase_init_error:
            print(f"Error initializing Supabase: {str(supabase_init_error)}")
            return jsonify({"success": False, "message": f"Database connection error: {str(supabase_init_error)}"}), 500
        
        # Create review data
        review_id = str(uuid.uuid4())
        review_data = {
            "review_id": review_id,
            "user_id": user_id,
            "degree_path": degree_path,
            "rating": rating,
            "review_text": review_text,
            "pros": pros,
            "cons": cons,
            "current_status": current_status,
            "created_at": str(datetime.datetime.now()),
            "updated_at": str(datetime.datetime.now()),
            "likes": 0
        }
        
        print(f"Prepared review data: {review_data}")
        
        try:
            # Insert review into Supabase
            print("Attempting to insert review into Supabase")
            response = app.supabase.table("Reviews").insert(review_data).execute()
            print(f"Supabase response: {response}")
            
            if hasattr(response, 'data') and response.data:
                print("Review inserted successfully")
                # Note: UserActivities table doesn't exist, so we're skipping activity tracking
                
                return jsonify({"success": True, "review_id": review_id}), 200
            else:
                print("No data in response or response is invalid")
                return jsonify({"success": False, "message": "Error saving review: No data returned from database"}), 500
        except Exception as insert_error:
            print(f"Error inserting review: {str(insert_error)}")
            return jsonify({"success": False, "message": f"Error saving review: {str(insert_error)}"}), 500
            
    except Exception as e:
        print(f"Error submitting review: {str(e)}")
        return jsonify({"success": False, "message": f"Unexpected error: {str(e)}"}), 500

@app.route("/like-review/<review_id>", methods=["POST"])
@login_required
def like_review(review_id):
    """Like or unlike a review"""
    try:
        # Get user info
        user_id = session.get("user_id")
        
        # Initialize Supabase if not already done
        init_supabase()
        
        # Check if user has already liked this review
        liked_response = app.supabase.table("ReviewLikes").select("*").filter("user_id", "eq", user_id).filter("review_id", "eq", review_id).execute()
        
        if hasattr(liked_response, 'data') and liked_response.data and len(liked_response.data) > 0:
            # User already liked this review, so unlike it
            app.supabase.table("ReviewLikes").delete().filter("user_id", "eq", user_id).filter("review_id", "eq", review_id).execute()
            
            # Decrement likes count
            review_response = app.supabase.table("Reviews").select("likes").filter("review_id", "eq", review_id).execute()
            current_likes = review_response.data[0]["likes"] if review_response.data else 0
            new_likes = max(0, current_likes - 1)  # Ensure likes don't go below 0
            
            app.supabase.table("Reviews").update({"likes": new_likes}).filter("review_id", "eq", review_id).execute()
            
            return jsonify({"success": True, "liked": False, "likes": new_likes}), 200
        else:
            # User hasn't liked this review yet, so add a like
            like_data = {
                "like_id": str(uuid.uuid4()),
                "user_id": user_id,
                "review_id": review_id,
                "created_at": str(datetime.datetime.now())
            }
            
            app.supabase.table("ReviewLikes").insert(like_data).execute()
            
            # Increment likes count
            review_response = app.supabase.table("Reviews").select("likes").filter("review_id", "eq", review_id).execute()
            current_likes = review_response.data[0]["likes"] if review_response.data else 0
            new_likes = current_likes + 1
            
            app.supabase.table("Reviews").update({"likes": new_likes}).filter("review_id", "eq", review_id).execute()
            
            return jsonify({"success": True, "liked": True, "likes": new_likes}), 200
            
    except Exception as e:
        print(f"Error liking review: {str(e)}")
        return jsonify({"success": False, "message": str(e)}), 500

@app.route("/delete-review/<review_id>", methods=["POST"])
@login_required
def delete_review(review_id):
    """Delete a review"""
    try:
        # Get user info
        user_id = session.get("user_id")
        
        # Initialize Supabase if not already done
        init_supabase()
        
        # Check if the review exists and belongs to the current user
        review_response = app.supabase.table("Reviews").select("*").filter("review_id", "eq", review_id).filter("user_id", "eq", user_id).execute()
        
        if not hasattr(review_response, 'data') or not review_response.data:
            return jsonify({"success": False, "message": "Review not found or you don't have permission to delete it"}), 404
        
        try:
            # Delete all likes for this review
            app.supabase.table("ReviewLikes").delete().filter("review_id", "eq", review_id).execute()
        except Exception as likes_error:
            print(f"Error deleting review likes: {str(likes_error)}")
            # Continue even if deleting likes fails
        
        # Delete the review
        app.supabase.table("Reviews").delete().filter("review_id", "eq", review_id).filter("user_id", "eq", user_id).execute()
        
        # Note: UserActivities table doesn't exist, so we're skipping activity deletion
        
        return jsonify({"success": True}), 200
            
    except Exception as e:
        print(f"Error deleting review: {str(e)}")
        return jsonify({"success": False, "message": str(e)}), 500


@app.route("/logout")
def logout():
    # Clear the session
    session.clear()
    flash("You have been logged out", "info")
    return redirect(url_for("login"))


@app.route("/")
def home():
    if 'user_id' in session:
        return redirect(url_for("careers"))
    return redirect(url_for("login"))


@app.route("/auth/google/login")
def google_login():
    """
    Initiates the Google OAuth login flow directly
    """
    # Make init_supabase accessible to the google_auth module
    app.init_supabase = init_supabase
    
    return start_google_login()

@app.route("/auth/google/callback")
def google_callback():
    """
    Handles the callback from Google OAuth
    """
    # Make init_supabase accessible to the google_auth module
    app.init_supabase = init_supabase
    
    # Print debug information
    print(f"Callback received with args: {request.args}")
    
    return handle_google_callback(app)

@app.route("/auth/github/login")
def github_login():
    """
    Initiates the GitHub OAuth login flow directly
    """
    # Make init_supabase accessible to the github_auth module
    app.init_supabase = init_supabase
    
    return start_github_login()

@app.route("/auth/github/callback")
def github_callback():
    """
    Handles the callback from GitHub OAuth
    """
    # Make init_supabase accessible to the github_auth module
    app.init_supabase = init_supabase
    
    # Print debug information
    print(f"GitHub callback received with args: {request.args}")
    
    return handle_github_callback(app)

# Route to handle Supabase callback for Google OAuth
@app.route("/supabase-callback")
def supabase_callback():
    """
    Handles the callback from Supabase after Google OAuth
    """
    # Get the access_token and refresh_token from the query parameters
    access_token = request.args.get('access_token')
    refresh_token = request.args.get('refresh_token')
    
    if not access_token:
        flash("Authentication failed: No access token received", "error")
        return redirect(url_for('login'))
    
    # Initialize Supabase
    init_supabase()
    
    try:
        # Get the user data from the access token
        user = app.supabase.auth.get_user(access_token)
        
        if not user or not user.user:
            flash("Failed to retrieve user data", "error")
            return redirect(url_for('login'))
        
        # Get user information
        user_data = user.user
        email = user_data.email
        user_id = user_data.id
        full_name = user_data.user_metadata.get('full_name', email.split('@')[0])
        
        # Check if user exists in our database
        existing_user = app.supabase.table("Users").select("*").filter("email", "eq", email).execute()
        
        if not existing_user.data or len(existing_user.data) == 0:
            # User doesn't exist, create a new user
            new_user = {
                "id": user_id,
                "username": full_name,
                "email": email,
                "password_hash": None,  # No password for OAuth users
                "is_verified": True,  # OAuth users are automatically verified
                "created_at": str(datetime.datetime.now()),
                "auth_provider": "google"
            }
            
            # Insert the new user
            app.supabase.table("Users").insert(new_user).execute()
            
            # Store user info in session
            session['user_id'] = user_id
            session['username'] = full_name
            session['email'] = email
            
            flash("Account created successfully with Google!", "success")
        else:
            # User exists, log them in
            db_user = existing_user.data[0]
            
            # Store user info in session
            session['user_id'] = db_user['id']
            session['username'] = db_user['username']
            session['email'] = db_user['email']
            
            flash("Login successful with Google!", "success")
        
        return redirect(url_for('profile'))
        
    except Exception as e:
        print(f"Error processing authentication: {str(e)}")
        import traceback
        traceback.print_exc()
        flash(f"Error processing authentication: {str(e)}", "error")
        return redirect(url_for('login'))

# Route to handle Supabase callback for GitHub OAuth
@app.route("/auth/v1/callback")
def supabase_github_callback():
    """
    Handles the callback from Supabase after GitHub OAuth
    """
    # Print debug information
    print(f"Supabase GitHub callback received with args: {request.args}")
    
    # Get the code and state from the query parameters
    code = request.args.get('code')
    state = request.args.get('state')
    
    if not code:
        flash("Authentication failed: No authorization code received", "error")
        return redirect(url_for('login'))
    
    # Initialize Supabase
    init_supabase()
    
    try:
        # Exchange the code for an access token
        client_id = os.getenv("GITHUB_CLIENT_ID", "Ov23liWQZyjkDqbYLy8S")
        client_secret = os.getenv("GITHUB_CLIENT_SECRET", "c9c2a3f4e4a0b6c9c2a3f4e4a0b6c9c2a3f4e4a0")
        
        token_url = "https://github.com/login/oauth/access_token"
        token_data = {
            "client_id": client_id,
            "client_secret": client_secret,
            "code": code,
            "redirect_uri": "https://zzmgshrgfkkiciwedzgc.supabase.co/auth/v1/callback"
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
        
        # Check if user exists in our database
        existing_user = app.supabase.table("Users").select("*").filter("email", "eq", email).execute()
        
        if existing_user.data and len(existing_user.data) > 0:
            # User exists, update login information
            user_id = existing_user.data[0]["id"]
            username = existing_user.data[0]["username"]
            
            # Update last login time
            app.supabase.table("Users").update({
                "last_login": str(datetime.datetime.now()),
                "auth_provider": "github"
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

# Handle token exchange from client-side
@app.route("/auth/token", methods=["POST"])
def handle_auth_token():
    """
    Handles the token exchange from the client-side JavaScript
    """
    try:
        # Get the tokens from the request
        data = request.json
        access_token = data.get('access_token')
        refresh_token = data.get('refresh_token')
        provider = data.get('provider')
        
        if not access_token or not refresh_token or not provider:
            return jsonify({"success": False, "error": "Missing required parameters"}), 400
            
        # Initialize Supabase if not already done
        init_supabase()
        
        # Get the user data from the access token
        user = app.supabase.auth.get_user(access_token)
        
        if not user or not user.user:
            return jsonify({"success": False, "error": "Failed to retrieve user data"}), 400
            
        # Get user information
        user_data = user.user
        email = user_data.email
        user_id = user_data.id
        full_name = user_data.user_metadata.get('full_name', email.split('@')[0])
        
        # Check if user exists in our database
        existing_user = app.supabase.table("Users").select("*").filter("email", "eq", email).execute()
        
        if not existing_user.data or len(existing_user.data) == 0:
            # User doesn't exist, create a new user
            new_user = {
                "id": user_id,
                "username": full_name,
                "email": email,
                "password_hash": None,  # No password for OAuth users
                "is_verified": True,  # OAuth users are automatically verified
                "created_at": str(datetime.datetime.now()),
                "auth_provider": provider
            }
            
            # Insert the new user
            app.supabase.table("Users").insert(new_user).execute()
            
            # Store user info in session
            session['user_id'] = user_id
            session['username'] = full_name
            session['email'] = email
            
            message = "Account created successfully!"
        else:
            # User exists, check if this is a verification from profile
            if 'verification_user_id' in session:
                verification_user_id = session.pop('verification_user_id')
                
                # Update the user's auth_provider to the provider
                app.supabase.table("Users").update({"auth_provider": provider}).filter("id", "eq", verification_user_id).execute()
                
                message = "Account verified successfully!"
            else:
                # Otherwise, log them in normally
                db_user = existing_user.data[0]
                
                # Store user info in session
                session['user_id'] = db_user['id']
                session['username'] = db_user['username']
                session['email'] = db_user['email']
                
                message = "Login successful!"
                
        return jsonify({
            "success": True,
            "message": message,
            "redirect_url": url_for('profile')
        })
        
    except Exception as e:
        print(f"Error handling auth token: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500

# Simplified route for Google login
@app.route("/google-login")
def google_login_redirect():
    return redirect(url_for('google_login'))
    
# Simplified route for GitHub login
@app.route("/github-login")
def github_login_redirect():
    return redirect(url_for('github_login'))
    
# Simplified route for Google authentication from profile
@app.route("/verify-with-google")
@login_required
def verify_with_google():
    # Store the user's ID before redirecting
    user_id = session.get('user_id')
    session['verification_user_id'] = user_id
    return redirect(url_for('google_login'))

# Simplified route for GitHub authentication from profile
@app.route("/verify-with-github")
@login_required
def verify_with_github():
    # Store the user's ID before redirecting
    user_id = session.get('user_id')
    session['verification_user_id'] = user_id
    return redirect(url_for('github_login'))

# Route for news page
@app.route("/news")
@login_required
def news():
    news_data = load_news_data()
    return render_template(
        "news.html", 
        news_items=news_data.get('articles', []), 
        last_updated=news_data.get('last_updated')
    )

# Route for reporting bugs
@app.route("/report-bugs")
def report_bugs():
    # Redirect to email client with pre-filled email
    bug_email = "adhyottech@gmail.com"
    subject = "CareerMate Bug Report"
    body = "Please describe the bug you encountered:"
    
    # Create mailto link with subject and body
    mailto_link = f"mailto:{bug_email}?subject={subject}&body={body}"
    
    return redirect(mailto_link)

@app.route("/tools")
@login_required
def tools():
    """Tools page with career tools"""
    return render_template("tools.html")

@app.route("/pricing")
def pricing():
    """Pricing page with subscription plans"""
    # Get the user's current plan for the career test
    user_plan = "free"
    if 'user_id' in session:
        user_plan = get_feature_tier("career_test")
    
    return render_template("pricing.html", user_plan=user_plan)

if __name__ == "__main__":
    # Initialize Supabase when running the app directly
    try:
        init_supabase()
        print("Supabase client initialized successfully")
    except Exception as e:
        print(f"Warning: Failed to initialize Supabase client: {str(e)}")
        print("The application will continue, but database operations may fail")
    
    # Start the news updater in a background thread
    try:
        start_news_updater()
        print("News updater started in background thread")
    except Exception as e:
        print(f"Warning: Failed to start news updater: {str(e)}")
        print("The application will continue, but news may not be updated automatically")
    
    # Subscription Management Routes
    @app.route("/subscriptions")
    @login_required
    def subscriptions():
        """
        Display the user's subscriptions and available premium features
        """
        # Get user's active subscriptions
        active_subscriptions = get_user_active_subscriptions()
        
        # Get user's subscriptions (for checking which features are already subscribed)
        user_subscriptions = get_user_subscriptions()
        
        return render_template(
            "subscriptions.html",
            active_subscriptions=active_subscriptions,
            available_features=FEATURES,
            user_subscriptions=user_subscriptions
        )
    
    @app.route("/feature/<feature_id>")
    @login_required
    def compare_feature_tiers(feature_id):
        """
        Display comparison between free and premium tiers for a specific feature
        """
        # Check if feature exists
        if feature_id not in FEATURES:
            flash("Feature not found", "error")
            return redirect(url_for("subscriptions"))
        
        # Get feature comparison data
        comparison = get_feature_comparison(feature_id)
        
        # Get user's tier for this feature
        user_tier = get_feature_tier(feature_id)
        
        return render_template(
            "feature_comparison.html",
            comparison=comparison,
            user_tier=user_tier
        )
    
    @app.route("/purchase/<feature_id>")
    @login_required
    def purchase_feature_subscription(feature_id):
        """
        Purchase a premium subscription for a specific feature
        """
        # Check if feature exists
        if feature_id not in FEATURES:
            flash("Feature not found", "error")
            return redirect(url_for("subscriptions"))
        
        # Purchase the feature
        result = purchase_feature(feature_id)
        
        if result["success"]:
            flash(f"Congratulations! You've upgraded to {result['feature_name']} Premium.", "success")
        else:
            flash(f"Error: {result.get('message', 'An error occurred during purchase.')}", "error")
        
        # Redirect to the feature comparison page
        return redirect(url_for("compare_feature_tiers", feature_id=feature_id))
    
    @app.route("/cancel/<feature_id>")
    @login_required
    def cancel_feature_subscription(feature_id):
        """
        Cancel a premium subscription for a specific feature
        """
        # Check if feature exists
        if feature_id not in FEATURES:
            flash("Feature not found", "error")
            return redirect(url_for("subscriptions"))
        
        # Cancel the subscription
        success = cancel_subscription(feature_id)
        
        if success:
            flash(f"Your subscription to {FEATURES[feature_id]['name']} Premium has been canceled.", "success")
        else:
            flash("Error: You don't have an active subscription for this feature.", "error")
        
        # Redirect to the subscriptions page
        return redirect(url_for("subscriptions"))
    
    @app.route("/downgrade/<feature_id>")
    @login_required
    def downgrade_feature(feature_id):
        """
        Downgrade a premium feature to the free tier
        """
        # Same as canceling
        return cancel_feature_subscription(feature_id)
        
    # Career Test Routes
    @app.route("/career-test-plans")
    @login_required
    def career_test_plans():
        """
        Display the career test plans comparison page
        """
        # Redirect to the feature comparison page for career test
        return redirect(url_for("compare_feature_tiers", feature_id="career_test"))
    
    @app.route("/career-test")
    @login_required
    def career_test():
        """
        Display the career fit test page
        """
        # Get the user's tier for the career test feature
        plan_type = get_feature_tier("career_test")
        
        # Get test questions based on plan type
        questions = get_test_questions(plan_type)
        
        return render_template(
            "career_test.html", 
            questions=questions, 
            plan_type=plan_type
        )
    
    @app.route("/submit-career-test", methods=["POST"])
    @login_required
    def submit_career_test():
        """
        Process career test submission and show results
        """
        # Get user ID from session
        user_id = session.get('user_id')
        
        if not user_id:
            flash("You must be logged in to take the career test", "error")
            return redirect(url_for("login"))
        
        # Get the user's tier for the career test feature
        plan_type = get_feature_tier("career_test")
        
        # Get form data (answers to test questions)
        answers = {}
        for key, value in request.form.items():
            # Only process question IDs (p1, p2, i1, etc.)
            if key.startswith(('p', 'i', 's', 'v')) and len(key) <= 3:
                answers[key] = value
        
        # Calculate career matches based on plan type
        results = calculate_career_matches(answers, plan_type)
        
        # Get personality insights based on plan type
        personality_insights = get_personality_insights(answers, plan_type)
        
        # Save test results to database
        try:
            # Initialize Supabase if not already done
            init_supabase()
            
            # Save results
            result_id, result_data = save_test_results(
                user_id, 
                answers, 
                results, 
                personality_insights, 
                plan_type
            )
            
            # Store in Supabase
            app.supabase.table("CareerTestResults").insert({
                "id": result_id,
                "user_id": user_id,
                "answers": json.dumps(answers),
                "results": json.dumps(results),
                "personality_insights": json.dumps(personality_insights),
                "plan_type": plan_type,
                "created_at": str(datetime.datetime.now())
            }).execute()
            
            # Add to user activities
            app.supabase.table("UserActivities").insert({
                "id": str(uuid.uuid4()),
                "user_id": user_id,
                "activity_type": "career_test",
                "content": f"Completed the Career Fit Test ({plan_type.title()} Plan)",
                "created_at": str(datetime.datetime.now())
            }).execute()
            
            # Store top result in session for easy access
            if results and len(results) > 0:
                session['top_career_match'] = results[0].get('title', results[0].get('category_title', 'Unknown'))
                session['top_career_percentage'] = results[0]['match_percentage']
            
        except Exception as e:
            print(f"Error saving test results: {str(e)}")
            # Continue to show results even if saving fails
        
        # Generate PDF report for premium users
        pdf_report_path = None
        if plan_type == "premium" and check_feature_access("career_test", "downloadable_report"):
            try:
                # Get user data for the report
                user_data = {
                    "user_id": user_id,
                    "username": session.get('username', 'User'),
                    "email": session.get('email', '')
                }
                
                # Generate the PDF report
                pdf_report_path = generate_pdf_report(
                    user_data, 
                    results, 
                    personality_insights
                )
            except Exception as e:
                print(f"Error generating PDF report: {str(e)}")
                # Continue without PDF if generation fails
        
        # Show results page
        return render_template(
            "career_test_results.html", 
            results=results,
            personality_insights=personality_insights,
            plan_type=plan_type,
            pdf_report_path=pdf_report_path
        )
    
    @app.route("/career-test-history")
    @login_required
    def career_test_history():
        """
        Show history of user's career test results
        """
        user_id = session.get('user_id')
        
        if not user_id:
            flash("You must be logged in to view your test history", "error")
            return redirect(url_for("login"))
        
        # Get the user's tier for the career test feature
        plan_type = get_feature_tier("career_test")
        
        # Check if progress tracking is available
        progress_tracking = check_feature_access("career_test", "progress_tracking")
        
        # Initialize Supabase if not already done
        init_supabase()
        
        # Get test history
        try:
            # Initialize test_history as an empty list
            test_history = []
            
            # Try to get results from Supabase
            try:
                results = app.supabase.table("CareerTestResults").select("*").filter("user_id", "eq", user_id).order("created_at", desc=True).execute()
                
                if results and hasattr(results, 'data') and results.data:
                    for result in results.data:
                        try:
                            # Parse the results JSON
                            parsed_results = []
                            if result.get("results"):
                                try:
                                    parsed_results = json.loads(result.get("results", "[]"))
                                except json.JSONDecodeError:
                                    parsed_results = []
                            
                            top_matches = []
                            
                            if parsed_results and len(parsed_results) > 0:
                                # Get top matches (limit based on plan)
                                match_limit = 3 if plan_type == "premium" else 2
                                for match in parsed_results[:match_limit]:
                                    title = match.get("title", match.get("category_title", "Unknown"))
                                    top_matches.append({
                                        "title": title,
                                        "match_percentage": match.get("match_percentage", 0)
                                    })
                            
                            # Format the date
                            try:
                                if isinstance(result.get("created_at"), str):
                                    created_at = datetime.datetime.fromisoformat(result["created_at"].replace('Z', '+00:00'))
                                else:
                                    created_at = result.get("created_at", datetime.datetime.now())
                            except (ValueError, TypeError):
                                created_at = datetime.datetime.now()
                            
                            # Get the test's plan type
                            test_plan_type = result.get("plan_type", "free")
                            
                            test_history.append({
                                "id": result.get("id"),
                                "created_at": created_at,
                                "top_matches": top_matches,
                                "plan_type": test_plan_type
                            })
                        except Exception as item_error:
                            print(f"Error processing test history item: {str(item_error)}")
                            continue
            except Exception as db_error:
                print(f"Database error retrieving test history: {str(db_error)}")
                # Continue with empty test_history
            
            # Render the template with whatever data we have
            return render_template(
                "career_test_history.html", 
                test_history=test_history,
                plan_type=plan_type,
                progress_tracking=progress_tracking
            )
            
        except Exception as e:
            print(f"Error retrieving test history: {str(e)}")
            flash("An error occurred while retrieving your test history", "error")
            return redirect(url_for("profile"))
            
    @app.route("/download-report/<result_id>")
    @login_required
    def download_report(result_id):
        """
        Download a PDF report of a career test result (premium users only)
        """
        user_id = session.get('user_id')
        
        if not user_id:
            flash("You must be logged in to download reports", "error")
            return redirect(url_for("login"))
        
        # Check if user has premium access to downloadable reports
        if not check_feature_access("career_test", "downloadable_report"):
            flash("PDF reports are only available to Career Test Premium subscribers", "error")
            return redirect(url_for("compare_feature_tiers", feature_id="career_test"))
        
        # Initialize Supabase if not already done
        init_supabase()
        
        try:
            # Get the test result
            result = app.supabase.table("CareerTestResults").select("*").filter("id", "eq", result_id).filter("user_id", "eq", user_id).execute()
            
            if not result.data or len(result.data) == 0:
                flash("Test result not found", "error")
                return redirect(url_for("career_test_history"))
            
            # Parse the result data
            test_data = result.data[0]
            results = json.loads(test_data.get("results", "[]"))
            personality_insights = json.loads(test_data.get("personality_insights", "[]"))
            
            # Get user data for the report
            user_data = {
                "user_id": user_id,
                "username": session.get('username', 'User'),
                "email": session.get('email', '')
            }
            
            # Generate the PDF report
            pdf_report_path = generate_pdf_report(
                user_data, 
                results, 
                personality_insights
            )
            
            if pdf_report_path and os.path.exists(pdf_report_path):
                # In a real implementation, this would return the PDF file
                # For our implementation, we'll serve the text file
                report_filename = os.path.basename(pdf_report_path)
                report_url = url_for('static', filename=f'reports/{report_filename}')
                
                flash(f"Your report has been generated and is ready for download", "success")
                return redirect(report_url)
            else:
                flash("An error occurred while generating your report", "error")
                return redirect(url_for("career_test_history"))
            
        except Exception as e:
            print(f"Error generating PDF report: {str(e)}")
            flash("An error occurred while generating your PDF report", "error")
            return redirect(url_for("career_test_history"))
    
    # Only run the app directly when this file is executed directly (not imported)
    port = int(os.environ.get("PORT", 5001))
    app.run(host='0.0.0.0', port=port, debug=False)
