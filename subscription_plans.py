# subscription_plans.py
# Handles subscription plan features and restrictions for CareerMate

import os
import json
import datetime
import uuid
from flask import session

# Feature definitions
FEATURES = {
    # Career Test Features
    "career_test": {
        "name": "Career Fit Test",
        "free_tier": {
            "test_questions_limit": 20,  # Limit to 20 questions for free plan
            "career_matches_limit": 2,   # Show only 2 career matches
            "personality_insights_limit": 3,  # Show only 3 personality traits
            "role_suggestions_limit": 3,  # Show only 3 generic roles
            "skill_gap_analysis": False,  # No detailed skill gap analysis
            "progress_tracking": False,   # No progress tracking
            "downloadable_report": False  # No PDF report
        },
        "premium_tier": {
            "name": "Career Fit Test Premium",
            "price": 4.99,  # Monthly price in USD
            "test_questions_limit": 60,  # Up to 60 questions for premium plan
            "career_matches_limit": 10,  # Show up to 10 career matches
            "personality_insights_limit": None,  # Show all personality insights
            "role_suggestions_limit": 10,  # Show 10+ specific roles
            "skill_gap_analysis": True,   # Detailed skill gap analysis
            "progress_tracking": True,    # Progress tracking available
            "downloadable_report": True   # PDF report available
        }
    },
    
    # Resume Builder Features
    "resume_builder": {
        "name": "Resume Builder",
        "free_tier": {
            "templates_limit": 2,  # Limit to 2 basic templates
            "sections_limit": 5,   # Limit to 5 sections
            "download_formats": ["PDF"],  # Only PDF download
            "ai_suggestions": False,  # No AI suggestions
            "ats_optimization": False  # No ATS optimization
        },
        "premium_tier": {
            "name": "Resume Builder Premium",
            "price": 3.99,  # Monthly price in USD
            "templates_limit": None,  # Unlimited templates
            "sections_limit": None,   # Unlimited sections
            "download_formats": ["PDF", "DOCX", "TXT"],  # Multiple download formats
            "ai_suggestions": True,   # AI-powered content suggestions
            "ats_optimization": True  # ATS optimization and scoring
        }
    },
    
    # Job Tracker Features
    "job_tracker": {
        "name": "Job Application Tracker",
        "free_tier": {
            "applications_limit": 10,  # Limit to 10 job applications
            "reminders": False,        # No reminders
            "notes_limit": 1,          # 1 note per application
            "status_tracking": True,   # Basic status tracking
            "analytics": False         # No analytics
        },
        "premium_tier": {
            "name": "Job Tracker Premium",
            "price": 2.99,  # Monthly price in USD
            "applications_limit": None,  # Unlimited job applications
            "reminders": True,           # Email/notification reminders
            "notes_limit": None,         # Unlimited notes
            "status_tracking": True,     # Advanced status tracking
            "analytics": True            # Application analytics and insights
        }
    },
    
    # Interview Prep Features
    "interview_prep": {
        "name": "Interview Preparation",
        "free_tier": {
            "practice_questions_limit": 20,  # Limit to 20 practice questions
            "mock_interviews": False,        # No mock interviews
            "ai_feedback": False,            # No AI feedback
            "company_specific": False        # No company-specific prep
        },
        "premium_tier": {
            "name": "Interview Prep Premium",
            "price": 4.99,  # Monthly price in USD
            "practice_questions_limit": None,  # Unlimited practice questions
            "mock_interviews": True,           # AI-powered mock interviews
            "ai_feedback": True,               # Detailed AI feedback
            "company_specific": True           # Company-specific interview prep
        }
    }
}

def get_user_subscriptions(user_id=None):
    """
    Get the user's current feature subscriptions
    
    Args:
        user_id: User ID (optional, defaults to current session user)
        
    Returns:
        Dictionary of feature subscriptions
    """
    if user_id is None:
        user_id = session.get('user_id')
    
    # In a real implementation, this would query the database
    # For demonstration, we'll use session variables
    subscriptions = session.get('subscriptions', {})
    
    return subscriptions

