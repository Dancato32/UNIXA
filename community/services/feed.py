"""
Feed service — production-ready personalized feed.

Strategy:
  1. Collect IDs of communities the user has joined.
  2. Collect IDs of users the user follows.
  3. Exclude posts from blocked users.
  4. UNION-style query via Q objects — single DB round-trip.
  5. Cursor-based pagination on created_at for infinite scroll.

No N+1 queries: select_related + prefetch_related used throughout.
"""

from django.db.models import Q
from django.utils.dateparse import parse_datetime

from community.models import (
    Block,
    CommunityMembership,
    Follow,
    Post,
)


def get_personalized_feed(user, limit: int = 20, cursor: str | None = None):
    """
    Return a paginated queryset of Post objects for `user`.

    Args:
        user:   Authenticated user instance.
        limit:  Max posts to return (default 20, max 100).
        cursor: ISO-8601 datetime string — return posts older than this.

    Returns:
        dict with keys:
            posts     — QuerySet (already evaluated)
            next_cursor — str or None (pass as `cursor` for next page)
            has_more  — bool
    """
    limit = min(int(limit), 100)

    # 1. Communities the user belongs to
    joined_community_ids = CommunityMembership.objects.filter(
        user=user
    ).values_list('community_id', flat=True)

    # 2. Users the requesting user follows
    followed_user_ids = Follow.objects.filter(
        follower=user
    ).values_list('following_id', flat=True)

    # 3. Users who have blocked this user OR whom this user has blocked
    blocked_ids = Block.objects.filter(
        Q(blocker=user) | Q(blocked=user)
    ).values_list('blocker_id', 'blocked_id')
    # Flatten to a set of user IDs to exclude
    excluded_author_ids = set()
    for blocker_id, blocked_id in blocked_ids:
        excluded_author_ids.add(blocker_id)
        excluded_author_ids.add(blocked_id)
    excluded_author_ids.discard(user.pk)  # never exclude self

    # 4. Build the base queryset — single query via OR
    feed_filter = (
        Q(school_community_id__in=joined_community_ids)
        | Q(custom_community_id__in=joined_community_ids)
        | Q(author_id__in=followed_user_ids)
        | Q(is_ai_generated=True)
        | Q(feed_only=True)
    )

    qs = (
        Post.objects.filter(feed_filter, is_deleted=False)
        .exclude(author_id__in=excluded_author_ids)
        .select_related('author', 'school_community', 'custom_community')
        .prefetch_related('likes')
        .order_by('-created_at')
        .distinct()
    )

    # 5. Cursor pagination
    if cursor:
        cursor_dt = parse_datetime(cursor)
        if cursor_dt:
            qs = qs.filter(created_at__lt=cursor_dt)

    # Fetch limit + 1 to determine has_more
    posts = list(qs[: limit + 1])
    has_more = len(posts) > limit
    if has_more:
        posts = posts[:limit]

    next_cursor = None
    if has_more and posts:
        next_cursor = posts[-1].created_at.isoformat()

    return {
        'posts': posts,
        'next_cursor': next_cursor,
        'has_more': has_more,
    }
