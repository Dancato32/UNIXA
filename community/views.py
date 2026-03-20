"""
Template-based views for the community app.
All views require login. No modifications to existing apps.
"""

from django.contrib import messages as django_messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.db import models
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from community.models import (
    Comment,
    CommentLike,
    CommunityMembership,
    CommunityProfile,
    Conversation,
    CustomCommunity,
    CustomCommunityMembership,
    Friendship,
    GroupWorkspace,
    Message,
    Notification,
    Post,
    PostLike,
    SchoolCommunity,
    WorkspaceFile,
    WorkspaceMember,
    WorkspaceMessage,
    WorkspaceTask,
)
from community.services.feed import get_personalized_feed

User = get_user_model()


# ── Feed ──────────────────────────────────────────────────────────────────────

@login_required
def feed(request):
    from django.utils.dateparse import parse_datetime
    cursor = request.GET.get('cursor')
    limit = 20

    # Show ALL posts (global feed) so dummy content is visible to everyone
    qs = (
        Post.objects.filter(is_deleted=False)
        .select_related('author', 'author__community_profile', 'school_community', 'custom_community')
        .order_by('-created_at')
    )
    if cursor:
        cursor_dt = parse_datetime(cursor)
        if cursor_dt:
            qs = qs.filter(created_at__lt=cursor_dt)

    posts = list(qs[:limit + 1])
    has_more = len(posts) > limit
    if has_more:
        posts = posts[:limit]
    next_cursor = posts[-1].created_at.isoformat() if has_more and posts else None

    post_ids = [p.id for p in posts]
    liked_ids = set(
        PostLike.objects.filter(user=request.user, post_id__in=post_ids)
        .values_list('post_id', flat=True)
    )

    school_communities = SchoolCommunity.objects.filter(is_active=True)[:8]
    joined_ids = set(
        CommunityMembership.objects.filter(user=request.user)
        .values_list('community_id', flat=True)
    )
    custom_communities = CustomCommunity.objects.filter(is_active=True).order_by('-created_at')[:5]
    custom_joined_ids = set(
        CustomCommunityMembership.objects.filter(user=request.user)
        .values_list('community_id', flat=True)
    )

    return render(request, 'community/feed.html', {
        'posts': posts,
        'has_more': has_more,
        'next_cursor': next_cursor,
        'liked_ids': liked_ids,
        'school_communities': school_communities,
        'joined_ids': joined_ids,
        'custom_communities': custom_communities,
        'custom_joined_ids': custom_joined_ids,
    })


# ── School Communities ────────────────────────────────────────────────────────

@login_required
def schools(request):
    query = request.GET.get('q', '').strip()
    qs = SchoolCommunity.objects.filter(is_active=True)
    if query:
        qs = qs.filter(Q(name__icontains=query) | Q(description__icontains=query))

    joined_ids = set(
        CommunityMembership.objects.filter(user=request.user)
        .values_list('community_id', flat=True)
    )
    return render(request, 'community/schools.html', {
        'schools': qs,
        'query': query,
        'joined_ids': joined_ids,
    })


@login_required
def school_detail(request, slug):
    community = get_object_or_404(SchoolCommunity, slug=slug, is_active=True)
    is_member = CommunityMembership.objects.filter(
        user=request.user, community=community
    ).exists()

    posts = (
        Post.objects.filter(school_community=community, is_deleted=False)
        .select_related('author', 'author__community_profile')
        .order_by('-created_at')[:30]
    )
    post_ids = [p.id for p in posts]
    liked_ids = set(
        PostLike.objects.filter(user=request.user, post_id__in=post_ids)
        .values_list('post_id', flat=True)
    )
    recent_members = (
        community.memberships.select_related('user').order_by('-joined_at')[:10]
    )
    return render(request, 'community/school_detail.html', {
        'community': community,
        'is_member': is_member,
        'posts': posts,
        'liked_ids': liked_ids,
        'recent_members': recent_members,
    })


@login_required
def school_join(request, slug):
    if request.method == 'POST':
        community = get_object_or_404(SchoolCommunity, slug=slug, is_active=True)
        CommunityMembership.objects.get_or_create(
            user=request.user,
            community=community,
            defaults={'role': CommunityMembership.ROLE_MEMBER},
        )
        django_messages.success(request, f'You joined {community.name}.')
    return redirect('community:school_detail', slug=slug)


@login_required
def school_leave(request, slug):
    if request.method == 'POST':
        community = get_object_or_404(SchoolCommunity, slug=slug)
        CommunityMembership.objects.filter(
            user=request.user, community=community
        ).delete()
        django_messages.success(request, f'You left {community.name}.')
    return redirect('community:school_detail', slug=slug)


# ── Custom Communities ────────────────────────────────────────────────────────

@login_required
def custom_list(request):
    query = request.GET.get('q', '').strip()
    qs = CustomCommunity.objects.filter(
        Q(privacy=CustomCommunity.PRIVACY_PUBLIC) | Q(creator=request.user),
        is_active=True,
    ).order_by('-created_at')
    if query:
        qs = qs.filter(Q(name__icontains=query) | Q(description__icontains=query))
    return render(request, 'community/custom_list.html', {
        'communities': qs,
        'query': query,
    })


