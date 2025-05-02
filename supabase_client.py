from supabase import create_client as supabase_create_client

def create_client(supabase_url, supabase_key):
    return supabase_create_client(supabase_url, supabase_key)