def check_feature_access(feature_id, setting_name, user_id=None):
    """
    Check if a user has premium access to a specific feature setting
    
    Args:
        feature_id: ID of the feature (e.g., 'career_test')
        setting_name: Name of the setting to check (e.g., 'test_questions_limit')
        user_id: User ID (optional, defaults to current session user)
        
    Returns:
        The value for the setting based on user's subscription status
    """
    if user_id is None:
        user_id = session.get('user_id')
    
    # Get user subscriptions
    subscriptions = get_user_subscriptions(user_id)
    
    # Check if user has premium access to this feature
    has_premium = feature_id in subscriptions and subscriptions[feature_id].get('active', False)
    
    # Get the appropriate tier settings
    if has_premium:
        tier = "premium_tier"
    else:
        tier = "free_tier"
    
    # Return the setting value
    if feature_id in FEATURES and setting_name in FEATURES[feature_id][tier]:
        return FEATURES[feature_id][tier][setting_name]
    
    # Default to False if setting not found
    return False

def get_feature_tier(feature_id, user_id=None):
    """
    Get the user's tier for a specific feature
    
    Args:
        feature_id: ID of the feature (e.g., 'career_test')
        user_id: User ID (optional, defaults to current session user)
        
    Returns:
        String 'premium' or 'free'
    """
    if user_id is None:
        user_id = session.get('user_id')
    
    # Get user subscriptions
    subscriptions = get_user_subscriptions(user_id)
    
    # Check if user has premium access to this feature
    if feature_id in subscriptions and subscriptions[feature_id].get('active', False):
        return "premium"
    else:
        return "free"