@login_required
def custom_create(request):
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        if not name:
            return JsonResponse({'error': 'Name is required.'}, status=400)
        cc = CustomCommunity(
            name=name,
            description=request.POST.get('description', ''),
            privacy=request.POST.get('privacy', 'public'),
            topic=request.POST.get('topic', ''),
            is_mature=request.POST.get('is_mature') == '1',
            rules=request.POST.get('rules', ''),
            creator=request.user,
        )
        if 'logo' in request.FILES:
            cc.logo = request.FILES['logo']
        cc.save()
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'slug': cc.slug, 'name': cc.name})
        return redirect('community:custom_detail', slug=cc.slug)
    return render(request, 'community/custom_create.html')


@login_required
def custom_detail(request, slug):
    community = get_object_or_404(CustomCommunity, slug=slug, is_active=True)
    # Enforce private community access
    if community.privacy == CustomCommunity.PRIVACY_PRIVATE:
        if community.creator != request.user:
            django_messages.error(request, 'This is a private community.')
            return redirect('community:custom_list')

    posts = (
        Post.objects.filter(custom_community=community, is_deleted=False)
        .select_related('author', 'author__community_profile')
        .order_by('-created_at')[:30]
    )
    post_ids = [p.id for p in posts]
    liked_ids = set(
        PostLike.objects.filter(user=request.user, post_id__in=post_ids)
        .values_list('post_id', flat=True)
    )
    return render(request, 'community/custom_detail.html', {
        'community': community,
        'posts': posts,
        'liked_ids': liked_ids,
    })


@login_required
def custom_delete(request, slug):
    community = get_object_or_404(CustomCommunity, slug=slug)
    if community.creator != request.user and not request.user.is_staff:
        return JsonResponse({'error': 'Not allowed.'}, status=403)
    if request.method == 'POST':
        community.is_active = False
        community.save(update_fields=['is_active'])
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'ok': True})
        django_messages.success(request, f'"{community.name}" has been deleted.')
        return redirect('community:custom_list')
    return JsonResponse({'error': 'POST required.'}, status=405)


# ── Posts ─────────────────────────────────────────────────────────────────────

@login_required
def post_create(request):
    # Preselect community from query params
    preselect_sc = request.GET.get('sc', '')
    preselect_cc = request.GET.get('cc', '')

    # Only show communities the user is a member of
    joined_community_ids = CommunityMembership.objects.filter(
        user=request.user
    ).values_list('community_id', flat=True)
    school_communities = SchoolCommunity.objects.filter(
        id__in=joined_community_ids, is_active=True
    )
    custom_communities = CustomCommunity.objects.filter(
        Q(creator=request.user) | Q(privacy=CustomCommunity.PRIVACY_PUBLIC),
        is_active=True,
    )

    if request.method == 'POST':
        content = request.POST.get('content', '').strip()
        title = request.POST.get('title', '').strip()
        has_media = 'media' in request.FILES
        if not content and not has_media:
            django_messages.error(request, 'Post content cannot be empty.')
            return render(request, 'community/post_create.html', {
                'school_communities': school_communities,
                'custom_communities': custom_communities,
            })

        community_type = request.POST.get('community_type', 'feed')
        post = Post(author=request.user, content=content, title=title)
        post.category = request.POST.get('category', '')

        if community_type == 'feed':
            post.feed_only = True
        elif community_type == 'school':
            sc_id = request.POST.get('school_community_id')
            if not sc_id:
                django_messages.error(request, 'Select a school community.')
                return render(request, 'community/post_create.html', {
                    'school_communities': school_communities,
                    'custom_communities': custom_communities,
                })
            if not CommunityMembership.objects.filter(
                user=request.user, community_id=sc_id
            ).exists():
                django_messages.error(request, 'You must join this community before posting.')
                return render(request, 'community/post_create.html', {
                    'school_communities': school_communities,
                    'custom_communities': custom_communities,
                })
            post.school_community_id = sc_id
        else:
            cc_id = request.POST.get('custom_community_id')
            if not cc_id:
                django_messages.error(request, 'Select a community.')
                return render(request, 'community/post_create.html', {
                    'school_communities': school_communities,
                    'custom_communities': custom_communities,
                })
            post.custom_community_id = cc_id

        if 'media' in request.FILES:
            post.media = request.FILES['media']
            mime = request.FILES['media'].content_type
            if mime.startswith('image'):
                post.media_type = Post.MEDIA_IMAGE
            elif mime.startswith('video'):
                post.media_type = Post.MEDIA_VIDEO
            else:
                post.media_type = Post.MEDIA_FILE

        post.save()
        django_messages.success(request, 'Post published.')
        return redirect('community:post_detail', pk=post.id)

    return render(request, 'community/post_create.html', {
        'school_communities': school_communities,
        'custom_communities': custom_communities,
        'preselect_sc': preselect_sc,
        'preselect_cc': preselect_cc,
    })


