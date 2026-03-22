"""
Campus app views — Live Campus hub + all 6 feature endpoints.
All JSON endpoints use simple JsonResponse (no DRF overhead for speed).
"""
import json
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.utils import timezone
from django.views.decorators.http import require_POST, require_GET

from community.models import CommunityMembership, SchoolCommunity
from campus.models import (
    Confession, ConfessionReply, ConfessionUpvote,
    HelpBeacon, PulseActivity, PulseJoin,
    SkillDeal, SkillListing,
    Startup, StartupFollow, StartupMember, StartupSupportInterest, StartupUpdate,
    UserReputation, VoiceRoom, VoiceRoomParticipant,
)

User = get_user_model()


# ─────────────────────────────────────────────────────────────────────────────
# LIVE CAMPUS HUB
# ─────────────────────────────────────────────────────────────────────────────

@login_required
def live_campus(request):
    """Main Live Campus page — unified hub for all 6 features."""
    school_ids = CommunityMembership.objects.filter(
        user=request.user
    ).values_list('community_id', flat=True)

    # Pulse: live activities (not expired)
    pulse = PulseActivity.objects.filter(
        expires_at__gt=timezone.now(),
        is_private=False,
    ).select_related('host', 'host__community_profile').order_by('-created_at')[:20]

    # Help beacons: open, urgent first
    beacons = HelpBeacon.objects.filter(
        status=HelpBeacon.STATUS_OPEN,
    ).select_related('requester', 'requester__community_profile').order_by(
        '-urgency', '-created_at'
    )[:10]

    # Voice rooms: open
    voice_rooms = VoiceRoom.objects.filter(
        status=VoiceRoom.STATUS_OPEN,
        ended_at__isnull=True,
    ).select_related('host', 'host__community_profile').order_by('-created_at')[:10]

    # Startups: active, recruiting
    startups = Startup.objects.filter(
        is_active=True, is_recruiting=True,
    ).select_related('founder', 'founder__community_profile').order_by('-created_at')[:8]

    # Skill requests: open
    skill_requests = SkillListing.objects.filter(
        listing_type=SkillListing.TYPE_REQUEST,
        status=SkillListing.STATUS_OPEN,
    ).select_related('user', 'user__community_profile').order_by('-created_at')[:8]

    # User's school for filtering
    my_school = None
    if school_ids:
        try:
            my_school = SchoolCommunity.objects.filter(id__in=school_ids).first()
        except Exception:
            pass

    return render(request, 'campus/live_campus.html', {
        'pulse': pulse,
        'beacons': beacons,
        'voice_rooms': voice_rooms,
        'startups': startups,
        'skill_requests': skill_requests,
        'my_school': my_school,
        'active_tab': request.GET.get('tab', 'pulse'),
    })


# ─────────────────────────────────────────────────────────────────────────────
# SKILL MARKETPLACE
# ─────────────────────────────────────────────────────────────────────────────

@login_required
def skill_marketplace(request):
    """Skill marketplace browse page."""
    tag = request.GET.get('tag', '')
    listing_type = request.GET.get('type', '')
    qs = SkillListing.objects.filter(status=SkillListing.STATUS_OPEN).select_related(
        'user', 'user__community_profile', 'school_community'
    )
    if tag:
        qs = qs.filter(skill_tag=tag)
    if listing_type in (SkillListing.TYPE_OFFER, SkillListing.TYPE_REQUEST):
        qs = qs.filter(listing_type=listing_type)
    listings = qs.order_by('-created_at')[:40]
    return render(request, 'campus/skill_marketplace.html', {
        'listings': listings,
        'skill_tags': SkillListing._meta.get_field('skill_tag').choices,
        'active_tag': tag,
        'active_type': listing_type,
    })


