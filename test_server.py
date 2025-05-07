from flask import Flask, jsonify, request, redirect, url_for, session
import argparse
import traceback
import sys
import os

app = Flask(__name__)

# Enable debug mode to see detailed error messages
app.config['DEBUG'] = True

# Set a secret key for session management
app.secret_key = os.urandom(24)

@app.route('/')
def index():
    try:
        html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>CareerMate Test Server</title>
            <style>
                body {
                    font-family: Arial, sans-serif;
                    margin: 0;
                    padding: 20px;
                    background-color: #f5f5f5;
                }
                .container {
                    max-width: 800px;
                    margin: 0 auto;
                    background-color: white;
                    padding: 20px;
                    border-radius: 5px;
                    box-shadow: 0 2px 5px rgba(0,0,0,0.1);
                }
                h1 {
                    color: #4285f4;
                }
                .status {
                    padding: 10px;
                    background-color: #e6f4ea;
                    border-left: 4px solid #34a853;
                    margin: 20px 0;
                }
                button {
                    background-color: #4285f4;
                    color: white;
                    border: none;
                    padding: 10px 15px;
                    border-radius: 4px;
                    cursor: pointer;
                }
                button:hover {
                    background-color: #3367d6;
                }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>CareerMate Test Server</h1>
                <div class="status">
                    <p><strong>Status:</strong> Server is running correctly</p>
                </div>
                <p>This is a test server for the CareerMate desktop application.</p>
                <p>The server is running and responding to requests.</p>
                <button onclick="checkHealth()">Check Health</button>
                <div id="health-result"></div>
                
                <div style="margin-top: 20px;">
                    <a href="/login"><button>Go to Login Page</button></a>
                    <a href="/careers"><button>Go to Careers Page</button></a>
                </div>
                
                <script>
                    function checkHealth() {
                        fetch('/health')
                            .then(response => response.json())
                            .then(data => {
                                document.getElementById('health-result').innerHTML = 
                                    '<pre>' + JSON.stringify(data, null, 2) + '</pre>';
                            })
                            .catch(error => {
                                document.getElementById('health-result').innerHTML = 
                                    '<pre>Error: ' + error.message + '</pre>';
                            });
                    }
                </script>
            </div>
        </body>
        </html>
        """
        return html
    except Exception as e:
        error_info = {
            'error': str(e),
            'traceback': traceback.format_exc()
        }
        print(f"Error in index route: {error_info}")
        return jsonify(error_info), 500

@app.route('/health')
def health():
    try:
        return jsonify({
            'status': 'ok',
            'message': 'Test server is running'
        })
    except Exception as e:
        error_info = {
            'error': str(e),
            'traceback': traceback.format_exc()
        }
        print(f"Error in health route: {error_info}")
        return jsonify(error_info), 500

@app.route('/login', methods=['GET', 'POST'])
def login():
    try:
        if request.method == 'POST':
            # Simple login logic - any username/password combination works
            username = request.form.get('username')
            password = request.form.get('password')
            
            if username and password:
                # Set session to indicate user is logged in
                session['logged_in'] = True
                session['username'] = username
                
                # Redirect to careers page after login
                return redirect(url_for('careers'))
        
        # Check if user is already logged in
        if session.get('logged_in'):
            return redirect(url_for('careers'))
            
        # Display login form
        html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>CareerMate - Login</title>
            <style>
                body {
                    font-family: Arial, sans-serif;
                    margin: 0;
                    padding: 20px;
                    background-color: #f5f5f5;
                }
                .container {
                    max-width: 500px;
                    margin: 50px auto;
                    background-color: white;
                    padding: 20px;
                    border-radius: 5px;
                    box-shadow: 0 2px 5px rgba(0,0,0,0.1);
                }
                h1 {
                    color: #4285f4;
                    text-align: center;
                }
                .form-group {
                    margin-bottom: 15px;
                }
                label {
                    display: block;
                    margin-bottom: 5px;
                    font-weight: bold;
                }
                input[type="text"], input[type="password"] {
                    width: 100%;
                    padding: 8px;
                    border: 1px solid #ddd;
                    border-radius: 4px;
                    box-sizing: border-box;
                }
                button {
                    background-color: #4285f4;
                    color: white;
                    border: none;
                    padding: 10px 15px;
                    border-radius: 4px;
                    cursor: pointer;
                    width: 100%;
                    font-size: 16px;
                }
                button:hover {
                    background-color: #3367d6;
                }
                .links {
                    text-align: center;
                    margin-top: 20px;
                }
                a {
                    color: #4285f4;
                    text-decoration: none;
                }
                a:hover {
                    text-decoration: underline;
                }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>CareerMate Login</h1>
                <form method="post">
                    <div class="form-group">
                        <label for="username">Username</label>
                        <input type="text" id="username" name="username" required>
                    </div>
                    <div class="form-group">
                        <label for="password">Password</label>
                        <input type="password" id="password" name="password" required>
                    </div>
                    <button type="submit">Login</button>
                </form>
                <div class="links">
                    <a href="/">Back to Home</a>
                </div>
            </div>
        </body>
        </html>
        """
        return html
    except Exception as e:
        error_info = {
            'error': str(e),
            'traceback': traceback.format_exc()
        }
        print(f"Error in login route: {error_info}")
        return jsonify(error_info), 500

