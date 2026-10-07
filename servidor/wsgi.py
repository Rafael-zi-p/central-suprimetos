"""Ponto de entrada do gunicorn:  gunicorn -c gunicorn.conf.py wsgi:app"""
from app import create_app

app = create_app()

if __name__ == "__main__":
    import os
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "3000")))