@login_required
@require_POST
def skill_listing_create(request):
    data = json.loads(request.body)
    listing = SkillListing.objects.create(
        user=request.user,
        listing_type=data.get('listing_type', SkillListing.TYPE_OFFER),
        title=data['title'][:200],
        description=data.get('description', '')[:1000],
        skill_tag=data.get('skill_tag', 'other'),
        exchange_for=data.get('exchange_for', '')[:200],
        urgency=data.get('urgency', SkillListing.URGENCY_LOW),
    )
    return JsonResponse({'ok': True, 'id': str(listing.id)})


@login_required
@require_POST
def skill_deal_propose(request, listing_id):
    listing = get_object_or_404(SkillListing, id=listing_id, status=SkillListing.STATUS_OPEN)
    if listing.user == request.user:
        return JsonResponse({'ok': False, 'error': 'Cannot deal with yourself'}, status=400)
    data = json.loads(request.body)
    deal, created = SkillDeal.objects.get_or_create(
        initiator=request.user,
        listing=listing,
        defaults={
            'receiver': listing.user,
            'message': data.get('message', '')[:500],
        }
    )
    return JsonResponse({'ok': True, 'deal_id': str(deal.id), 'created': created})


@login_required
@require_POST
def skill_deal_respond(request, deal_id):
    deal = get_object_or_404(SkillDeal, id=deal_id, receiver=request.user)
    data = json.loads(request.body)
    action = data.get('action')
    if action == 'accept':
        deal.status = SkillDeal.STATUS_ACTIVE
        deal.listing.status = SkillListing.STATUS_MATCHED
        deal.listing.save(update_fields=['status'])
    elif action == 'reject':
        deal.status = SkillDeal.STATUS_CANCELLED
    elif action == 'complete':
        deal.status = SkillDeal.STATUS_DONE
        deal.listing.status = SkillListing.STATUS_DONE
        deal.listing.save(update_fields=['status'])
    deal.save(update_fields=['status', 'updated_at'])
    return JsonResponse({'ok': True, 'status': deal.status})


@login_required
@require_POST
def skill_deal_rate(request, deal_id):
    deal = get_object_or_404(SkillDeal, id=deal_id, status=SkillDeal.STATUS_DONE)
    data = json.loads(request.body)
    rating = max(1, min(5, int(data.get('rating', 5))))
    review = data.get('review', '')[:300]
    if deal.initiator == request.user:
        deal.initiator_rating = rating
        deal.initiator_review = review
        deal.save(update_fields=['initiator_rating', 'initiator_review'])
    elif deal.receiver == request.user:
        deal.receiver_rating = rating
        deal.receiver_review = review
        deal.save(update_fields=['receiver_rating', 'receiver_review'])
    return JsonResponse({'ok': True})


# ─────────────────────────────────────────────────────────────────────────────
# CONFESSION FEED
# ─────────────────────────────────────────────────────────────────────────────

@login_required
def confession_feed(request):
    category = request.GET.get('cat', '')
    sort = request.GET.get('sort', 'new')
    qs = Confession.objects.filter(status=Confession.STATUS_VISIBLE).prefetch_related('replies')
    if category:
        qs = qs.filter(category=category)
    if sort == 'top':
        qs = qs.order_by('-upvote_count', '-created_at')
    else:
        qs = qs.order_by('-created_at')
    confessions = qs[:30]
    # Annotate with user's upvote status
    upvoted_ids = set(
        ConfessionUpvote.objects.filter(
            user=request.user, confession__in=confessions
        ).values_list('confession_id', flat=True)
    )
    return render(request, 'campus/confession_feed.html', {
        'confessions': confessions,
        'upvoted_ids': upvoted_ids,
        'categories': Confession.CATEGORY_CHOICES,
        'active_cat': category,
        'active_sort': sort,
    })


