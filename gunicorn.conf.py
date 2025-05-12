from dotenv import load_dotenv

# take environment variables from .env file if it exists
load_dotenv()

bind = "127.0.0.1:8000"
errorlog = "/var/log/gunicorn/error.log"
accesslog = "/var/log/gunicorn/access.log"
workers = 3
timeout = 300