@app.route('/careers')
def careers():
    try:
        # Check if user is logged in
        if not session.get('logged_in'):
            return redirect(url_for('login'))
            
        # Display careers page
        username = session.get('username', 'User')
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>CareerMate - Careers</title>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    margin: 0;
                    padding: 20px;
                    background-color: #f5f5f5;
                }}
                .container {{
                    max-width: 800px;
                    margin: 0 auto;
                    background-color: white;
                    padding: 20px;
                    border-radius: 5px;
                    box-shadow: 0 2px 5px rgba(0,0,0,0.1);
                }}
                h1 {{
                    color: #4285f4;
                }}
                .welcome {{
                    padding: 10px;
                    background-color: #e6f4ea;
                    border-left: 4px solid #34a853;
                    margin: 20px 0;
                }}
                .job-card {{
                    border: 1px solid #ddd;
                    border-radius: 4px;
                    padding: 15px;
                    margin-bottom: 15px;
                }}
                .job-title {{
                    font-size: 18px;
                    font-weight: bold;
                    color: #4285f4;
                    margin-top: 0;
                }}
                .job-company {{
                    color: #666;
                    margin-bottom: 10px;
                }}
                button {{
                    background-color: #4285f4;
                    color: white;
                    border: none;
                    padding: 10px 15px;
                    border-radius: 4px;
                    cursor: pointer;
                }}
                button:hover {{
                    background-color: #3367d6;
                }}
                .logout {{
                    text-align: right;
                }}
                a {{
                    color: #4285f4;
                    text-decoration: none;
                }}
                a:hover {{
                    text-decoration: underline;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="logout">
                    <a href="/logout">Logout</a>
                </div>
                <h1>CareerMate Careers</h1>
                <div class="welcome">
                    <p>Welcome, {username}! Here are some job opportunities for you.</p>
                </div>
                
                <div class="job-card">
                    <h3 class="job-title">Software Engineer</h3>
                    <p class="job-company">Google - Mountain View, CA</p>
                    <p>Join our team to develop cutting-edge software solutions that impact millions of users worldwide.</p>
                    <button>Apply Now</button>
                </div>
                
                <div class="job-card">
                    <h3 class="job-title">Data Scientist</h3>
                    <p class="job-company">Microsoft - Redmond, WA</p>
                    <p>Use your analytical skills to extract insights from large datasets and drive business decisions.</p>
                    <button>Apply Now</button>
                </div>
                
                <div class="job-card">
                    <h3 class="job-title">UX Designer</h3>
                    <p class="job-company">Apple - Cupertino, CA</p>
                    <p>Create beautiful and intuitive user experiences for Apple's next generation of products.</p>
                    <button>Apply Now</button>
                </div>
                
                <div style="margin-top: 20px; text-align: center;">
                    <a href="/">Back to Home</a>
                </div>
            </div>
        </body>
        </html>
        """
        return html
    except Exception as e:
        error_info = {
            'error': str(e),
            'traceback': traceback.format_exc()
        }
        print(f"Error in careers route: {error_info}")
        return jsonify(error_info), 500

@app.route('/logout')
def logout():
    try:
        # Clear session
        session.clear()
        return redirect(url_for('login'))
    except Exception as e:
        error_info = {
            'error': str(e),
            'traceback': traceback.format_exc()
        }
        print(f"Error in logout route: {error_info}")
        return jsonify(error_info), 500

if __name__ == '__main__':
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Test Server')
    parser.add_argument('--port', type=int, default=5001, help='Port to run the server on')
    args = parser.parse_args()
    
    port = args.port
    print(f"Starting test server on port {port}")
    
    try:
        app.run(host='0.0.0.0', port=port, debug=True)
    except Exception as e:
        print(f"Error starting server: {str(e)}")
        print(traceback.format_exc())
        sys.exit(1)