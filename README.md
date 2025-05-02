# CareerMate

CareerMate is a career guidance platform that helps students and graduates explore career options based on their education level and interests.

## Deployment on Render

This application is configured for deployment on Render.com.

### Deployment Steps

1. Create a new account on [Render](https://render.com/) if you don't have one already.

2. Connect your GitHub repository to Render:
   - Go to the Render dashboard
   - Click "New" and select "Blueprint"
   - Connect your GitHub account and select your CareerMate repository

3. Configure Environment Variables:
   - SUPABASE_URL: Your Supabase project URL
   - SUPABASE_KEY: Your Supabase API key
   - MAIL_SERVER: SMTP server for sending emails (e.g., smtp.gmail.com)
   - MAIL_PORT: SMTP port (e.g., 587)
   - MAIL_USERNAME: Your email username
   - MAIL_PASSWORD: Your email password or app password
   - MAIL_DEFAULT_SENDER: Default sender email address
   - SECRET_KEY: A secure random string for Flask sessions

4. Deploy:
   - Render will automatically detect the render.yaml file and set up your service
   - The deployment will start automatically

### Local Development

To run the application locally:

1. Create a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Create a .env file with the required environment variables.

4. Run the application:
   ```
   python app.py
   ```

The application will be available at http://localhost:5001.