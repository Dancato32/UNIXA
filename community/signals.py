"""
Signals for the community app.

Responsibilities:
  - Keep denormalized like_count / comment_count in sync on Post.
  - Create Notification records for ALL in-app events.
  - All operations are atomic-safe (post_save / post_delete).
"""

from django.db.models import F
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from community.models import (
    Comment,
    CommentLike,
    CommunityMembership,
    CustomCommunityMembership,
    Follow,
    Friendship,
    Message,
    Notification,
    Post,
    PostLike,
)


# ── PostLike → update Post.like_count + notify ────────────────────────────────

@receiver(post_save, sender=PostLike)
def on_post_like(sender, instance, created, **kwargs):
    if created:
        Post.objects.filter(pk=instance.post_id).update(like_count=F('like_count') + 1)
        if instance.user != instance.post.author:
            Notification.objects.get_or_create(
                recipient=instance.post.author,
                actor=instance.user,
                type=Notification.TYPE_LIKE,
                post=instance.post,
            )


@receiver(post_delete, sender=PostLike)
def on_post_unlike(sender, instance, **kwargs):
    Post.objects.filter(pk=instance.post_id).update(like_count=F('like_count') - 1)


# ── Comment → update Post.comment_count + notify ─────────────────────────────

@receiver(post_save, sender=Comment)
def on_comment(sender, instance, created, **kwargs):
    if created:
        Post.objects.filter(pk=instance.post_id).update(comment_count=F('comment_count') + 1)
        if instance.parent:
            # Reply — notify parent comment author
            if instance.author != instance.parent.author:
                Notification.objects.create(
                    recipient=instance.parent.author,
                    actor=instance.author,
                    type=Notification.TYPE_REPLY,
                    post=instance.post,
                    comment=instance,
                )
        else:
            # Top-level comment — notify post author
            if instance.author != instance.post.author:
                Notification.objects.create(
                    recipient=instance.post.author,
                    actor=instance.author,
                    type=Notification.TYPE_COMMENT,
                    post=instance.post,
                    comment=instance,
                )


@receiver(post_delete, sender=Comment)
def on_comment_delete(sender, instance, **kwargs):
    Post.objects.filter(pk=instance.post_id).update(comment_count=F('comment_count') - 1)


# ── CommentLike → update Comment.like_count + notify ─────────────────────────

@receiver(post_save, sender=CommentLike)
def on_comment_like(sender, instance, created, **kwargs):
    if created:
        Comment.objects.filter(pk=instance.comment_id).update(like_count=F('like_count') + 1)
        if instance.user != instance.comment.author:
            Notification.objects.create(
                recipient=instance.comment.author,
                actor=instance.user,
                type=Notification.TYPE_COMMENT_LIKE,
                post=instance.comment.post,
                comment=instance.comment,
            )


@receiver(post_delete, sender=CommentLike)
def on_comment_unlike(sender, instance, **kwargs):
    Comment.objects.filter(pk=instance.comment_id).update(like_count=F('like_count') - 1)


# ── Follow → notify ───────────────────────────────────────────────────────────

@receiver(post_save, sender=Follow)
def on_follow(sender, instance, created, **kwargs):
    if created:
        Notification.objects.get_or_create(
            recipient=instance.following,
            actor=instance.follower,
            type=Notification.TYPE_FOLLOW,
        )


# ── Friendship → notify on request + accept ──────────────────────────────────

@receiver(post_save, sender=Friendship)
def on_friendship_change(sender, instance, created, **kwargs):
    if created:
        # New friend request — notify recipient
        Notification.objects.get_or_create(
            recipient=instance.recipient,
            actor=instance.requester,
            type=Notification.TYPE_FRIEND_REQUEST,
            defaults={},
        )
    else:
        # Status changed to accepted — notify requester
        if instance.status == Friendship.STATUS_ACCEPTED:
            Notification.objects.get_or_create(
                recipient=instance.requester,
                actor=instance.recipient,
                type=Notification.TYPE_FRIEND_ACCEPTED,
                defaults={},
            )


# ── Message → notify recipient of new DM ─────────────────────────────────────

@receiver(post_save, sender=Message)
def on_new_message(sender, instance, created, **kwargs):
    if not created:
        return
    # Skip empty messages (no content, no media, no voice)
    if not instance.content and not instance.voice_note and not instance.media:
        return
    # Get all participants except the sender
    try:
        recipient_ids = (
            instance.conversation.participants
            .exclude(id=instance.sender_id)
            .values_list('id', flat=True)
        )
        for rid in recipient_ids:
            # Delete any existing unread message notification from this sender
            # to this recipient so we don't spam — keep only the latest
            Notification.objects.filter(
                recipient_id=rid,
                actor=instance.sender,
                type=Notification.TYPE_MESSAGE,
                is_read=False,
            ).delete()
            Notification.objects.create(
                recipient_id=rid,
                actor=instance.sender,
                type=Notification.TYPE_MESSAGE,
                conversation=instance.conversation,
            )
    except Exception as e:
        import logging
        logging.getLogger(__name__).warning('on_new_message signal error: %s', e)


# ── CommunityMembership → notify community creator on join ───────────────────

@receiver(post_save, sender=CommunityMembership)
def on_school_join(sender, instance, created, **kwargs):
    if created:
        # Notify the first admin/creator — use the community itself as context
        # School communities don't have a single creator, so skip
        pass


@receiver(post_save, sender=CustomCommunityMembership)
def on_custom_community_join(sender, instance, created, **kwargs):
    if created and instance.community.creator and instance.user != instance.community.creator:
        Notification.objects.create(
            recipient=instance.community.creator,
            actor=instance.user,
            type=Notification.TYPE_JOIN,
        )


# ── Auto-create Personal Workspace on user registration ──────────────────────

from django.contrib.auth import get_user_model as _get_user_model

def _create_personal_workspace(sender, instance, created, **kwargs):
    """Auto-create MyNexa workspace for every new user — the single personal hub."""
    if not created:
        return
    try:
        from community.models import GroupWorkspace, WorkspaceMember
        nexa_ws = GroupWorkspace.objects.create(
            name='MyNexa',
            description='Your personal command center. All tools, drafts, and actions live here.',
            workspace_type=GroupWorkspace.TYPE_NEXA,
            privacy=GroupWorkspace.PRIVACY_PRIVATE,
            owner=instance,
            is_personal=True,
        )
        WorkspaceMember.objects.create(
            workspace=nexa_ws,
            user=instance,
            role=WorkspaceMember.ROLE_OWNER,
        )
    except Exception as e:
        import logging
        logging.getLogger(__name__).warning('MyNexa workspace creation failed: %s', e)


def _connect_user_signal():
    User = _get_user_model()
    post_save.connect(_create_personal_workspace, sender=User, weak=False)

_connect_user_signal()
