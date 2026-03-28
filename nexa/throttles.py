"""
Custom throttle classes for NEXA.
Applied per-view to AI and upload endpoints.
"""
from rest_framework.throttling import UserRateThrottle, AnonRateThrottle


class AIThrottle(UserRateThrottle):
    """30 AI requests per hour per user."""
    scope = 'ai'


class UploadThrottle(UserRateThrottle):
    """20 uploads per hour per user."""
    scope = 'upload'


class AnonThrottle(AnonRateThrottle):
    """20 requests per day for unauthenticated users."""
    scope = 'anon'
