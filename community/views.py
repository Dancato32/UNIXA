"""
Template-based views for the community app.
All views require login. No modifications to existing apps.
"""

from django.contrib import messages as django_messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
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
    Message,
    Notification,
    Post,
    PostLike,
    SchoolCommunity,
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

    return render(request, 'community/feed.html', {
        'posts': posts,
        'has_more': has_more,
        'next_cursor': next_cursor,
        'liked_ids': liked_ids,
        'school_communities': school_communities,
        'joined_ids': joined_ids,
        'custom_communities': custom_communities,
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
            django_messages.error(request, 'Name is required.')
            return render(request, 'community/custom_create.html')
        cc = CustomCommunity(
            name=name,
            description=request.POST.get('description', ''),
            privacy=request.POST.get('privacy', 'public'),
            rules=request.POST.get('rules', ''),
            creator=request.user,
        )
        if 'logo' in request.FILES:
            cc.logo = request.FILES['logo']
        cc.save()
        django_messages.success(request, f'Community "{cc.name}" created.')
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
