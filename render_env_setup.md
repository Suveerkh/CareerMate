# Render Environment Setup Guide

## Environment Variables to Set in Render

When deploying to Render, you need to set these environment variables in your Render dashboard:

### Required Environment Variables:

1. **RENDER=true** - This tells the app it's running on Render
2. **RENDER_EXTERNAL_HOSTNAME=your-app-name.onrender.com** - Replace with your actual Render app URL
3. **SECRET_KEY=your-secret-key-here** - Generate a secure secret key
4. **GOOGLE_CLIENT_ID=your-google-client-id** - From Google Cloud Console
5. **GOOGLE_CLIENT_SECRET=your-google-client-secret** - From Google Cloud Console
6. **GITHUB_CLIENT_ID=your-github-client-id** - From GitHub OAuth App
7. **GITHUB_CLIENT_SECRET=your-github-client-secret** - From GitHub OAuth App
8. **SUPABASE_URL=your-supabase-url** - Your Supabase project URL
9. **SUPABASE_KEY=your-supabase-anon-key** - Your Supabase anon key
10. **MAIL_USERNAME=your-email@gmail.com** - For sending emails
11. **MAIL_PASSWORD=your-app-password** - Gmail app password
12. **NEWS_API_KEY=your-news-api-key** - For news fetching (optional)

### OAuth Configuration Updates Needed:

#### Google OAuth (Google Cloud Console):
1. Go to https://console.cloud.google.com/
2. Navigate to APIs & Services > Credentials
3. Find your OAuth 2.0 Client ID
4. Add these Authorized redirect URIs:
   - `https://your-app-name.onrender.com/auth/google/callback`
   - `https://your-app-name.onrender.com/supabase/callback`

#### GitHub OAuth (GitHub Settings):
1. Go to GitHub Settings > Developer settings > OAuth Apps
2. Find your OAuth App
3. Update Authorization callback URL to:
   - `https://your-app-name.onrender.com/auth/github/callback`

### Render IP Addresses:
The IP addresses you mentioned (13.228.225.19, 18.142.128.26, 54.254.162.138) are Render's outbound IP addresses. You may need to whitelist these in:
- Supabase (if you have IP restrictions)
- Any external APIs that require IP whitelisting
- Email service providers (if they have IP restrictions)

### Steps to Deploy:
1. Set all environment variables in Render dashboard
2. Update OAuth redirect URIs in Google and GitHub
3. Deploy your app
4. Test OAuth flows
5. Monitor logs for any issues

### Troubleshooting:
- Check Render logs for detailed error messages
- Verify all environment variables are set correctly
- Ensure OAuth redirect URIs match exactly
- Test with a simple endpoint first before testing OAuth