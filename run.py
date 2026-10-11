"""Development entry point for the Tripura Explore application.

Run with:  python run.py
"""
from app import create_app

app = create_app()

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)