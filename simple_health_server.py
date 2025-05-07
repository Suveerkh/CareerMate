from flask import Flask, jsonify
import datetime
import argparse

app = Flask(__name__)

@app.route('/')
@app.route('/health')
def health_check():
    """Simple health check endpoint for the desktop app."""
    data = {
        "status": "ok",
        "message": "Server is running",
        "timestamp": datetime.datetime.now().isoformat()
    }
    
    response = jsonify(data)
    
    # Set no-cache headers
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    
    return response

if __name__ == "__main__":
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Simple Health Check Server')
    parser.add_argument('--port', type=int, default=5001, help='Port to run the server on')
    args = parser.parse_args()
    
    print(f"Starting simple health check server on port {args.port}")
    app.run(host='0.0.0.0', port=args.port, debug=False)