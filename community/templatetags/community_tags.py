import os
from django import template
from community.models import CommunityProfile

register = template.Library()


@register.filter
def community_avatar(user):
    """Return the community profile avatar URL for a user, or None if not set."""
    try:
        profile = user.community_profile
        if profile.avatar:
            return profile.avatar.url
    except (CommunityProfile.DoesNotExist, AttributeError):
        pass
    return None


@register.filter
def basename(value):
    """Extract file name from a path or name."""
    if not value:
        return ''
    return os.path.basename(str(value))