@login_required
def post_detail(request, pk):
    post = get_object_or_404(
        Post.objects.select_related('author', 'author__community_profile',
                                    'school_community', 'custom_community'),
        pk=pk, is_deleted=False
    )
    is_liked = PostLike.objects.filter(user=request.user, post=post).exists()

    if request.method == 'POST':
        # Legacy form fallback (kept for non-JS clients)
        action = request.POST.get('action')
        if action == 'comment':
            content = request.POST.get('content', '').strip()
            if content:
                parent_id = request.POST.get('parent_id')
                Comment.objects.create(
                    post=post,
                    author=request.user,
                    content=content,
                    parent_id=parent_id if parent_id else None,
                )
                # comment_count is updated by signal; no manual update needed
        return redirect('community:post_detail', pk=pk)

    comments = (
        Comment.objects.filter(post=post, parent=None)
        .select_related('author', 'author__community_profile')
        .prefetch_related('replies__author', 'replies__author__community_profile')
        .order_by('created_at')
    )
    # Collect all comment IDs (top-level + replies) to check likes
    all_comment_ids = []
    for c in comments:
        all_comment_ids.append(c.id)
        for r in c.replies.all():
            all_comment_ids.append(r.id)
    liked_comment_ids = set(
        CommentLike.objects.filter(user=request.user, comment_id__in=all_comment_ids)
        .values_list('comment_id', flat=True)
    )
    # Ensure current user has a community profile (for avatar in template)
    CommunityProfile.objects.get_or_create(user=request.user)
    # Ensure all comment/reply authors have profiles (prevents RelatedObjectDoesNotExist)
    author_ids = set()
    for c in comments:
        author_ids.add(c.author_id)
        for r in c.replies.all():
            author_ids.add(r.author_id)
    author_ids.add(post.author_id)
    existing_profile_ids = set(
        CommunityProfile.objects.filter(user_id__in=author_ids).values_list('user_id', flat=True)
    )
    missing = author_ids - existing_profile_ids
    if missing:
        CommunityProfile.objects.bulk_create(
            [CommunityProfile(user_id=uid) for uid in missing],
            ignore_conflicts=True,
        )
    return render(request, 'community/post_detail.html', {
        'post': post,
        'is_liked': is_liked,
        'comments': comments,
        'liked_comment_ids': liked_comment_ids,
    })


@login_required
def post_delete(request, pk):
    post = get_object_or_404(Post, pk=pk, is_deleted=False)
    if post.author != request.user and not request.user.is_staff:
        django_messages.error(request, 'You cannot delete this post.')
        return redirect('community:post_detail', pk=pk)
    if request.method == 'POST':
        post.is_deleted = True
        post.save(update_fields=['is_deleted'])
        django_messages.success(request, 'Post deleted.')
        return redirect('community:feed')
    return render(request, 'community/post_delete.html', {'post': post})


# ── Messages / Conversations ──────────────────────────────────────────────────

@login_required
def messages_view(request, convo_id=None):
    user_convos = (
        Conversation.objects.filter(participants=request.user)
        .prefetch_related('participants', 'participants__community_profile', 'messages')
        .order_by('-updated_at')
    )

    # Attach helper data to each conversation
    for convo in user_convos:
        others = [p for p in convo.participants.all() if p != request.user]
        convo.other_participant = others[0] if others else request.user
        # Ensure the other participant has a community profile
        try:
            CommunityProfile.objects.get_or_create(user=convo.other_participant)
        except Exception:
            pass
        last = convo.messages.order_by('-created_at').first()
        convo.last_message_preview = (last.content[:40] + '…') if last and len(last.content) > 40 else (last.content if last else '')

    active_convo = None
    messages_list = []
    other_user = None

    if convo_id:
        active_convo = get_object_or_404(
            Conversation, id=convo_id, participants=request.user
        )
        messages_list = active_convo.messages.select_related('sender').order_by('created_at')
        others = [p for p in active_convo.participants.all() if p != request.user]
        other_user = others[0] if others else request.user
        # Ensure both users have a community profile for avatar rendering
        CommunityProfile.objects.get_or_create(user=request.user)
        if other_user != request.user:
            CommunityProfile.objects.get_or_create(user=other_user)

        if request.method == 'POST':
            content = request.POST.get('content', '').strip()
            if content:
                msg = Message.objects.create(
                    conversation=active_convo,
                    sender=request.user,
                    content=content,
                )
                Conversation.objects.filter(pk=active_convo.pk).update(
                    updated_at=timezone.now()
                )
                # AJAX request — return JSON
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or \
                   request.content_type == 'application/json' or \
                   request.headers.get('Accept') == 'application/json':
                    return JsonResponse({
                        'id': str(msg.id),
                        'content': msg.content,
                        'created_at': msg.created_at.isoformat(),
                    })
            return redirect('community:conversation_detail', convo_id=convo_id)

    return render(request, 'community/messages.html', {
        'conversations': user_convos,
        'active_convo': active_convo,
        'messages_list': messages_list,
        'other_user': other_user,
    })


