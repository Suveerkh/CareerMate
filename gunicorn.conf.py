import multiprocessing
import os

# Gunicorn configuration for Render deployment

# Bind to 0.0.0.0:$PORT (for Render)
port = os.environ.get("PORT", "8000")
bind = f"0.0.0.0:{port}"

# Number of worker processes - use a reasonable number for Render
workers = 4

# Use threads for concurrency
threads = 2

# Timeout in seconds
timeout = 120

# Access log - writes to stdout by default
accesslog = "-"

# Error log - writes to stderr by default
errorlog = "-"

# Log level
loglevel = "info"

# Preload application code before forking
preload_app = True

# Worker class
worker_class = "sync"