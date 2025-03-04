#!/usr/bin/env bash
# exit on error
set -o errexit

# Create necessary directories
mkdir -p assets staticfiles

# Install dependencies
pip install -r requirements.txt

# Collect static files
python manage.py collectstatic --noinput

# Run migrations
python manage.py migrate 