@login_required
def poll_messages(request, convo_id):
    """Return messages newer than ?since=<iso-timestamp> as JSON for live polling."""
    convo = get_object_or_404(Conversation, id=convo_id, participants=request.user)
    since_raw = request.GET.get('since')
    qs = convo.messages.select_related('sender', 'sender__community_profile').order_by('created_at')
    if since_raw:
        from django.utils.dateparse import parse_datetime
        since_dt = parse_datetime(since_raw)
        if since_dt:
            qs = qs.filter(created_at__gt=since_dt)

    others = [p for p in convo.participants.all() if p != request.user]
    other_user = others[0] if others else request.user

    data = []
    for msg in qs:
        entry = {
            'id': str(msg.id),
            'content': msg.content,
            'message_type': msg.message_type,
            'created_at': msg.created_at.isoformat(),
            'is_mine': msg.sender_id == request.user.id,
            'sender_username': msg.sender.username,
            'sender_avatar': msg.sender.community_profile.avatar.url if hasattr(msg.sender, 'community_profile') and msg.sender.community_profile.avatar else None,
        }
        if msg.message_type == Message.TYPE_VOICE and msg.voice_note:
            entry['voice_note_url'] = msg.voice_note.url
        if msg.message_type in (Message.TYPE_IMAGE, Message.TYPE_VIDEO, Message.TYPE_FILE) and msg.media:
            entry['media_url'] = msg.media.url
            entry['media_name'] = msg.media.name
        data.append(entry)

    return JsonResponse({'messages': data})


@login_required
@require_POST
def send_voice_note(request, convo_id):
    convo = get_object_or_404(Conversation, id=convo_id, participants=request.user)
    audio = request.FILES.get('audio')
    if not audio:
        return JsonResponse({'error': 'No audio file'}, status=400)
    msg = Message.objects.create(
        conversation=convo,
        sender=request.user,
        content='',
        voice_note=audio,
        message_type=Message.TYPE_VOICE,
    )
    Conversation.objects.filter(pk=convo.pk).update(updated_at=timezone.now())
    return JsonResponse({
        'id': str(msg.id),
        'voice_note_url': msg.voice_note.url,
        'created_at': msg.created_at.isoformat(),
    })


@login_required
@require_POST
def send_media(request, convo_id):
    """Upload images, videos, documents and other files in a DM."""
    convo = get_object_or_404(Conversation, id=convo_id, participants=request.user)
    file = request.FILES.get('file')
    if not file:
        return JsonResponse({'error': 'No file'}, status=400)

    mime = file.content_type or ''
    if mime.startswith('image/'):
        msg_type = Message.TYPE_IMAGE
    elif mime.startswith('video/'):
        msg_type = Message.TYPE_VIDEO
    else:
        msg_type = Message.TYPE_FILE

    caption = request.POST.get('caption', '').strip()
    msg = Message.objects.create(
        conversation=convo,
        sender=request.user,
        content=caption,
        media=file,
        message_type=msg_type,
    )
    Conversation.objects.filter(pk=convo.pk).update(updated_at=timezone.now())
    return JsonResponse({
        'id': str(msg.id),
        'media_url': msg.media.url,
        'message_type': msg.message_type,
        'filename': file.name,
        'content': caption,
        'created_at': msg.created_at.isoformat(),
    })


@login_required
def dm_start(request, username):
    """Find or create a DM conversation with `username`, then redirect to it."""
    recipient = get_object_or_404(User, username=username)
    if recipient == request.user:
        return redirect('community:messages')

    existing = (
        Conversation.objects.filter(participants=request.user, is_group=False)
        .filter(participants=recipient)
        .first()
    )
    if existing:
        return redirect('community:conversation_detail', convo_id=existing.id)

    convo = Conversation.objects.create(is_group=False)
    convo.participants.set([request.user, recipient])
    return redirect('community:conversation_detail', convo_id=convo.id)


@login_required
def conversation_create(request):
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        content = request.POST.get('content', '').strip()
        try:
            recipient = User.objects.get(username=username)
        except User.DoesNotExist:
            django_messages.error(request, f'User "{username}" not found.')
            return render(request, 'community/conversation_create.html')

        if recipient == request.user:
            django_messages.error(request, 'You cannot message yourself.')
            return render(request, 'community/conversation_create.html')

        # Find existing DM or create new one
        existing = Conversation.objects.filter(
            participants=request.user, is_group=False
        ).filter(participants=recipient).first()

        if existing:
            convo = existing
        else:
            convo = Conversation.objects.create(is_group=False)
            convo.participants.set([request.user, recipient])

        if content:
            Message.objects.create(
                conversation=convo, sender=request.user, content=content
            )

        return redirect('community:conversation_detail', convo_id=convo.id)

    return render(request, 'community/conversation_create.html')


# ── Notifications ─────────────────────────────────────────────────────────────

@login_required
def notifications(request):
    notifs = (
        Notification.objects.filter(recipient=request.user)
        .select_related('actor', 'post', 'comment')
        .order_by('-created_at')[:50]
    )
    # Mark all as read when the page is visited
    Notification.objects.filter(recipient=request.user, is_read=False).update(is_read=True)
    return render(request, 'community/notifications.html', {'notifications': notifs})


@login_required
def notifications_mark_read(request):
    if request.method == 'POST':
        Notification.objects.filter(recipient=request.user, is_read=False).update(
            is_read=True
        )
    return redirect('community:notifications')