def get_feature_comparison(feature_id):
    """
    Get a comparison of free vs premium tiers for a specific feature
    
    Args:
        feature_id: ID of the feature (e.g., 'career_test')
        
    Returns:
        Dictionary with feature comparison data
    """
    if feature_id not in FEATURES:
        return None
    
    feature = FEATURES[feature_id]
    free_tier = feature["free_tier"]
    premium_tier = feature["premium_tier"]
    
    # Create comparison data based on the feature
    if feature_id == "career_test":
        comparison = {
            "feature_id": feature_id,
            "feature_name": feature["name"],
            "tiers": [
                {
                    "name": "Free Tier",
                    "price": 0,
                    "features": [
                        {"name": "Test Questions", "value": f"Basic test ({free_tier['test_questions_limit']} questions)"},
                        {"name": "Career Fit %", "value": f"{free_tier['career_matches_limit']} general suggestions (e.g., \"Technology\", \"Arts\")"},
                        {"name": "Personality Type", "value": "Simple type (e.g., \"Creative Thinker\")"},
                        {"name": "Role Match Suggestions", "value": f"{free_tier['role_suggestions_limit']} generic roles (e.g., \"Software Developer\")"},
                        {"name": "Skill Gap Overview", "value": "Generic skill suggestions (e.g., \"Improve communication\")"},
                        {"name": "Progress Tracking", "value": "❌ Not available"},
                        {"name": "Downloadable PDF Report", "value": "❌ Not available"}
                    ]
                },
                {
                    "name": premium_tier["name"],
                    "price": premium_tier["price"],
                    "features": [
                        {"name": "Test Questions", "value": f"Full psychometric test ({premium_tier['test_questions_limit']} questions)"},
                        {"name": "Career Fit %", "value": f"Detailed breakdown: Top {premium_tier['career_matches_limit']} career fits with % match"},
                        {"name": "Personality Type", "value": "In-depth report: MBTI-style or Big Five + strengths/weaknesses"},
                        {"name": "Role Match Suggestions", "value": f"{premium_tier['role_suggestions_limit']}+ specific roles with descriptions, salary ranges, and fit scores"},
                        {"name": "Skill Gap Overview", "value": "Personalized gap analysis: current skills vs required, with suggestions/tools to improve"},
                        {"name": "Progress Tracking", "value": "✅ Track improvements over time after retaking tests"},
                        {"name": "Downloadable PDF Report", "value": "✅ Beautiful, branded PDF report for college/job applications"}
                    ]
                }
            ]
        }
    elif feature_id == "resume_builder":
        comparison = {
            "feature_id": feature_id,
            "feature_name": feature["name"],
            "tiers": [
                {
                    "name": "Free Tier",
                    "price": 0,
                    "features": [
                        {"name": "Templates", "value": f"{free_tier['templates_limit']} basic templates"},
                        {"name": "Sections", "value": f"Limited to {free_tier['sections_limit']} sections"},
                        {"name": "Download Formats", "value": ", ".join(free_tier['download_formats'])},
                        {"name": "AI Content Suggestions", "value": "❌ Not available"},
                        {"name": "ATS Optimization", "value": "❌ Not available"}
                    ]
                },
                {
                    "name": premium_tier["name"],
                    "price": premium_tier["price"],
                    "features": [
                        {"name": "Templates", "value": "Unlimited premium templates"},
                        {"name": "Sections", "value": "Unlimited customizable sections"},
                        {"name": "Download Formats", "value": ", ".join(premium_tier['download_formats'])},
                        {"name": "AI Content Suggestions", "value": "✅ Smart suggestions for skills and achievements"},
                        {"name": "ATS Optimization", "value": "✅ ATS-friendly formatting and keyword optimization"}
                    ]
                }
            ]
        }
    elif feature_id == "job_tracker":
        comparison = {
            "feature_id": feature_id,
            "feature_name": feature["name"],
            "tiers": [
                {
                    "name": "Free Tier",
                    "price": 0,
                    "features": [
                        {"name": "Job Applications", "value": f"Track up to {free_tier['applications_limit']} applications"},
                        {"name": "Status Tracking", "value": "Basic application status tracking"},
                        {"name": "Notes", "value": f"{free_tier['notes_limit']} note per application"},
                        {"name": "Reminders", "value": "❌ Not available"},
                        {"name": "Analytics", "value": "❌ Not available"}
                    ]
                },
                {
                    "name": premium_tier["name"],
                    "price": premium_tier["price"],
                    "features": [
                        {"name": "Job Applications", "value": "Unlimited job application tracking"},
                        {"name": "Status Tracking", "value": "Advanced status tracking with timeline"},
                        {"name": "Notes", "value": "Unlimited notes and attachments"},
                        {"name": "Reminders", "value": "✅ Email and notification reminders for follow-ups"},
                        {"name": "Analytics", "value": "✅ Application insights and success rate analytics"}
                    ]
                }
            ]
        }
    elif feature_id == "interview_prep":
        comparison = {
            "feature_id": feature_id,
            "feature_name": feature["name"],
            "tiers": [
                {
                    "name": "Free Tier",
                    "price": 0,
                    "features": [
                        {"name": "Practice Questions", "value": f"{free_tier['practice_questions_limit']} common interview questions"},
                        {"name": "Mock Interviews", "value": "❌ Not available"},
                        {"name": "AI Feedback", "value": "❌ Not available"},
                        {"name": "Company-Specific Prep", "value": "❌ Not available"}
                    ]
                },
                {
                    "name": premium_tier["name"],
                    "price": premium_tier["price"],
                    "features": [
                        {"name": "Practice Questions", "value": "Unlimited industry-specific questions"},
                        {"name": "Mock Interviews", "value": "✅ AI-powered mock interviews with real-time feedback"},
                        {"name": "AI Feedback", "value": "✅ Detailed analysis of your responses and improvement suggestions"},
                        {"name": "Company-Specific Prep", "value": "✅ Tailored preparation for specific companies"}
                    ]
                }
            ]
        }
    else:
        # Generic comparison for other features
        comparison = {
            "feature_id": feature_id,
            "feature_name": feature["name"],
            "tiers": [
                {
                    "name": "Free Tier",
                    "price": 0,
                    "features": [{"name": "Basic Features", "value": "Limited functionality"}]
                },
                {
                    "name": premium_tier["name"],
                    "price": premium_tier["price"],
                    "features": [{"name": "Premium Features", "value": "Full functionality"}]
                }
            ]
        }
    
    return comparison

