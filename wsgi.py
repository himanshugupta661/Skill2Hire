"""
WSGI Entry point for production deployment on Render / Gunicorn.
"""
import os
from app import create_app

# Default to production if FLASK_ENV not explicitly set
env = os.environ.get('FLASK_ENV', 'production')
app = create_app(env)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5001))
    app.run(host="0.0.0.0", port=port)