# ── Comment Like API ──────────────────────────────────────────────────────────

@login_required
@require_POST
def comment_like(request, comment_id):
    comment = get_object_or_404(Comment, pk=comment_id)
    like, created = CommentLike.objects.get_or_create(user=request.user, comment=comment)
    if not created:
        like.delete()
        # Re-fetch fresh count after signal fires
        comment.refresh_from_db(fields=['like_count'])
        return JsonResponse({'liked': False, 'like_count': comment.like_count})
    # Re-fetch fresh count after signal fires
    comment.refresh_from_db(fields=['like_count'])
    return JsonResponse({'liked': True, 'like_count': comment.like_count})


# ── Community Profile ─────────────────────────────────────────────────────────

@login_required
def community_profile(request, username):
    profile_user = get_object_or_404(User, username=username)
    profile, _ = CommunityProfile.objects.get_or_create(user=profile_user)
    posts = (
        Post.objects.filter(author=profile_user, is_deleted=False)
        .select_related('school_community', 'custom_community')
        .order_by('-created_at')[:20]
    )
    post_ids = [p.id for p in posts]
    liked_ids = set(
        PostLike.objects.filter(user=request.user, post_id__in=post_ids)
        .values_list('post_id', flat=True)
    )
    return render(request, 'community/profile.html', {
        'profile_user': profile_user,
        'profile': profile,
        'posts': posts,
        'liked_ids': liked_ids,
        'is_own': profile_user == request.user,
    })


@login_required
def community_profile_edit(request):
    profile, _ = CommunityProfile.objects.get_or_create(user=request.user)
    if request.method == 'POST':
        profile.bio = request.POST.get('bio', '').strip()[:500]
        if 'avatar' in request.FILES:
            profile.avatar = request.FILES['avatar']
        if 'banner' in request.FILES:
            profile.banner = request.FILES['banner']
        try:
            profile.save()
            django_messages.success(request, 'Profile updated.')
        except Exception:
            django_messages.error(request, 'Could not save profile. Please try again.')
        return redirect('community:profile', username=request.user.username)
    return render(request, 'community/profile_edit.html', {'profile': profile})


# ── Voice / Video Calls (Daily.co) ────────────────────────────────────────────

@login_required
@require_POST
def create_call(request, convo_id):
    """
    Create a Daily.co room for this conversation and return the room URL.
    Rooms expire after 1 hour automatically.
    If DAILY_API_KEY is not set, falls back to a free public room on daily.co.
    """
    import os, requests as http_requests, time

    convo = get_object_or_404(Conversation, id=convo_id, participants=request.user)
    call_type = request.POST.get('type', 'video')  # 'voice' or 'video'

    api_key = os.environ.get('DAILY_API_KEY', '')
    room_name = f'nexa-{convo_id}'

    if api_key:
        try:
            resp = http_requests.post(
                'https://api.daily.co/v1/rooms',
                headers={'Authorization': f'Bearer {api_key}', 'Content-Type': 'application/json'},
                json={
                    'name': room_name,
                    'properties': {
                        'exp': int(time.time()) + 3600,  # 1 hour
                        'enable_chat': False,
                        'enable_screenshare': True,
                        'start_video_off': call_type == 'voice',
                        'start_audio_off': False,
                        'max_participants': 10,
                    },
                },
                timeout=8,
            )
            data = resp.json()
            room_url = data.get('url') or f'https://nexa.daily.co/{room_name}'
        except Exception:
            room_url = f'https://nexa.daily.co/{room_name}'
    else:
        # No API key — use a deterministic public room name (fine for dev/demo)
        room_url = f'https://meet.daily.co/{room_name}'

    return JsonResponse({'room_url': room_url, 'type': call_type})


# ── Group Workspaces ──────────────────────────────────────────────────────────

@login_required
def workspace_list(request):
    """List all workspaces the user belongs to."""
    memberships = (
        WorkspaceMember.objects
        .filter(user=request.user)
        .select_related('workspace', 'workspace__owner')
        .order_by('-workspace__updated_at')
    )
    return render(request, 'community/workspace_list.html', {
        'memberships': memberships,
    })


@login_required
def workspace_create(request):
    """Two-step workspace creation."""
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        if not name:
            return render(request, 'community/workspace_create.html', {'error': 'Group name is required.'})

        description = request.POST.get('description', '').strip()
        subject = request.POST.get('subject', '').strip()
        privacy = request.POST.get('privacy', GroupWorkspace.PRIVACY_PRIVATE)
        if privacy not in (GroupWorkspace.PRIVACY_PRIVATE, GroupWorkspace.PRIVACY_REQUEST):
            privacy = GroupWorkspace.PRIVACY_PRIVATE

        ws = GroupWorkspace.objects.create(
            name=name,
            description=description,
            subject=subject,
            privacy=privacy,
            owner=request.user,
        )
        # Owner is automatically a member
        WorkspaceMember.objects.create(workspace=ws, user=request.user, role=WorkspaceMember.ROLE_OWNER)

        # Add selected members
        usernames = request.POST.getlist('members')
        for uname in usernames:
            try:
                u = User.objects.get(username=uname)
                if u != request.user:
                    WorkspaceMember.objects.get_or_create(workspace=ws, user=u, defaults={'role': WorkspaceMember.ROLE_MEMBER})
            except User.DoesNotExist:
                pass

        return redirect('community:workspace_detail', ws_id=ws.id)

    return render(request, 'community/workspace_create.html', {})


