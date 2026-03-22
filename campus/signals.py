"""
Campus app signals — keep denormalized counts in sync and auto-create
PulseActivity entries when voice rooms or help beacons are created.
"""
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.utils import timezone
from datetime import timedelta

from campus.models import (
    ConfessionUpvote, ConfessionReply, Confession,
    StartupFollow, StartupUpdate,
    VoiceRoom, VoiceRoomParticipant,
    HelpBeacon, PulseActivity,
    SkillDeal, UserReputation,
)


# ── Confession counts ─────────────────────────────────────────────────────────

@receiver(post_save, sender=ConfessionUpvote)
def on_confession_upvote(sender, instance, created, **kwargs):
    if created:
        Confession.objects.filter(pk=instance.confession_id).update(
            upvote_count=instance.confession.upvote_count + 1
        )


@receiver(post_delete, sender=ConfessionUpvote)
def on_confession_unvote(sender, instance, **kwargs):
    Confession.objects.filter(pk=instance.confession_id).update(
        upvote_count=max(0, instance.confession.upvote_count - 1)
    )


@receiver(post_save, sender=ConfessionReply)
def on_confession_reply(sender, instance, created, **kwargs):
    if created:
        Confession.objects.filter(pk=instance.confession_id).update(
            reply_count=instance.confession.reply_count + 1
        )


# ── Startup follower count ────────────────────────────────────────────────────

@receiver(post_save, sender=StartupFollow)
def on_startup_follow(sender, instance, created, **kwargs):
    if created:
        from campus.models import Startup
        Startup.objects.filter(pk=instance.startup_id).update(
            follower_count=instance.startup.follower_count + 1
        )


@receiver(post_delete, sender=StartupFollow)
def on_startup_unfollow(sender, instance, **kwargs):
    from campus.models import Startup
    Startup.objects.filter(pk=instance.startup_id).update(
        follower_count=max(0, instance.startup.follower_count - 1)
    )


# ── Auto-create PulseActivity when VoiceRoom opens ───────────────────────────

@receiver(post_save, sender=VoiceRoom)
def on_voice_room_created(sender, instance, created, **kwargs):
    if created:
        PulseActivity.objects.create(
            host=instance.host,
            activity_type=PulseActivity.TYPE_VOICE_ROOM,
            title=instance.topic,
            description='Voice room — join to listen and talk',
            school_community=instance.school_community,
            voice_room=instance,
            expires_at=timezone.now() + timedelta(hours=3),
        )
    elif instance.status == VoiceRoom.STATUS_CLOSED:
        # Expire the pulse entry when room closes
        PulseActivity.objects.filter(voice_room=instance).update(
            expires_at=timezone.now()
        )


# ── Auto-create PulseActivity when HelpBeacon is posted ──────────────────────

@receiver(post_save, sender=HelpBeacon)
def on_help_beacon_created(sender, instance, created, **kwargs):
    if created:
        deadline = instance.deadline or (timezone.now() + timedelta(hours=2))
        PulseActivity.objects.create(
            host=instance.requester,
            activity_type=PulseActivity.TYPE_HELP,
            title=f'🆘 {instance.title}',
            description=instance.description[:200],
            school_community=instance.school_community,
            help_beacon=instance,
            expires_at=deadline,
        )
    elif instance.status in (HelpBeacon.STATUS_RESOLVED, HelpBeacon.STATUS_EXPIRED):
        PulseActivity.objects.filter(help_beacon=instance).update(
            expires_at=timezone.now()
        )


# ── Reputation updates after deal completion ─────────────────────────────────

@receiver(post_save, sender=SkillDeal)
def on_deal_update(sender, instance, **kwargs):
    if instance.status == SkillDeal.STATUS_DONE:
        for user in [instance.initiator, instance.receiver]:
            rep, _ = UserReputation.objects.get_or_create(user=user)
            rep.deals_completed += 1
            rep.score += 20
            rep.save(update_fields=['deals_completed', 'score', 'updated_at'])