@login_required
@require_POST
def confession_create(request):
    data = json.loads(request.body)
    content = data.get('content', '').strip()
    if not content or len(content) < 10:
        return JsonResponse({'ok': False, 'error': 'Too short'}, status=400)
    # Basic crisis keyword detection
    crisis_words = ['suicide', 'kill myself', 'end my life', 'self harm', 'hurt myself']
    is_crisis = any(w in content.lower() for w in crisis_words)
    confession = Confession.objects.create(
        author=request.user,
        content=content[:2000],
        category=data.get('category', Confession.CAT_OTHER),
        is_crisis=is_crisis,
    )
    return JsonResponse({'ok': True, 'id': str(confession.id), 'is_crisis': is_crisis})


@login_required
@require_POST
def confession_upvote(request, confession_id):
    confession = get_object_or_404(Confession, id=confession_id, status=Confession.STATUS_VISIBLE)
    obj, created = ConfessionUpvote.objects.get_or_create(user=request.user, confession=confession)
    if not created:
        obj.delete()
        Confession.objects.filter(pk=confession_id).update(upvote_count=max(0, confession.upvote_count - 1))
        return JsonResponse({'ok': True, 'upvoted': False, 'count': confession.upvote_count - 1})
    Confession.objects.filter(pk=confession_id).update(upvote_count=confession.upvote_count + 1)
    return JsonResponse({'ok': True, 'upvoted': True, 'count': confession.upvote_count + 1})


@login_required
@require_POST
def confession_reply_create(request, confession_id):
    confession = get_object_or_404(Confession, id=confession_id, status=Confession.STATUS_VISIBLE)
    data = json.loads(request.body)
    content = data.get('content', '').strip()
    if not content:
        return JsonResponse({'ok': False, 'error': 'Empty reply'}, status=400)
    reply = ConfessionReply.objects.create(
        confession=confession,
        author=request.user,
        content=content[:1000],
        is_anonymous=data.get('is_anonymous', False),
    )
    Confession.objects.filter(pk=confession_id).update(reply_count=confession.reply_count + 1)
    return JsonResponse({'ok': True, 'id': str(reply.id)})


@login_required
@require_POST
def confession_mark_helpful(request, reply_id):
    reply = get_object_or_404(ConfessionReply, id=reply_id, confession__author=request.user)
    reply.is_helpful = not reply.is_helpful
    reply.save(update_fields=['is_helpful'])
    return JsonResponse({'ok': True, 'helpful': reply.is_helpful})


# ─────────────────────────────────────────────────────────────────────────────
# STARTUP COMMAND CENTER
# ─────────────────────────────────────────────────────────────────────────────

@login_required
def startup_list(request):
    startups = Startup.objects.filter(is_active=True).select_related(
        'founder', 'founder__community_profile'
    ).prefetch_related('members').order_by('-created_at')[:30]
    followed_ids = set(
        StartupFollow.objects.filter(user=request.user).values_list('startup_id', flat=True)
    )
    return render(request, 'campus/startup_list.html', {
        'startups': startups,
        'followed_ids': followed_ids,
    })


@login_required
def startup_detail(request, startup_id):
    startup = get_object_or_404(Startup, id=startup_id, is_active=True)
    updates = startup.updates.select_related('author', 'author__community_profile').order_by('-created_at')[:20]
    members = startup.members.filter(status=StartupMember.STATUS_ACTIVE).select_related('user', 'user__community_profile')
    is_following = StartupFollow.objects.filter(user=request.user, startup=startup).exists()
    is_member = StartupMember.objects.filter(startup=startup, user=request.user, status=StartupMember.STATUS_ACTIVE).exists()
    return render(request, 'campus/startup_detail.html', {
        'startup': startup,
        'updates': updates,
        'members': members,
        'is_following': is_following,
        'is_member': is_member,
    })