def _ws_member_or_404(request, ws_id):
    """Return (workspace, membership) or raise 404/403."""
    ws = get_object_or_404(GroupWorkspace, id=ws_id, is_active=True)
    try:
        membership = WorkspaceMember.objects.get(workspace=ws, user=request.user)
    except WorkspaceMember.DoesNotExist:
        from django.http import Http404
        raise Http404
    return ws, membership


@login_required
def workspace_detail(request, ws_id):
    """Main workspace dashboard."""
    ws, membership = _ws_member_or_404(request, ws_id)

    members = WorkspaceMember.objects.filter(workspace=ws).select_related('user', 'user__community_profile')
    messages_qs = ws.chat_messages.select_related('sender', 'sender__community_profile').order_by('created_at')
    files = ws.files.select_related('uploaded_by').order_by('-uploaded_at')
    tasks = ws.tasks.select_related('assigned_to', 'created_by').order_by('status', 'due_date')

    return render(request, 'community/workspace_detail.html', {
        'ws': ws,
        'membership': membership,
        'members': members,
        'messages_list': messages_qs,
        'files': files,
        'tasks': tasks,
        'is_owner': membership.role == WorkspaceMember.ROLE_OWNER,
        'is_admin': membership.role in (WorkspaceMember.ROLE_OWNER, WorkspaceMember.ROLE_ADMIN),
    })


@login_required
def workspace_join(request, invite_code):
    """Join a workspace via invite code."""
    ws = get_object_or_404(GroupWorkspace, invite_code=invite_code, is_active=True)
    _, created = WorkspaceMember.objects.get_or_create(
        workspace=ws, user=request.user,
        defaults={'role': WorkspaceMember.ROLE_MEMBER}
    )
    return redirect('community:workspace_detail', ws_id=ws.id)


@login_required
@require_POST
def workspace_send_message(request, ws_id):
    ws, _ = _ws_member_or_404(request, ws_id)
    content = request.POST.get('content', '').strip()
    file = request.FILES.get('file')
    if not content and not file:
        return JsonResponse({'error': 'Empty message'}, status=400)

    msg = WorkspaceMessage(workspace=ws, sender=request.user, content=content)
    if file:
        msg.media = file
        msg.media_name = file.name
    msg.save()
    ws.updated_at = timezone.now()
    ws.save(update_fields=['updated_at'])

    avatar = None
    try:
        avatar = request.user.community_profile.avatar.url if request.user.community_profile.avatar else None
    except Exception:
        pass

    return JsonResponse({
        'id': str(msg.id),
        'content': msg.content,
        'sender': request.user.username,
        'sender_avatar': avatar,
        'media_url': msg.media.url if msg.media else None,
        'media_name': msg.media_name,
        'created_at': msg.created_at.isoformat(),
    })


@login_required
def workspace_poll_messages(request, ws_id):
    ws, _ = _ws_member_or_404(request, ws_id)
    since_raw = request.GET.get('since')
    qs = ws.chat_messages.select_related('sender', 'sender__community_profile').order_by('created_at')
    if since_raw:
        from django.utils.dateparse import parse_datetime
        since_dt = parse_datetime(since_raw)
        if since_dt:
            qs = qs.filter(created_at__gt=since_dt)

    data = []
    for msg in qs:
        avatar = None
        try:
            avatar = msg.sender.community_profile.avatar.url if msg.sender.community_profile.avatar else None
        except Exception:
            pass
        data.append({
            'id': str(msg.id),
            'content': msg.content,
            'sender': msg.sender.username,
            'sender_avatar': avatar,
            'is_mine': msg.sender_id == request.user.id,
            'media_url': msg.media.url if msg.media else None,
            'media_name': msg.media_name,
            'created_at': msg.created_at.isoformat(),
        })
    return JsonResponse({'messages': data})


@login_required
@require_POST
def workspace_upload_file(request, ws_id):
    ws, _ = _ws_member_or_404(request, ws_id)
    f = request.FILES.get('file')
    if not f:
        return JsonResponse({'error': 'No file'}, status=400)
    wf = WorkspaceFile.objects.create(
        workspace=ws,
        uploaded_by=request.user,
        file=f,
        original_name=f.name,
        file_size=f.size,
    )
    return JsonResponse({
        'id': str(wf.id),
        'name': wf.original_name,
        'url': wf.file.url,
        'size': wf.file_size,
        'uploaded_by': request.user.username,
    })


