"""
Simple rate limiting decorator for Django function-based views.
Uses Django's cache backend — no extra packages needed.
"""
import time
from functools import wraps
from django.core.cache import cache
from django.http import JsonResponse


def rate_limit(requests=30, window=3600, scope='default'):
    """
    Decorator: limit to `requests` calls per `window` seconds per user.
    Returns 429 JSON if exceeded.
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return view_func(request, *args, **kwargs)

            key = f'rl:{scope}:{request.user.id}'
            now = int(time.time())
            window_start = now - window

            # Get existing timestamps
            timestamps = cache.get(key, [])
            # Keep only timestamps within the current window
            timestamps = [t for t in timestamps if t > window_start]

            if len(timestamps) >= requests:
                retry_after = window - (now - timestamps[0])
                return JsonResponse(
                    {
                        'error': 'Rate limit exceeded. Please slow down.',
                        'retry_after_seconds': max(0, retry_after),
                    },
                    status=429
                )

            timestamps.append(now)
            cache.set(key, timestamps, timeout=window)
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


# Pre-configured decorators for common use cases
ai_rate_limit = rate_limit(requests=30, window=3600, scope='ai')          # 30/hour
upload_rate_limit = rate_limit(requests=20, window=3600, scope='upload')  # 20/hour
chat_rate_limit = rate_limit(requests=60, window=3600, scope='chat')      # 60/hour
essay_rate_limit = rate_limit(requests=10, window=3600, scope='essay')    # 10/hour