@login_required
@require_POST
def startup_create(request):
    data = json.loads(request.body)
    startup = Startup.objects.create(
        founder=request.user,
        name=data['name'][:200],
        tagline=data.get('tagline', '')[:300],
        description=data.get('description', ''),
        industry=data.get('industry', '')[:100],
        stage=data.get('stage', Startup.STAGE_IDEA),
        looking_for=data.get('looking_for', '')[:500],
    )
    # Founder is automatically a member
    StartupMember.objects.create(
        startup=startup, user=request.user,
        role=StartupMember.ROLE_FOUNDER, status=StartupMember.STATUS_ACTIVE,
    )
    # Auto-create pulse entry
    PulseActivity.objects.create(
        host=request.user,
        activity_type=PulseActivity.TYPE_STARTUP,
        title=f'🚀 New startup: {startup.name}',
        description=startup.tagline or startup.description[:200],
        startup=startup,
        expires_at=timezone.now() + timedelta(days=7),
    )
    return JsonResponse({'ok': True, 'id': str(startup.id)})


@login_required
@require_POST
def startup_follow_toggle(request, startup_id):
    startup = get_object_or_404(Startup, id=startup_id)
    obj, created = StartupFollow.objects.get_or_create(user=request.user, startup=startup)
    if not created:
        obj.delete()
        Startup.objects.filter(pk=startup_id).update(follower_count=max(0, startup.follower_count - 1))
        return JsonResponse({'ok': True, 'following': False, 'count': startup.follower_count - 1})
    Startup.objects.filter(pk=startup_id).update(follower_count=startup.follower_count + 1)
    return JsonResponse({'ok': True, 'following': True, 'count': startup.follower_count + 1})


@login_required
@require_POST
def startup_post_update(request, startup_id):
    startup = get_object_or_404(Startup, id=startup_id)
    if not StartupMember.objects.filter(startup=startup, user=request.user, status=StartupMember.STATUS_ACTIVE).exists():
        return JsonResponse({'ok': False, 'error': 'Not a member'}, status=403)
    data = json.loads(request.body)
    update = StartupUpdate.objects.create(
        startup=startup,
        author=request.user,
        content=data['content'][:2000],
        milestone=data.get('milestone', '')[:200],
    )
    return JsonResponse({'ok': True, 'id': str(update.id)})


@login_required
@require_POST
def startup_apply(request, startup_id):
    startup = get_object_or_404(Startup, id=startup_id, is_recruiting=True)
    data = json.loads(request.body)
    member, created = StartupMember.objects.get_or_create(
        startup=startup, user=request.user,
        defaults={'role': data.get('role', StartupMember.ROLE_OTHER), 'status': StartupMember.STATUS_PENDING},
    )
    return JsonResponse({'ok': True, 'created': created})


@login_required
@require_POST
def startup_support_interest(request, startup_id):
    startup = get_object_or_404(Startup, id=startup_id)
    data = json.loads(request.body)
    interest, created = StartupSupportInterest.objects.get_or_create(
        user=request.user, startup=startup,
        interest_type=data.get('interest_type', StartupSupportInterest.TYPE_COLLABORATOR),
        defaults={'message': data.get('message', '')[:500]},
    )
    return JsonResponse({'ok': True, 'created': created})


# ─────────────────────────────────────────────────────────────────────────────
# CAMPUS PULSE
# ─────────────────────────────────────────────────────────────────────────────

@login_required
@require_GET
def pulse_feed(request):
    """JSON feed of live activities for polling."""
    activity_type = request.GET.get('type', '')
    qs = PulseActivity.objects.filter(
        expires_at__gt=timezone.now(), is_private=False,
    ).select_related('host', 'host__community_profile', 'voice_room', 'help_beacon', 'startup')
    if activity_type:
        qs = qs.filter(activity_type=activity_type)
    activities = []
    for a in qs.order_by('-created_at')[:30]:
        try:
            avatar = a.host.community_profile.avatar.url if a.host.community_profile.avatar else None
        except Exception:
            avatar = None
        activities.append({
            'id': str(a.id),
            'type': a.activity_type,
            'type_label': a.get_activity_type_display(),
            'title': a.title,
            'description': a.description,
            'location': a.location_name,
            'host': a.host.username,
            'host_avatar': avatar,
            'participants': a.participant_count,
            'expires_at': a.expires_at.isoformat(),
            'lat': float(a.latitude) if a.latitude else None,
            'lng': float(a.longitude) if a.longitude else None,
            'voice_room_id': str(a.voice_room_id) if a.voice_room_id else None,
            'beacon_id': str(a.help_beacon_id) if a.help_beacon_id else None,
            'startup_id': str(a.startup_id) if a.startup_id else None,
        })
    return JsonResponse({'activities': activities})


