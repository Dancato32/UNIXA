from celery import shared_task
from django.contrib.auth import get_user_model
from community.models import Post
from community.scrapers import ClutchAIScraper
from django.core.files.base import ContentFile
import requests
import random
import time
import os

User = get_user_model()

# Map opportunity types to banner filenames stored in the artifact folder
BANNER_DIR = os.path.join(
    os.path.expanduser("~"),
    ".gemini", "antigravity", "brain",
    "ed8ca8a4-7899-49c6-97a0-7ae58fb04577",
)

BANNER_FILES = {
    "internship": "internship_banner_1775103478995.png",
    "job": "job_banner_1775103689430.png",
    "generic": "clutch_generic_banner_1775103715966.png",
}


def _load_banner(key):
    """Return (bytes, filename) or (None, None)."""
    filename = BANNER_FILES.get(key, BANNER_FILES["generic"])
    path = os.path.join(BANNER_DIR, filename)
    if os.path.exists(path):
        try:
            with open(path, "rb") as f:
                return f.read(), filename
        except Exception:
            pass
    return None, None


@shared_task
def run_clutch_ai_cycle():
    """
    Fetch real job opportunities from multiple sources and post them
    as Clutch AI every 10 minutes. 
    Tracks heartbeat in cache for UI visibility.
    """
    from django.core.cache import cache
    from django.utils import timezone
    
    print("Starting Clutch AI opportunity discovery cycle...")
    
    # Track this run in cache
    cache.set('clutch_ai_last_run', timezone.now(), timeout=86400)

    # 1. Make sure the bot user exists
    try:
        author = User.objects.get(username="clutch_ai")
    except User.DoesNotExist:
        print("Error: clutch_ai user not found.")
        return
    
    # 2. Fetch live opportunities
    try:
        scraper = ClutchAIScraper()
        opportunities = scraper.fetch_all()
    except Exception as e:
        print(f"Scraper failed: {e}")
        return

    if not opportunities:
        print("No opportunities found this cycle.")
        return

    # 3. Pick a dynamic number of items, prioritized by diversity
    # Shift from purely random to picking more if available
    count = min(len(opportunities), random.randint(5, 10))
    selected = random.sample(opportunities, count)

    posts_created = 0

    for opp in selected:
        # Skip duplicates
        if Post.objects.filter(source_url=opp["url"]).exists():
            continue
        
        # 4. Build post content
        tags_str = " ".join(opp.get("tags", []))
        content = (
            f"{opp['description']}\n\n"
            f"Field: {opp['category']}\n"
            f"Location: {opp['location']}\n"
            f"Deadline: {opp['deadline']}\n\n"
            f"{tags_str}"
        )

        # 5. Map to opportunity type
        title_lower = opp["title"].lower()
        if "internship" in title_lower or "intern" in title_lower:
            opp_type = Post.OPP_INTERNSHIP
            banner_key = "internship"
        elif "freelance" in title_lower or "gig" in title_lower:
            opp_type = Post.OPP_FREELANCE
            banner_key = "generic"
        elif "scholarship" in title_lower:
            opp_type = Post.OPP_SCHOLARSHIP
            banner_key = "generic"
        else:
            opp_type = Post.OPP_JOB
            banner_key = "job"

        # 6. Get media
        media_bytes = None
        media_name = None
        image_url = opp.get("image_url")
        
        if image_url:
            try:
                resp = requests.get(image_url, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
                if resp.status_code == 200 and len(resp.content) > 1000:
                    media_bytes = resp.content
                    media_name = f"clutch_{int(time.time())}.jpg"
            except Exception:
                pass

        if not media_bytes:
            media_bytes, media_name = _load_banner(banner_key)

        # 7. Create post
        try:
            post = Post.objects.create(
                author=author,
                title=opp["title"],
                content=content,
                is_ai_generated=True,
                source_url=opp["url"],
                is_opportunity=True,
                opportunity_type=opp_type,
                feed_only=True,
                media_type="image" if media_bytes else "",
            )
            if media_bytes and media_name:
                post.media.save(media_name, ContentFile(media_bytes), save=True)
            
            posts_created += 1
            time.sleep(random.uniform(0.5, 1.5))
        except Exception:
            continue

    print(f"Clutch AI cycle complete. Created {posts_created} posts.")
    return f"Created {posts_created} posts."
