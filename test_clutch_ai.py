import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'nexa.settings')
django.setup()

from community.tasks import run_clutch_ai_cycle

def test():
    print("Manually triggering Clutch AI cycle (10min freq + Images)...")
    result = run_clutch_ai_cycle()
    print(f"Result: {result}")

if __name__ == '__main__':
    test()
