#!/usr/bin/env bash
set -o errexit

pip install --upgrade pip
pip install -r requirements.txt

mkdir -p staticfiles
python manage.py collectstatic --no-input
python manage.py migrate
python manage.py createcachetable

# Create superuser automatically if it doesn't exist
python manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
import os
username = os.environ.get('ADMIN_USERNAME', 'admin')
email = os.environ.get('ADMIN_EMAIL', 'admin@nexa.com')
password = os.environ.get('ADMIN_PASSWORD', 'admin1234')
if not User.objects.filter(username=username).exists():
    User.objects.create_superuser(username=username, email=email, password=password)
    print(f'Superuser {username} created.')
else:
    print(f'Superuser {username} already exists.')
"