@login_required
@require_POST
def workspace_add_task(request, ws_id):
    ws, _ = _ws_member_or_404(request, ws_id)
    title = request.POST.get('title', '').strip()
    if not title:
        return JsonResponse({'error': 'Title required'}, status=400)
    due = request.POST.get('due_date') or None
    assignee_name = request.POST.get('assigned_to', '').strip()
    assignee = None
    if assignee_name:
        try:
            assignee = User.objects.get(username=assignee_name)
        except User.DoesNotExist:
            pass
    task = WorkspaceTask.objects.create(
        workspace=ws,
        created_by=request.user,
        title=title,
        description=request.POST.get('description', ''),
        due_date=due,
        assigned_to=assignee,
    )
    return JsonResponse({
        'id': str(task.id),
        'title': task.title,
        'status': task.status,
        'due_date': str(task.due_date) if task.due_date else None,
        'assigned_to': task.assigned_to.username if task.assigned_to else None,
    })


@login_required
@require_POST
def workspace_update_task(request, ws_id, task_id):
    ws, _ = _ws_member_or_404(request, ws_id)
    task = get_object_or_404(WorkspaceTask, id=task_id, workspace=ws)
    status = request.POST.get('status')
    if status in (WorkspaceTask.STATUS_TODO, WorkspaceTask.STATUS_DOING, WorkspaceTask.STATUS_DONE):
        task.status = status
        task.save(update_fields=['status'])
    return JsonResponse({'id': str(task.id), 'status': task.status})


@login_required
@require_POST
def workspace_add_member(request, ws_id):
    ws, membership = _ws_member_or_404(request, ws_id)
    if membership.role not in (WorkspaceMember.ROLE_OWNER, WorkspaceMember.ROLE_ADMIN):
        return JsonResponse({'error': 'Permission denied'}, status=403)
    username = request.POST.get('username', '').strip()
    try:
        u = User.objects.get(username=username)
    except User.DoesNotExist:
        return JsonResponse({'error': 'User not found'}, status=404)
    _, created = WorkspaceMember.objects.get_or_create(
        workspace=ws, user=u, defaults={'role': WorkspaceMember.ROLE_MEMBER}
    )
    return JsonResponse({'username': u.username, 'added': created})


@login_required
@require_POST
def workspace_remove_member(request, ws_id, user_id):
    ws, membership = _ws_member_or_404(request, ws_id)
    if membership.role not in (WorkspaceMember.ROLE_OWNER, WorkspaceMember.ROLE_ADMIN):
        return JsonResponse({'error': 'Permission denied'}, status=403)
    WorkspaceMember.objects.filter(workspace=ws, user_id=user_id).exclude(
        role=WorkspaceMember.ROLE_OWNER
    ).delete()
    return JsonResponse({'ok': True})


@login_required
@require_POST
def workspace_leave(request, ws_id):
    ws, membership = _ws_member_or_404(request, ws_id)
    if membership.role == WorkspaceMember.ROLE_OWNER:
        return JsonResponse({'error': 'Owner cannot leave. Delete the workspace instead.'}, status=400)
    membership.delete()
    return redirect('community:workspace_list')


@login_required
@require_POST
def workspace_delete(request, ws_id):
    ws = get_object_or_404(GroupWorkspace, id=ws_id, owner=request.user)
    ws.delete()
    return redirect('community:workspace_list')


@login_required
def workspace_search_users(request):
    """AJAX user search for adding members."""
    q = request.GET.get('q', '').strip()
    if len(q) < 2:
        return JsonResponse({'users': []})
    users = User.objects.filter(
        Q(username__icontains=q) | Q(first_name__icontains=q) | Q(last_name__icontains=q)
    ).exclude(id=request.user.id)[:10]
    return JsonResponse({'users': [{'username': u.username, 'display': u.get_full_name() or u.username} for u in users]})


# ── Quick Join Community (from feed) ─────────────────────────────────────────

@login_required
@require_POST
def quick_join_custom(request, slug):
    """Join/leave a public CustomCommunity directly from the feed."""
    community = get_object_or_404(CustomCommunity, slug=slug, is_active=True)
    if community.privacy == CustomCommunity.PRIVACY_PRIVATE:
        return JsonResponse({'error': 'Private community.'}, status=403)
    membership, created = CustomCommunityMembership.objects.get_or_create(
        user=request.user, community=community
    )
    if not created:
        membership.delete()
        return JsonResponse({'joined': False, 'member_count': community.memberships.count()})
    return JsonResponse({'joined': True, 'member_count': community.memberships.count()})


@login_required
@require_POST
def quick_join_school(request, slug):
    """Join/leave a SchoolCommunity directly from the feed."""
    community = get_object_or_404(SchoolCommunity, slug=slug, is_active=True)
    membership, created = CommunityMembership.objects.get_or_create(
        user=request.user, community=community,
        defaults={'role': CommunityMembership.ROLE_MEMBER}
    )
    if not created:
        membership.delete()
        return JsonResponse({'joined': False})
    return JsonResponse({'joined': True})


# ── Share Post via DM ─────────────────────────────────────────────────────────

@login_required
def share_post_dm_list(request):
    """Return the user's DM conversations for the share picker."""
    convos = (
        Conversation.objects.filter(participants=request.user, is_group=False)
        .prefetch_related('participants', 'participants__community_profile')
        .order_by('-updated_at')[:30]
    )
    data = []
    for c in convos:
        others = [p for p in c.participants.all() if p != request.user]
        if not others:
            continue
        other = others[0]
        avatar = None
        try:
            avatar = other.community_profile.avatar.url if other.community_profile.avatar else None
        except Exception:
            pass
        data.append({
            'convo_id': str(c.id),
            'username': other.username,
            'avatar': avatar,
        })
    return JsonResponse({'conversations': data})


