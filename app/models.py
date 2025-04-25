from supabase import create_client

# Supabase client initialization (use the same credentials)
supabase = create_client('your_supabase_url', 'your_supabase_key')

def create_user(username, email, password_hash):
    # Insert new user into the 'users' table
    response = supabase.table('users').insert({
        'username': username,
        'email': email,
        'password_hash': password_hash
    }).execute()
    return response

def get_user_by_email(email):
    # Fetch user by email from the 'users' table
    response = supabase.table('users').select('*').eq('email', email).execute()
    return response.data
