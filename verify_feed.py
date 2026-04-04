import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'nexa.settings')
django.setup()

from community.services.feed import get_personalized_feed
from django.contrib.auth import get_user_model

def test():
    User = get_user_model()
    # Pick a random user to check their feed
    user = User.objects.exclude(username='clutch_ai').first()
    print(f"Checking feed for user: {user.username}")
    
    result = get_personalized_feed(user, limit=5)
    posts = result.get('posts', [])
    print(f"Found {len(posts)} posts in feed.")
    for p in posts:
        print(f"- {p.title} (AI: {p.is_ai_generated})")

if __name__ == '__main__':
    test()