@login_required
@require_POST
def share_post_send(request, post_id):
    """Send a post link as a DM to selected conversations."""
    import json
    post = get_object_or_404(Post, pk=post_id, is_deleted=False)
    try:
        body = json.loads(request.body)
        convo_ids = body.get('convo_ids', [])
    except Exception:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    if not convo_ids:
        return JsonResponse({'error': 'No conversations selected.'}, status=400)

    post_url = request.build_absolute_uri(f'/community/posts/{post.id}/')
    preview = post.content[:80] + ('…' if len(post.content) > 80 else '')
    message_text = f'📎 Shared a post: {preview}\n{post_url}'

    sent = 0
    for cid in convo_ids[:10]:  # cap at 10
        try:
            convo = Conversation.objects.get(id=cid, participants=request.user)
            Message.objects.create(
                conversation=convo,
                sender=request.user,
                content=message_text,
                message_type=Message.TYPE_TEXT,
            )
            Conversation.objects.filter(pk=convo.pk).update(updated_at=timezone.now())
            # Increment share count
            Post.objects.filter(pk=post.id).update(share_count=models.F('share_count') + 1)
            sent += 1
        except Conversation.DoesNotExist:
            pass

    return JsonResponse({'sent': sent})


# ── Friend Requests ───────────────────────────────────────────────────────────

@login_required
@require_POST
def friend_request_send(request, username):
    """Send a friend request to a user."""
    recipient = get_object_or_404(User, username=username)
    if recipient == request.user:
        return JsonResponse({'error': 'Cannot friend yourself.'}, status=400)

    # Check if already friends or request exists
    existing = Friendship.objects.filter(
        Q(requester=request.user, recipient=recipient) |
        Q(requester=recipient, recipient=request.user)
    ).first()

    if existing:
        if existing.status == Friendship.STATUS_ACCEPTED:
            return JsonResponse({'status': 'already_friends'})
        if existing.status == Friendship.STATUS_PENDING:
            return JsonResponse({'status': 'pending'})
        # Rejected — allow re-request
        existing.delete()

    friendship = Friendship.objects.create(requester=request.user, recipient=recipient)

    # Notify recipient
    Notification.objects.create(
        recipient=recipient,
        actor=request.user,
        type=Notification.TYPE_FRIEND_REQUEST,
    )

    return JsonResponse({'status': 'sent', 'id': str(friendship.id)})


@login_required
@require_POST
def friend_request_respond(request, friendship_id):
    """Accept or reject a friend request."""
    import json
    friendship = get_object_or_404(
        Friendship, id=friendship_id, recipient=request.user, status=Friendship.STATUS_PENDING
    )
    try:
        body = json.loads(request.body)
        action = body.get('action')
    except Exception:
        action = request.POST.get('action')

    if action == 'accept':
        friendship.status = Friendship.STATUS_ACCEPTED
        friendship.save(update_fields=['status', 'updated_at'])
        # Notify requester
        Notification.objects.create(
            recipient=friendship.requester,
            actor=request.user,
            type=Notification.TYPE_FRIEND_ACCEPTED,
        )
        return JsonResponse({'status': 'accepted'})
    elif action == 'reject':
        friendship.status = Friendship.STATUS_REJECTED
        friendship.save(update_fields=['status', 'updated_at'])
        return JsonResponse({'status': 'rejected'})

    return JsonResponse({'error': 'Invalid action.'}, status=400)


@login_required
def friend_status(request, username):
    """Return friendship status between current user and username."""
    other = get_object_or_404(User, username=username)
    friendship = Friendship.objects.filter(
        Q(requester=request.user, recipient=other) |
        Q(requester=other, recipient=request.user)
    ).first()

    if not friendship:
        return JsonResponse({'status': 'none'})

    # Determine perspective
    if friendship.status == Friendship.STATUS_ACCEPTED:
        return JsonResponse({'status': 'friends', 'id': str(friendship.id)})
    if friendship.requester == request.user:
        return JsonResponse({'status': 'pending_sent', 'id': str(friendship.id)})
    return JsonResponse({'status': 'pending_received', 'id': str(friendship.id)})


@login_required
def pending_friend_requests(request):
    """Return pending friend requests received by the current user."""
    requests_qs = (
        Friendship.objects.filter(recipient=request.user, status=Friendship.STATUS_PENDING)
        .select_related('requester', 'requester__community_profile')
        .order_by('-created_at')
    )
    data = []
    for fr in requests_qs:
        avatar = None
        try:
            avatar = fr.requester.community_profile.avatar.url if fr.requester.community_profile.avatar else None
        except Exception:
            pass
        data.append({
            'id': str(fr.id),
            'username': fr.requester.username,
            'avatar': avatar,
            'created_at': fr.created_at.isoformat(),
        })
    return JsonResponse({'requests': data})
