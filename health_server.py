from flask import Flask, jsonify, render_template_string, request
import datetime
import os

app = Flask(__name__)

# HTML template for the health check page
HEALTH_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CareerMate - Server Health</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            background-color: #f5f5f5;
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
            margin: 0;
            color: #333;
        }
        .health-container {
            text-align: center;
            padding: 40px;
            background-color: white;
            border-radius: 10px;
            box-shadow: 0 4px 10px rgba(0, 0, 0, 0.1);
            max-width: 500px;
        }
        h1 {
            color: #4285f4;
            margin-bottom: 20px;
        }
        .status {
            font-size: 18px;
            margin-bottom: 20px;
            color: #0f9d58;
            font-weight: bold;
        }
        .timestamp {
            font-size: 14px;
            color: #666;
        }
    </style>
</head>
<body>
    <div class="health-container">
        <h1>CareerMate Server</h1>
        <div class="status">Status: {{ status }}</div>
        <p>{{ message }}</p>
        <div class="timestamp">Last updated: {{ timestamp }}</div>
    </div>
</body>
</html>
"""

@app.route('/')
@app.route('/health')
def health_check():
    """Health check endpoint for the desktop app with HTML response."""
    data = {
        "status": "OK",
        "message": "Server is running correctly",
        "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    # Return HTML for browser requests, JSON for API requests
    if 'application/json' in request.headers.get('Accept', ''):
        return jsonify(data)
    else:
        return render_template_string(HEALTH_HTML, **data)

if __name__ == "__main__":
    import argparse
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='CareerMate Health Check Server')
    parser.add_argument('--port', type=int, default=5001, help='Port to run the server on')
    args = parser.parse_args()
    
    print(f"Starting health check server on port {args.port}")
    app.run(host='0.0.0.0', port=args.port, debug=False)