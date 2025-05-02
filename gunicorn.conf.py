import multiprocessing

# Gunicorn configuration for Render deployment

# Bind to 0.0.0.0:$PORT (for Render)
bind = "0.0.0.0:$PORT"

# Number of worker processes
workers = multiprocessing.cpu_count() * 2 + 1

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