def purchase_feature(feature_id, user_id=None):
    """
    Purchase premium access to a specific feature
    
    Args:
        feature_id: ID of the feature to purchase (e.g., 'career_test')
        user_id: User ID (optional, defaults to current session user)
        
    Returns:
        Dictionary with purchase information
    """
    if user_id is None:
        user_id = session.get('user_id')
    
    if feature_id not in FEATURES:
        return {"success": False, "message": "Invalid feature ID"}
    
    # Get the feature details
    feature = FEATURES[feature_id]
    premium_tier = feature["premium_tier"]
    
    # In a real implementation, this would handle payment processing
    # and update the user's subscription status in the database
    
    # For demonstration, we'll just update the session
    subscriptions = session.get('subscriptions', {})
    
    # Create a new subscription
    subscription_id = str(uuid.uuid4())
    purchase_date = datetime.datetime.now()
    expiry_date = purchase_date + datetime.timedelta(days=30)  # 30-day subscription
    
    subscriptions[feature_id] = {
        "id": subscription_id,
        "active": True,
        "purchase_date": purchase_date.isoformat(),
        "expiry_date": expiry_date.isoformat(),
        "auto_renew": True,
        "price": premium_tier["price"]
    }
    
    # Update session
    session['subscriptions'] = subscriptions
    
    return {
        "success": True,
        "subscription_id": subscription_id,
        "feature_id": feature_id,
        "feature_name": feature["name"],
        "price": premium_tier["price"],
        "purchase_date": purchase_date.isoformat(),
        "expiry_date": expiry_date.isoformat()
    }

def cancel_subscription(feature_id, user_id=None):
    """
    Cancel a feature subscription
    
    Args:
        feature_id: ID of the feature to cancel (e.g., 'career_test')
        user_id: User ID (optional, defaults to current session user)
        
    Returns:
        Boolean indicating success
    """
    if user_id is None:
        user_id = session.get('user_id')
    
    # Get user subscriptions
    subscriptions = session.get('subscriptions', {})
    
    # Check if user has this subscription
    if feature_id not in subscriptions:
        return False
    
    # Mark as inactive (in a real system, you might keep it active until the end of the billing period)
    subscriptions[feature_id]["active"] = False
    subscriptions[feature_id]["auto_renew"] = False
    
    # Update session
    session['subscriptions'] = subscriptions
    
    return True

def get_user_active_subscriptions(user_id=None):
    """
    Get all active subscriptions for a user
    
    Args:
        user_id: User ID (optional, defaults to current session user)
        
    Returns:
        List of active subscription dictionaries
    """
    if user_id is None:
        user_id = session.get('user_id')
    
    # Get user subscriptions
    subscriptions = session.get('subscriptions', {})
    
    # Filter active subscriptions and add feature details
    active_subscriptions = []
    for feature_id, subscription in subscriptions.items():
        if subscription.get('active', False) and feature_id in FEATURES:
            # Add feature details to subscription
            subscription_with_details = subscription.copy()
            subscription_with_details["feature_id"] = feature_id
            subscription_with_details["feature_name"] = FEATURES[feature_id]["name"]
            subscription_with_details["price"] = FEATURES[feature_id]["premium_tier"]["price"]
            
            active_subscriptions.append(subscription_with_details)
    
    return active_subscriptions