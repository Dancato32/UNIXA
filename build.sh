#!/usr/bin/env bash
# Render build script — runs before the app starts

set -o errexit   # exit on any error

pip install --upgrade pip
pip install -r requirements.txt

# Collect static files into /staticfiles
python manage.py collectstatic --no-input

# Run database migrations
python manage.py migrate