@login_required
@require_POST
def pulse_create(request):
    data = json.loads(request.body)
    hours = min(int(data.get('duration_hours', 2)), 24)
    activity = PulseActivity.objects.create(
        host=request.user,
        activity_type=data.get('activity_type', PulseActivity.TYPE_STUDY),
        title=data['title'][:200],
        description=data.get('description', '')[:500],
        location_name=data.get('location_name', '')[:200],
        latitude=data.get('lat') or None,
        longitude=data.get('lng') or None,
        max_participants=int(data.get('max_participants', 0)),
        is_private=data.get('is_private', False),
        expires_at=timezone.now() + timedelta(hours=hours),
    )
    return JsonResponse({'ok': True, 'id': str(activity.id)})


@login_required
@require_POST
def pulse_join(request, activity_id):
    activity = get_object_or_404(PulseActivity, id=activity_id)
    if activity.expires_at < timezone.now():
        return JsonResponse({'ok': False, 'error': 'Expired'}, status=400)
    join, created = PulseJoin.objects.get_or_create(user=request.user, activity=activity)
    if created:
        PulseActivity.objects.filter(pk=activity_id).update(
            participant_count=activity.participant_count + 1
        )
    return JsonResponse({'ok': True, 'joined': created})


# ─────────────────────────────────────────────────────────────────────────────
# VOICE ROOMS
# ─────────────────────────────────────────────────────────────────────────────

@login_required
def voice_rooms(request):
    rooms = VoiceRoom.objects.filter(
        status=VoiceRoom.STATUS_OPEN, ended_at__isnull=True,
    ).select_related('host', 'host__community_profile').prefetch_related('participants').order_by('-created_at')
    return render(request, 'campus/voice_rooms.html', {'rooms': rooms})


@login_required
@require_POST
def voice_room_create(request):
    data = json.loads(request.body)
    room = VoiceRoom.objects.create(
        host=request.user,
        topic=data['topic'][:200],
        max_participants=int(data.get('max_participants', 20)),
        is_low_bandwidth=data.get('low_bandwidth', False),
    )
    VoiceRoomParticipant.objects.create(room=room, user=request.user)
    return JsonResponse({'ok': True, 'room_id': str(room.id)})


@login_required
@require_POST
def voice_room_join(request, room_id):
    room = get_object_or_404(VoiceRoom, id=room_id, status=VoiceRoom.STATUS_OPEN)
    participant, created = VoiceRoomParticipant.objects.get_or_create(
        room=room, user=request.user,
        defaults={'left_at': None},
    )
    if created:
        VoiceRoom.objects.filter(pk=room_id).update(participant_count=room.participant_count + 1)
    return JsonResponse({'ok': True, 'joined': created, 'topic': room.topic})


@login_required
@require_POST
def voice_room_leave(request, room_id):
    room = get_object_or_404(VoiceRoom, id=room_id)
    VoiceRoomParticipant.objects.filter(room=room, user=request.user).update(left_at=timezone.now())
    VoiceRoom.objects.filter(pk=room_id).update(
        participant_count=max(0, room.participant_count - 1)
    )
    # Auto-close if empty
    remaining = VoiceRoomParticipant.objects.filter(room=room, left_at__isnull=True).count()
    if remaining == 0:
        VoiceRoom.objects.filter(pk=room_id).update(
            status=VoiceRoom.STATUS_CLOSED, ended_at=timezone.now()
        )
    return JsonResponse({'ok': True})


