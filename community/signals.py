"""
Signals for the community app.

Responsibilities:
  - Keep denormalized like_count / comment_count in sync on Post.
  - Create Notification records on like, comment, and follow events.
  - All operations are atomic-safe (post_save / post_delete).
"""

from django.db.models import F
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from community.models import Comment, CommentLike, Follow, Notification, Post, PostLike


# ── PostLike → update Post.like_count ─────────────────────────────────────────

@receiver(post_save, sender=PostLike)
def increment_like_count(sender, instance, created, **kwargs):
    if created:
        Post.objects.filter(pk=instance.post_id).update(like_count=F('like_count') + 1)
        # Notify post author (skip self-likes)
        if instance.user != instance.post.author:
            Notification.objects.get_or_create(
                recipient=instance.post.author,
                actor=instance.user,
                type=Notification.TYPE_LIKE,
                post=instance.post,
            )


@receiver(post_delete, sender=PostLike)
def decrement_like_count(sender, instance, **kwargs):
    Post.objects.filter(pk=instance.post_id).update(like_count=F('like_count') - 1)


# ── Comment → update Post.comment_count ──────────────────────────────────────

@receiver(post_save, sender=Comment)
def increment_comment_count(sender, instance, created, **kwargs):
    if created:
        Post.objects.filter(pk=instance.post_id).update(comment_count=F('comment_count') + 1)

        if instance.parent:
            # This is a reply — notify the parent comment's author (skip self-replies)
            if instance.author != instance.parent.author:
                Notification.objects.create(
                    recipient=instance.parent.author,
                    actor=instance.author,
                    type=Notification.TYPE_REPLY,
                    post=instance.post,
                    comment=instance,
                )
        else:
            # Top-level comment — notify post author (skip self-comments)
            if instance.author != instance.post.author:
                Notification.objects.create(
                    recipient=instance.post.author,
                    actor=instance.author,
                    type=Notification.TYPE_COMMENT,
                    post=instance.post,
                    comment=instance,
                )


@receiver(post_delete, sender=Comment)
def decrement_comment_count(sender, instance, **kwargs):
    Post.objects.filter(pk=instance.post_id).update(comment_count=F('comment_count') - 1)


# ── CommentLike → update Comment.like_count ───────────────────────────────────

@receiver(post_save, sender=CommentLike)
def increment_comment_like_count(sender, instance, created, **kwargs):
    if created:
        Comment.objects.filter(pk=instance.comment_id).update(like_count=F('like_count') + 1)
        # Notify comment author (skip self-likes)
        if instance.user != instance.comment.author:
            Notification.objects.create(
                recipient=instance.comment.author,
                actor=instance.user,
                type=Notification.TYPE_COMMENT_LIKE,
                post=instance.comment.post,
                comment=instance.comment,
            )


@receiver(post_delete, sender=CommentLike)
def decrement_comment_like_count(sender, instance, **kwargs):
    Comment.objects.filter(pk=instance.comment_id).update(like_count=F('like_count') - 1)


# ── Follow → Notification ─────────────────────────────────────────────────────

@receiver(post_save, sender=Follow)
def notify_on_follow(sender, instance, created, **kwargs):
    if created:
        Notification.objects.create(
            recipient=instance.following,
            actor=instance.follower,
            type=Notification.TYPE_FOLLOW,
        )