@login_required
@require_POST
def voice_room_close(request, room_id):
    room = get_object_or_404(VoiceRoom, id=room_id, host=request.user)
    room.status = VoiceRoom.STATUS_CLOSED
    room.ended_at = timezone.now()
    room.save(update_fields=['status', 'ended_at'])
    return JsonResponse({'ok': True})


@login_required
@require_GET
def voice_room_participants(request, room_id):
    room = get_object_or_404(VoiceRoom, id=room_id)
    participants = VoiceRoomParticipant.objects.filter(
        room=room, left_at__isnull=True
    ).select_related('user', 'user__community_profile')
    data = []
    for p in participants:
        try:
            avatar = p.user.community_profile.avatar.url if p.user.community_profile.avatar else None
        except Exception:
            avatar = None
        data.append({
            'username': p.user.username,
            'display_name': getattr(getattr(p.user, 'community_profile', None), 'display_name', '') or p.user.username,
            'avatar': avatar,
            'is_muted': p.is_muted,
            'is_host': p.user_id == room.host_id,
        })
    return JsonResponse({'participants': data, 'status': room.status, 'topic': room.topic})


# ─────────────────────────────────────────────────────────────────────────────
# HELP BEACON
# ─────────────────────────────────────────────────────────────────────────────

@login_required
def help_beacon_list(request):
    beacons = HelpBeacon.objects.filter(
        status=HelpBeacon.STATUS_OPEN,
    ).select_related('requester', 'requester__community_profile').order_by(
        '-urgency', '-created_at'
    )[:30]
    return render(request, 'campus/help_beacons.html', {
        'beacons': beacons,
        'categories': HelpBeacon.CATEGORY_CHOICES,
    })


@login_required
@require_POST
def help_beacon_create(request):
    data = json.loads(request.body)
    title = data.get('title', '').strip()
    if not title:
        return JsonResponse({'ok': False, 'error': 'Title required'}, status=400)
    urgency = data.get('urgency', HelpBeacon.URGENCY_MEDIUM)
    deadline_map = {
        HelpBeacon.URGENCY_HIGH: timedelta(hours=1),
        HelpBeacon.URGENCY_MEDIUM: timedelta(hours=2),
        HelpBeacon.URGENCY_LOW: timedelta(hours=24),
    }
    beacon = HelpBeacon.objects.create(
        requester=request.user,
        title=title[:200],
        description=data.get('description', '')[:1000],
        category=data.get('category', HelpBeacon.CAT_OTHER),
        urgency=urgency,
        help_mode=data.get('help_mode', HelpBeacon.MODE_EITHER),
        deadline=timezone.now() + deadline_map.get(urgency, timedelta(hours=2)),
    )
    return JsonResponse({'ok': True, 'id': str(beacon.id)})


@login_required
@require_POST
def help_beacon_claim(request, beacon_id):
    beacon = get_object_or_404(HelpBeacon, id=beacon_id, status=HelpBeacon.STATUS_OPEN)
    if beacon.requester == request.user:
        return JsonResponse({'ok': False, 'error': 'Cannot claim your own beacon'}, status=400)
    beacon.helper = request.user
    beacon.status = HelpBeacon.STATUS_CLAIMED
    beacon.save(update_fields=['helper', 'status'])
    return JsonResponse({'ok': True})


@login_required
@require_POST
def help_beacon_resolve(request, beacon_id):
    beacon = get_object_or_404(HelpBeacon, id=beacon_id, requester=request.user)
    data = json.loads(request.body)
    beacon.status = HelpBeacon.STATUS_RESOLVED
    beacon.resolved_at = timezone.now()
    if data.get('rating') and beacon.helper:
        beacon.helper_rating = max(1, min(5, int(data['rating'])))
        beacon.helper_review = data.get('review', '')[:300]
        # Give reputation to helper
        rep, _ = UserReputation.objects.get_or_create(user=beacon.helper)
        rep.help_given += 1
        rep.score += beacon.reputation_reward
        rep.save(update_fields=['help_given', 'score', 'updated_at'])
    beacon.save()
    return JsonResponse({'ok': True})
