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


# ── Community Home ───────────────────────────────────────────────────────────

@login_required
def community_home(request):
    """
    Community-First Home page.
    Shows feed preview, communities, quick actions, and user's workspaces.
    This is the new post-login landing page — the old dashboard remains at /dashboard/.
    """
    from community.services.feed import get_personalized_feed

    # Recent feed posts (top 8)
    try:
        result = get_personalized_feed(request.user, limit=8)
        feed_posts = result.get('posts', [])
    except Exception:
        feed_posts = []

    # User's school memberships
    try:
        school_memberships = list(
            CommunityMembership.objects.filter(user=request.user)
            .select_related('community').order_by('-joined_at')[:6]
        )
    except Exception:
        school_memberships = []

    # User's custom community memberships
    try:
        custom_memberships = list(
            CustomCommunityMembership.objects.filter(user=request.user)
            .select_related('community').order_by('-joined_at')[:6]
        )
    except Exception:
        custom_memberships = []

    # Suggested communities (public, not already joined)
    try:
        joined_custom_ids = [m.community_id for m in custom_memberships]
        suggested_communities = list(
            CustomCommunity.objects.filter(
                privacy=CustomCommunity.PRIVACY_PUBLIC,
                is_active=True,
            ).exclude(id__in=joined_custom_ids).order_by('-created_at')[:4]
        )
    except Exception:
        suggested_communities = []

    # User's workspaces — guard against missing is_personal column before migration runs
    workspace_memberships = []
    personal_ws = None
    nexa_ws = None
    last_workspace = None
    try:
        workspace_memberships = list(
            WorkspaceMember.objects.filter(
                user=request.user,
                workspace__is_active=True,
                workspace__is_personal=False,
            ).select_related('workspace', 'workspace__owner')
            .order_by('-workspace__updated_at')[:6]
        )
        # Personal workspace — any is_personal=True workspace that isn't Nexa
        personal_ws = GroupWorkspace.objects.filter(
            owner=request.user, is_personal=True, is_active=True,
        ).exclude(workspace_type=GroupWorkspace.TYPE_NEXA).first()
        # Nexa workspace
        nexa_ws = GroupWorkspace.objects.filter(
            owner=request.user, is_personal=True, is_active=True,
            workspace_type=GroupWorkspace.TYPE_NEXA,
        ).first()
        last_ws_member = (
            WorkspaceMember.objects.filter(
                user=request.user,
                workspace__is_active=True,
                workspace__is_personal=False,
            ).select_related('workspace').order_by('-workspace__updated_at').first()
        )
        last_workspace = last_ws_member.workspace if last_ws_member else None
    except Exception:
        # Migration hasn't run yet — fall back to queries without is_personal
        try:
            workspace_memberships = list(
                WorkspaceMember.objects.filter(
                    user=request.user,
                    workspace__is_active=True,
                ).select_related('workspace', 'workspace__owner')
                .order_by('-workspace__updated_at')[:6]
            )
            last_ws_member = (
                WorkspaceMember.objects.filter(
                    user=request.user, workspace__is_active=True,
                ).select_related('workspace').order_by('-workspace__updated_at').first()
            )
            last_workspace = last_ws_member.workspace if last_ws_member else None
        except Exception:
            pass

    # Unread message count (simple approach)
    try:
        from community.models import Message as _Msg
        unread_msgs = _Msg.objects.filter(
            conversation__participants=request.user,
            is_read=False,
        ).exclude(sender=request.user).count()
    except Exception:
        unread_msgs = 0

    return render(request, 'community/home.html', {
        'feed_posts': feed_posts,
        'school_memberships': school_memberships,
        'custom_memberships': custom_memberships,
        'suggested_communities': suggested_communities,
        'workspace_memberships': workspace_memberships,
        'personal_ws': personal_ws,
        'nexa_ws': nexa_ws,
        'last_workspace': last_workspace,
        'unread_msgs': unread_msgs,
        'workspace_type_choices': GroupWorkspace.TYPE_CHOICES,
    })


# ── Feed ──────────────────────────────────────────────────────────────────────

@login_required
def feed(request):
    from django.utils.dateparse import parse_datetime
    from community.models import Follow
    cursor = request.GET.get('cursor')
    tab = request.GET.get('tab', 'all')  # 'all' or 'following'
    limit = 20

    qs = Post.objects.filter(is_deleted=False).select_related(
        'author', 'author__community_profile', 'school_community', 'custom_community'
    )

    if tab == 'following':
        from django.db.models import Q
        # Posts from people the current user follows OR communities they've joined
        following_ids = Follow.objects.filter(follower=request.user).values_list('following_id', flat=True)
        joined_school_ids = CommunityMembership.objects.filter(user=request.user).values_list('community_id', flat=True)
        joined_custom_ids = CustomCommunityMembership.objects.filter(user=request.user).values_list('community_id', flat=True)
        qs = qs.filter(
            Q(author_id__in=following_ids) |
            Q(school_community_id__in=joined_school_ids) |
            Q(custom_community_id__in=joined_custom_ids)
        )
    
    qs = qs.order_by('-created_at')

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

    # People the current user follows (for sidebar)
    following = (
        Follow.objects.filter(follower=request.user)
        .select_related('following', 'following__community_profile')
        .order_by('-created_at')[:10]
    )
    following_user_ids = set(Follow.objects.filter(follower=request.user).values_list('following_id', flat=True))

    return render(request, 'community/feed.html', {
        'posts': posts,
        'has_more': has_more,
        'next_cursor': next_cursor,
        'liked_ids': liked_ids,
        'school_communities': school_communities,
        'joined_ids': joined_ids,
        'custom_communities': custom_communities,
        'custom_joined_ids': custom_joined_ids,
        'tab': tab,
        'following': following,
        'following_user_ids': following_user_ids,
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

    TECHNICAL_KEYWORDS = ['technical university', 'university of mines', 'university of technology']
    INTERNATIONAL_KEYWORDS = ['lancaster', 'academic city', 'bluecrest']
    PRIVATE_KEYWORDS = [
        'ashesi', 'central university', 'valley view', 'methodist university',
        'presbyterian university', 'pentecost university', 'catholic university',
        'islamic university', 'christian university', 'garden city', 'knutsford',
        'kings university', 'wisconsin', 'regent university', 'african university college',
        'ghana technology university', 'ghana christian',
    ]

    def get_type(name):
        n = name.lower()
        if any(k in n for k in TECHNICAL_KEYWORDS):
            return 'technical'
        if any(k in n for k in INTERNATIONAL_KEYWORDS):
            return 'international'
        if any(k in n for k in PRIVATE_KEYWORDS):
            return 'private'
        return 'public'

    schools_with_type = [(sc, get_type(sc.name)) for sc in qs]

    return render(request, 'community/schools.html', {
        'schools_with_type': schools_with_type,
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
    joined_cc_ids = CustomCommunityMembership.objects.filter(
        user=request.user
    ).values_list('community_id', flat=True)
    custom_communities = CustomCommunity.objects.filter(
        Q(id__in=joined_cc_ids) | Q(creator=request.user),
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
            if not CustomCommunityMembership.objects.filter(
                user=request.user, community_id=cc_id
            ).exists() and not CustomCommunity.objects.filter(
                id=cc_id, creator=request.user
            ).exists():
                django_messages.error(request, 'You must join this community before posting.')
                return render(request, 'community/post_create.html', {
                    'school_communities': school_communities,
                    'custom_communities': custom_communities,
                })

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

        # Mark message notifications from the other user as read when opening convo
        if other_user and other_user != request.user:
            Notification.objects.filter(
                recipient=request.user,
                actor=other_user,
                type=Notification.TYPE_MESSAGE,
                is_read=False,
            ).update(is_read=True)

    # Get accepted friends (excluding those already in conversations)
    accepted_friendships = Friendship.objects.filter(
        Q(requester=request.user, status=Friendship.STATUS_ACCEPTED) |
        Q(recipient=request.user, status=Friendship.STATUS_ACCEPTED)
    ).select_related('requester', 'requester__community_profile', 'recipient', 'recipient__community_profile')

    convo_participant_ids = set()
    for convo in user_convos:
        if convo.other_participant:
            convo_participant_ids.add(convo.other_participant.id)

    friends = []
    for f in accepted_friendships:
        friend_user = f.recipient if f.requester_id == request.user.id else f.requester
        if friend_user.id not in convo_participant_ids:
            try:
                CommunityProfile.objects.get_or_create(user=friend_user)
            except Exception:
                pass
            friends.append(friend_user)

    return render(request, 'community/messages.html', {
        'conversations': user_convos,
        'active_convo': active_convo,
        'messages_list': messages_list,
        'other_user': other_user,
        'friends': friends,
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
        .select_related('actor', 'post', 'comment', 'conversation')
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
    from community.models import Follow
    follower_count = Follow.objects.filter(following=profile_user).count()
    following_count = Follow.objects.filter(follower=profile_user).count()
    total_likes = Post.objects.filter(author=profile_user, is_deleted=False).aggregate(
        total=models.Sum('like_count')
    )['total'] or 0
    is_following = Follow.objects.filter(follower=request.user, following=profile_user).exists()
    return render(request, 'community/profile.html', {
        'profile_user': profile_user,
        'profile': profile,
        'posts': posts,
        'liked_ids': liked_ids,
        'is_own': profile_user == request.user,
        'follower_count': follower_count,
        'following_count': following_count,
        'total_likes': total_likes,
        'is_following': is_following,
    })


@login_required
def community_profile_edit(request):
    profile, _ = CommunityProfile.objects.get_or_create(user=request.user)
    if request.method == 'POST':
        profile.display_name = request.POST.get('display_name', '').strip()[:100]
        profile.bio = request.POST.get('bio', '').strip()[:500]
        profile.location = request.POST.get('location', '').strip()[:100]
        profile.website = request.POST.get('website', '').strip()[:200]
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


# ── Voice / Video Calls (PeerJS WebRTC) ──────────────────────────────────────

@login_required
@require_POST
def create_call(request, convo_id):
    """Store caller's peer ID server-side so the callee can look it up."""
    from django.core.cache import cache
    convo = get_object_or_404(Conversation, id=convo_id, participants=request.user)
    call_type = request.POST.get('type', 'voice')
    peer_id = request.POST.get('peer_id', '')
    if peer_id:
        # Store for 5 minutes so callee can fetch it
        cache_key = f'call_peer_{convo_id}_{request.user.username}'
        cache.set(cache_key, peer_id, timeout=300)
    return JsonResponse({'ok': True, 'type': call_type})


@login_required
def get_peer_id(request, convo_id):
    """Return the other participant's registered peer ID (if any)."""
    from django.core.cache import cache
    convo = get_object_or_404(Conversation, id=convo_id, participants=request.user)
    others = [p for p in convo.participants.all() if p != request.user]
    other = others[0] if others else None
    peer_id = None
    if other:
        cache_key = f'call_peer_{convo_id}_{other.username}'
        peer_id = cache.get(cache_key)
    return JsonResponse({'peer_id': peer_id})


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
def nexa_workspace(request):
    """Get or create the user's personal Nexa workspace and redirect to it."""
    ws = GroupWorkspace.objects.filter(
        owner=request.user,
        workspace_type=GroupWorkspace.TYPE_NEXA,
        is_personal=True,
    ).first()
    if not ws:
        ws = GroupWorkspace.objects.create(
            name='My Nexa Workspace',
            description='Your personal AI-powered learning hub.',
            workspace_type=GroupWorkspace.TYPE_NEXA,
            privacy=GroupWorkspace.PRIVACY_PRIVATE,
            owner=request.user,
            is_personal=True,
        )
        WorkspaceMember.objects.create(
            workspace=ws,
            user=request.user,
            role=WorkspaceMember.ROLE_OWNER,
        )
    return redirect('community:workspace_detail', ws_id=ws.id)


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

        ws_type = request.POST.get('workspace_type', GroupWorkspace.TYPE_GENERAL)
        valid_types = [t[0] for t in GroupWorkspace.TYPE_CHOICES]
        if ws_type not in valid_types:
            ws_type = GroupWorkspace.TYPE_GENERAL

        ws = GroupWorkspace.objects.create(
            name=name,
            description=description,
            subject=subject,
            workspace_type=ws_type,
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
    from django.conf import settings as django_settings
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
        'PEERJS_API_KEY': __import__('django.conf', fromlist=['settings']).settings.PEERJS_API_KEY,
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
        # Detect AI messages stored with [AI] prefix
        is_ai_msg = msg.content.startswith('[AI]')
        content = msg.content[4:] if is_ai_msg else msg.content
        data.append({
            'id': str(msg.id),
            'content': content,
            'sender': 'AI Assistant' if is_ai_msg else msg.sender.username,
            'sender_avatar': avatar,
            'is_mine': (not is_ai_msg) and (msg.sender_id == request.user.id),
            'is_ai': is_ai_msg,
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
    # Notification created by signal (on_friendship_change)
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
        # Notification created by signal (on_friendship_change)
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
@require_POST
def follow_toggle(request):
    """Toggle follow for a user. Body: {username: '...'}"""
    import json
    try:
        body = json.loads(request.body)
        username = body.get('username', '').strip()
    except Exception:
        username = request.POST.get('username', '').strip()
    if not username:
        return JsonResponse({'error': 'username required'}, status=400)
    other = get_object_or_404(User, username=username)
    if other == request.user:
        return JsonResponse({'error': 'Cannot follow yourself.'}, status=400)
    from community.models import Follow
    follow, created = Follow.objects.get_or_create(follower=request.user, following=other)
    if not created:
        follow.delete()
        following = False
    else:
        following = True
        # Notification is created by signal (community/signals.py → on_follow)
    follower_count = Follow.objects.filter(following=other).count()
    return JsonResponse({'following': following, 'follower_count': follower_count})


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


def profile_stats(request, username):
    """Return live follower/following counts for a profile. No login required."""
    from community.models import Follow
    profile_user = get_object_or_404(User, username=username)
    return JsonResponse({
        'follower_count': Follow.objects.filter(following=profile_user).count(),
        'following_count': Follow.objects.filter(follower=profile_user).count(),
    })

@login_required
def search_users(request):
    """Search users by username for friend/follow discovery."""
    q = request.GET.get('q', '').strip()
    if len(q) < 2:
        return JsonResponse({'users': []})

    users = (
        User.objects.filter(username__icontains=q)
        .exclude(id=request.user.id)
        .select_related('community_profile')
        [:10]
    )

    # Get friendship statuses in bulk
    user_ids = [u.id for u in users]
    friendships = Friendship.objects.filter(
        Q(requester=request.user, recipient_id__in=user_ids) |
        Q(requester_id__in=user_ids, recipient=request.user)
    ).select_related('requester', 'recipient')

    friendship_map = {}
    for f in friendships:
        other_id = f.recipient_id if f.requester_id == request.user.id else f.requester_id
        if f.status == Friendship.STATUS_ACCEPTED:
            friendship_map[other_id] = ('friends', str(f.id))
        elif f.requester_id == request.user.id:
            friendship_map[other_id] = ('pending_sent', str(f.id))
        else:
            friendship_map[other_id] = ('pending_received', str(f.id))

    from community.models import Follow
    following_ids = set(
        Follow.objects.filter(follower=request.user, following_id__in=user_ids)
        .values_list('following_id', flat=True)
    )

    data = []
    for u in users:
        avatar = None
        display_name = u.username
        try:
            cp = u.community_profile
            if cp.avatar:
                avatar = cp.avatar.url
            if cp.display_name:
                display_name = cp.display_name
        except Exception:
            pass
        status, fid = friendship_map.get(u.id, ('none', ''))
        data.append({
            'id': u.id,
            'username': u.username,
            'display_name': display_name,
            'avatar': avatar,
            'friendship_status': status,
            'friendship_id': fid,
            'is_following': u.id in following_ids,
        })
    return JsonResponse({'users': data})


@login_required
def api_workspaces_list(request):
    """Return recent workspaces for the radar."""
    from community.models import GroupWorkspace, WorkspaceMember
    ws_ids = WorkspaceMember.objects.filter(user=request.user).values_list('workspace_id', flat=True)
    workspaces = GroupWorkspace.objects.filter(id__in=ws_ids).order_by('-created_at')[:10]
    return JsonResponse({
        'workspaces': [{'id': str(w.id), 'name': w.name} for w in workspaces]
    })


@login_required
def api_posts_recent(request):
    """Return recent posts for the radar."""
    posts = Post.objects.filter(is_deleted=False).order_by('-created_at')[:10]
    return JsonResponse({
        'posts': [{'id': str(p.id), 'content': p.content[:80]} for p in posts]
    })


@login_required
def api_communities_list(request):
    """Return active communities for the radar."""
    from community.models import SchoolCommunity, CustomCommunity
    schools = list(SchoolCommunity.objects.filter(is_active=True).values('name')[:5])
    customs = list(CustomCommunity.objects.filter(is_active=True).values('name')[:5])
    return JsonResponse({'communities': schools + customs})


# ── Group Call Presence ───────────────────────────────────────────────────────
# Uses Django's cache to track who is in a call. TTL = 30s, refreshed every 10s.
# No new DB model needed — presence is ephemeral.

def _call_cache_key(ws_id):
    return f'ws_call_{ws_id}'


@login_required
@require_POST
def workspace_call_join(request, ws_id):
    """Mark current user as active in the workspace call."""
    from django.core.cache import cache
    ws = get_object_or_404(GroupWorkspace, id=ws_id, is_active=True)
    # Verify membership
    if not WorkspaceMember.objects.filter(workspace=ws, user=request.user).exists():
        return JsonResponse({'error': 'Not a member'}, status=403)

    key = _call_cache_key(ws_id)
    participants = cache.get(key, {})
    is_first = len(participants) == 0

    avatar = None
    try:
        avatar = request.user.community_profile.avatar.url if request.user.community_profile.avatar else None
    except Exception:
        pass
    participants[str(request.user.id)] = {
        'username': request.user.username,
        'avatar': avatar,
        'joined_at': timezone.now().isoformat(),
    }
    cache.set(key, participants, timeout=30)

    # Record call start time when first person joins
    if is_first:
        start_key = f'ws_call_start_{ws_id}'
        cache.set(start_key, timezone.now().isoformat(), timeout=86400)

    # Post a system message to chat (only when first joining, not on heartbeat)
    if request.POST.get('announce') == '1':
        WorkspaceMessage.objects.create(
            workspace=ws,
            sender=request.user,
            content=f'📞 {request.user.username} joined the group call',
        )

    return JsonResponse({'ok': True, 'count': len(participants)})


@login_required
@require_POST
def workspace_call_leave(request, ws_id):
    """Remove current user from the workspace call. When last person leaves, auto-save meeting record."""
    from django.core.cache import cache
    from community.models import MeetingRecord
    ws = get_object_or_404(GroupWorkspace, id=ws_id, is_active=True)
    key = _call_cache_key(ws_id)
    participants = cache.get(key, {})
    participants.pop(str(request.user.id), None)
    if participants:
        cache.set(key, participants, timeout=30)
    else:
        cache.delete(key)
        # Last person left — capture meeting record
        start_key = f'ws_call_start_{ws_id}'
        started_at_str = cache.get(start_key)
        cache.delete(start_key)

        if started_at_str:
            from django.utils.dateparse import parse_datetime
            started_at = parse_datetime(started_at_str) or timezone.now()
            ended_at = timezone.now()

            # Collect all messages sent during the call window
            msgs_qs = WorkspaceMessage.objects.filter(
                workspace=ws,
                created_at__gte=started_at,
                created_at__lte=ended_at,
            ).values('sender__username', 'content', 'created_at')

            chat_log = [
                {
                    'sender': m['sender__username'],
                    'content': m['content'],
                    'time': m['created_at'].strftime('%H:%M'),
                }
                for m in msgs_qs
                if not m['content'].startswith('📞') and not m['content'].startswith('📴')
            ]

            # Collect participant usernames from all who joined
            all_members = list(WorkspaceMember.objects.filter(workspace=ws).values_list('user__username', flat=True))

            # Run AI summary
            from ai_community.ai_engine import analyze_meeting_transcript
            analysis = analyze_meeting_transcript(
                messages=chat_log,
                workspace_name=ws.name,
                members=all_members,
            )

            summary = ''
            decisions = []
            action_items = []
            key_topics = []
            if analysis:
                summary = analysis.get('summary', '')
                decisions = analysis.get('decisions', [])
                action_items = analysis.get('action_items', [])
                key_topics = analysis.get('key_topics', [])

            # Save meeting record
            record = MeetingRecord.objects.create(
                workspace=ws,
                started_at=started_at,
                ended_at=ended_at,
                participants=all_members,
                chat_log=chat_log,
                ai_summary=summary,
                decisions=decisions,
                action_items=action_items,
                key_topics=key_topics,
            )

            # Post Nexa summary to group chat
            if summary:
                duration_mins = max(1, int((ended_at - started_at).total_seconds() / 60))
                nexa_msg = f"[AI] 📋 Meeting ended ({duration_mins} min). Here's what was covered:\n\n{summary}"
                if decisions:
                    nexa_msg += '\n\n✅ Decisions: ' + ' | '.join(decisions[:3])
                if action_items:
                    items_text = ', '.join(
                        a.get('task', str(a)) if isinstance(a, dict) else str(a)
                        for a in action_items[:3]
                    )
                    nexa_msg += f'\n\n📌 Action items: {items_text}'
                nexa_msg += f'\n\n📁 Full transcript saved in Meeting Notes.'
                WorkspaceMessage.objects.create(
                    workspace=ws,
                    sender=request.user,
                    content=nexa_msg,
                )

    WorkspaceMessage.objects.create(
        workspace=ws,
        sender=request.user,
        content=f'📴 {request.user.username} left the group call',
    )
    return JsonResponse({'ok': True})


@login_required
def workspace_call_participants(request, ws_id):
    """Return current call participants + heartbeat (refreshes TTL)."""
    from django.core.cache import cache
    ws = get_object_or_404(GroupWorkspace, id=ws_id, is_active=True)
    if not WorkspaceMember.objects.filter(workspace=ws, user=request.user).exists():
        return JsonResponse({'error': 'Not a member'}, status=403)

    key = _call_cache_key(ws_id)
    participants = cache.get(key, {})

    # Heartbeat: refresh TTL for current user if they're in the call
    uid = str(request.user.id)
    if uid in participants:
        participants[uid]['joined_at'] = timezone.now().isoformat()
        cache.set(key, participants, timeout=30)

    return JsonResponse({
        'participants': list(participants.values()),
        'count': len(participants),
    })


# ── Workspace AI Manager ──────────────────────────────────────────────────────

@login_required
@require_POST
def workspace_ai_chat(request, ws_id):
    """Conversational AI manager endpoint — AI acts as a real team member."""
    import json as _json
    from ai_community.ai_engine import workspace_ai_chat as _ai_chat
    ws, _ = _ws_member_or_404(request, ws_id)

    try:
        body = _json.loads(request.body)
        message = body.get('message', '').strip()
        # source: 'group' = came from group chat, 'manager' = AI Manager panel
        source = body.get('source', 'group')
    except Exception:
        message = request.POST.get('message', '').strip()
        source = 'group'

    if not message:
        return JsonResponse({'error': 'Message required'}, status=400)

    members = list(
        WorkspaceMember.objects.filter(workspace=ws)
        .values_list('user__username', flat=True)
    )
    tasks = list(
        ws.tasks.values('title', 'status', 'assigned_to__username')
    )
    tasks_clean = [
        {'title': t['title'], 'status': t['status'], 'assigned_to': t['assigned_to__username']}
        for t in tasks
    ]
    files = list(ws.files.values_list('original_name', flat=True))

    # Pass last 20 messages so AI has full conversation context
    recent_chat = list(
        ws.chat_messages.order_by('-created_at')
        .values('sender__username', 'content')[:20]
    )
    recent_chat = list(reversed(recent_chat))

    context = {
        'workspace_name': ws.name,
        'workspace_type': ws.workspace_type,
        'members': members,
        'tasks': tasks_clean,
        'files': list(files),
        'recent_chat': recent_chat,
        'current_sender': request.user.username,
        'source': source,
    }

    result = _ai_chat(message, context)

    # Save AI reply to group chat DB so all members see it via polling
    if result.get('reply') and source == 'group':
        # Use a system/bot user approach — save as a special marker message
        # We store it as a WorkspaceMessage with content prefixed so polling can identify it
        WorkspaceMessage.objects.create(
            workspace=ws,
            sender=request.user,  # sender field required; we override display on frontend
            content=f'[AI]{result["reply"]}',
        )

    return JsonResponse(result)


@login_required
def workspace_ai_analyze(request, ws_id):
    """Analyze workspace files and generate project brief + suggested tasks."""
    from ai_community.ai_engine import analyze_project_files as _analyze
    ws, _ = _ws_member_or_404(request, ws_id)

    files = ws.files.select_related('uploaded_by').order_by('-uploaded_at')[:10]
    members = list(
        WorkspaceMember.objects.filter(workspace=ws)
        .select_related('user')
        .values('user__username')
    )
    members_clean = [{'username': m['user__username']} for m in members]

    files_data = []
    for f in files:
        preview = ''
        try:
            # For Cloudinary/remote storage, fetch via URL; fallback to local open
            file_url = f.file.url
            if file_url.startswith('http'):
                import requests as _req
                resp = _req.get(file_url, timeout=8)
                raw_bytes = resp.content[:3000]
            else:
                f.file.open('rb')
                raw_bytes = f.file.read(3000)
                f.file.close()
            try:
                preview = raw_bytes.decode('utf-8', errors='ignore')
            except Exception:
                preview = f'[Binary file: {f.original_name}]'
        except Exception:
            preview = f'[Could not read: {f.original_name}]'
        files_data.append({'name': f.original_name, 'content_preview': preview})

    if not files_data:
        return JsonResponse({'error': 'No files uploaded yet. Upload your assignment brief first.'}, status=400)

    result = _analyze(files_data, ws.name, members_clean)
    if not result:
        return JsonResponse({'error': 'Could not analyze files. Try again.'}, status=500)

    return JsonResponse(result)


@login_required
def workspace_ai_health(request, ws_id):
    """Return project health report."""
    from ai_community.ai_engine import generate_project_health as _health
    ws, _ = _ws_member_or_404(request, ws_id)

    members = list(
        WorkspaceMember.objects.filter(workspace=ws)
        .values('user__username')
    )
    members_clean = [{'username': m['user__username']} for m in members]
    tasks = list(ws.tasks.values('title', 'status', 'assigned_to__username'))
    tasks_clean = [
        {'title': t['title'], 'status': t['status'], 'assigned_to': t['assigned_to__username']}
        for t in tasks
    ]
    files = list(ws.files.values_list('original_name', flat=True))

    result = _health(ws.name, members_clean, tasks_clean, list(files))
    return JsonResponse(result)

@login_required
@require_POST
def workspace_ai_meeting(request, ws_id):
    """Process a meeting transcript and return summary, decisions, action items."""
    import json as _json
    from ai_community.ai_engine import analyze_meeting_transcript as _meeting
    ws, _ = _ws_member_or_404(request, ws_id)

    transcript = request.POST.get('transcript', '').strip()
    if not transcript:
        try:
            body = _json.loads(request.body)
            transcript = body.get('transcript', '').strip()
        except Exception:
            pass

    if not transcript:
        return JsonResponse({'error': 'Transcript text is required.'}, status=400)

    members = list(
        WorkspaceMember.objects.filter(workspace=ws)
        .values_list('user__username', flat=True)
    )
    result = _meeting(transcript, ws.name, members)
    if not result:
        return JsonResponse({'error': 'Could not process transcript. Try again.'}, status=500)
    return JsonResponse(result)


@login_required
def workspace_ai_autocomplete(request, ws_id):
    """Generate a final document draft or presentation outline from workspace files + tasks."""
    import json as _json
    from ai_community.ai_engine import generate_autocomplete_doc as _autocomplete
    ws, _ = _ws_member_or_404(request, ws_id)

    doc_type = request.GET.get('type', 'report')  # report | slides | summary

    files = ws.files.select_related('uploaded_by').order_by('-uploaded_at')[:8]
    tasks = list(ws.tasks.values('title', 'status', 'assigned_to__username'))
    members = list(
        WorkspaceMember.objects.filter(workspace=ws)
        .values_list('user__username', flat=True)
    )

    files_data = []
    for f in files:
        preview = ''
        try:
            file_url = f.file.url
            if file_url.startswith('http'):
                import requests as _req
                resp = _req.get(file_url, timeout=8)
                raw_bytes = resp.content[:2000]
            else:
                f.file.open('rb')
                raw_bytes = f.file.read(2000)
                f.file.close()
            preview = raw_bytes.decode('utf-8', errors='ignore')
        except Exception:
            preview = f'[Could not read: {f.original_name}]'
        files_data.append({'name': f.original_name, 'content_preview': preview})

    result = _autocomplete(ws.name, list(members), tasks, files_data, doc_type)
    if not result:
        return JsonResponse({'error': 'Could not generate document. Try again.'}, status=500)
    return JsonResponse(result)


# ── GitHub-style contribution system ─────────────────────────────────────────

@login_required
@require_POST
def workspace_task_submit(request, ws_id, task_id):
    """Member submits their work for a task."""
    import json as _json
    ws, _ = _ws_member_or_404(request, ws_id)
    task = get_object_or_404(WorkspaceTask, id=task_id, workspace=ws)

    try:
        body = _json.loads(request.body)
        submission = body.get('submission', '').strip()
    except Exception:
        submission = request.POST.get('submission', '').strip()

    if not submission:
        return JsonResponse({'error': 'Submission content is required.'}, status=400)

    from django.utils import timezone
    task.submission = submission
    task.review_status = WorkspaceTask.REVIEW_PENDING
    task.submitted_at = timezone.now()
    task.status = WorkspaceTask.STATUS_DOING
    task.save(update_fields=['submission', 'review_status', 'submitted_at', 'status'])

    return JsonResponse({
        'ok': True,
        'task_id': str(task.id),
        'review_status': task.review_status,
        'message': 'Submission received. Awaiting AI review.',
    })


@login_required
def workspace_task_review(request, ws_id, task_id):
    """AI reviews a task submission and approves or requests revision."""
    from ai_community.ai_engine import review_task_submission as _review
    ws, _ = _ws_member_or_404(request, ws_id)
    task = get_object_or_404(WorkspaceTask, id=task_id, workspace=ws)

    if not task.submission:
        return JsonResponse({'error': 'No submission to review.'}, status=400)

    # Gather project context from files
    files_data = []
    for f in ws.files.order_by('-uploaded_at')[:5]:
        preview = ''
        try:
            file_url = f.file.url
            if file_url.startswith('http'):
                import requests as _req
                resp = _req.get(file_url, timeout=8)
                preview = resp.content[:1500].decode('utf-8', errors='ignore')
            else:
                f.file.open('rb')
                preview = f.file.read(1500).decode('utf-8', errors='ignore')
                f.file.close()
        except Exception:
            preview = ''
        if preview:
            files_data.append({'name': f.original_name, 'content_preview': preview})

    result = _review(
        task_title=task.title,
        task_description=task.description,
        submission=task.submission,
        workspace_name=ws.name,
        files_context=files_data,
    )

    if not result:
        return JsonResponse({'error': 'AI review failed. Try again.'}, status=500)

    # Save review result
    task.review_status = result['status']  # 'approved' or 'revision'
    task.review_feedback = result['feedback']
    if result['status'] == WorkspaceTask.REVIEW_APPROVED:
        task.status = WorkspaceTask.STATUS_DONE
    task.save(update_fields=['review_status', 'review_feedback', 'status'])

    # Post AI feedback as a system message in the workspace chat
    ai_msg = f"🤖 AI Review — *{task.title}*\n"
    ai_msg += f"Status: {'✅ Approved' if result['status'] == 'approved' else '🔄 Revision Requested'}\n"
    ai_msg += result['feedback']
    WorkspaceMessage.objects.create(
        workspace=ws,
        sender=request.user,
        content=ai_msg,
    )

    return JsonResponse(result)


@login_required
def workspace_final_assembly(request, ws_id):
    """Merge all approved task submissions into a coherent final document."""
    from ai_community.ai_engine import assemble_final_document as _assemble
    ws, _ = _ws_member_or_404(request, ws_id)

    approved_tasks = list(
        ws.tasks.filter(review_status=WorkspaceTask.REVIEW_APPROVED)
        .select_related('assigned_to')
        .values('title', 'description', 'submission', 'assigned_to__username')
    )

    if not approved_tasks:
        return JsonResponse({'error': 'No approved submissions yet. Get tasks reviewed first.'}, status=400)

    contributions = [
        {
            'title': t['title'],
            'author': t['assigned_to__username'] or 'Unknown',
            'content': t['submission'],
        }
        for t in approved_tasks
    ]

    result = _assemble(ws.name, contributions)
    if not result:
        return JsonResponse({'error': 'Assembly failed. Try again.'}, status=500)

    return JsonResponse(result)


@login_required
def workspace_ai_proactive(request, ws_id):
    """
    Called by the frontend after N new messages.
    AI reads recent chat and optionally returns a suggestion to post.
    Returns {should_post, message} — frontend decides whether to show it.
    """
    from ai_community.ai_engine import proactive_chat_suggestion as _proactive
    ws, _ = _ws_member_or_404(request, ws_id)

    recent_msgs = list(
        ws.chat_messages.order_by('-created_at')
        .values('sender__username', 'content')[:12]
    )
    recent_msgs = list(reversed(recent_msgs))

    tasks = list(ws.tasks.values('title', 'status'))
    members = list(WorkspaceMember.objects.filter(workspace=ws).values_list('user__username', flat=True))

    result = _proactive(
        workspace_name=ws.name,
        workspace_type=ws.workspace_type,
        recent_messages=recent_msgs,
        tasks=tasks,
        members=list(members),
    )
    return JsonResponse(result or {'should_post': False, 'message': ''})


@login_required
@require_POST
def workspace_ai_schedule_meeting(request, ws_id):
    """
    Nexa parses a natural-language meeting request, DMs every member,
    posts a group announcement, and returns countdown seconds so the
    frontend can auto-start the call.
    """
    import json as _json
    from ai_community.ai_engine import parse_meeting_request as _parse
    ws, _ = _ws_member_or_404(request, ws_id)

    try:
        body = _json.loads(request.body)
        message = body.get('message', '').strip()
    except Exception:
        message = ''

    if not message:
        return JsonResponse({'error': 'Message required'}, status=400)

    # Parse the meeting request with AI
    parsed = _parse(message)
    if not parsed:
        return JsonResponse({'error': 'Could not understand meeting request'}, status=400)

    delay_seconds = parsed.get('delay_seconds', 1200)   # default 20 min
    meeting_title = parsed.get('title', 'Team Meeting')
    time_label = parsed.get('time_label', 'in 20 minutes')

    # Get all workspace members
    members = list(
        WorkspaceMember.objects.filter(workspace=ws)
        .select_related('user', 'user__community_profile')
    )
    member_users = [m.user for m in members]

    # DM every member privately as Nexa (using the requester as sender proxy)
    dm_text = (
        f"👋 Hey! Nexa here.\n\n"
        f"📅 **{meeting_title}** has been scheduled for **{time_label}** "
        f"in the *{ws.name}* workspace.\n\n"
        f"The call will start automatically — just head to the workspace when it's time. See you there! 🚀"
    )

    for member_user in member_users:
        if member_user == request.user:
            continue
        try:
            # Find or create a DM conversation between requester and this member
            existing = (
                Conversation.objects.filter(participants=request.user, is_group=False)
                .filter(participants=member_user)
                .first()
            )
            if existing:
                convo = existing
            else:
                convo = Conversation.objects.create(is_group=False)
                convo.participants.set([request.user, member_user])

            Message.objects.create(
                conversation=convo,
                sender=request.user,
                content=dm_text,
            )
            Conversation.objects.filter(pk=convo.pk).update(updated_at=timezone.now())

            # Create a notification for the member
            Notification.objects.create(
                recipient=member_user,
                actor=request.user,
                type=Notification.TYPE_MESSAGE,
                conversation=convo,
            )
        except Exception:
            pass

    # Post group chat announcement from Nexa
    announce = (
        f"[AI]📅 **{meeting_title}** scheduled {time_label}.\n"
        f"I've DM'd everyone with the details. The call will start automatically — "
        f"I'll ping you here when it's time! ⏰"
    )
    WorkspaceMessage.objects.create(
        workspace=ws,
        sender=request.user,
        content=announce,
    )

    return JsonResponse({
        'ok': True,
        'meeting_title': meeting_title,
        'time_label': time_label,
        'delay_seconds': delay_seconds,
    })


@login_required
@require_POST
def workspace_ai_deep_search(request, ws_id):
    """
    Nexa performs a deep web search and posts the results to the group chat.
    """
    import json as _json
    from ai_community.ai_engine import deep_search as _deep_search
    ws, _ = _ws_member_or_404(request, ws_id)

    try:
        body = _json.loads(request.body)
        query = body.get('query', '').strip()
    except Exception:
        query = ''

    if not query:
        return JsonResponse({'error': 'Query required'}, status=400)

    # Pass workspace context so results can be relevant
    ws_context = f"Workspace: {ws.name}, Type: {ws.workspace_type}"
    result = _deep_search(query, workspace_context=ws_context)

    if not result:
        return JsonResponse({'error': 'Search failed'}, status=500)

    # Save a compact version to group chat so all members see it
    summary_msg = (
        f"[AI]🔍 **Deep Search: {query}**\n\n"
        f"{result.get('summary', '')}\n\n"
        f"**Key Findings:**\n" +
        '\n'.join(f"• {f}" for f in result.get('key_findings', [])[:5])
    )
    WorkspaceMessage.objects.create(
        workspace=ws,
        sender=request.user,
        content=summary_msg,
    )

    return JsonResponse({'ok': True, 'result': result})


@login_required
def workspace_meeting_records(request, ws_id):
    """Return all meeting records for a workspace."""
    from community.models import MeetingRecord
    ws, _ = _ws_member_or_404(request, ws_id)
    records = MeetingRecord.objects.filter(workspace=ws).order_by('-started_at')[:20]
    data = []
    for r in records:
        duration = None
        if r.ended_at and r.started_at:
            duration = max(1, int((r.ended_at - r.started_at).total_seconds() / 60))
        data.append({
            'id': str(r.id),
            'started_at': r.started_at.strftime('%b %d, %Y %H:%M'),
            'ended_at': r.ended_at.strftime('%H:%M') if r.ended_at else None,
            'duration_mins': duration,
            'participants': r.participants,
            'ai_summary': r.ai_summary,
            'decisions': r.decisions,
            'action_items': r.action_items,
            'key_topics': r.key_topics,
            'chat_log': r.chat_log,
        })
    return JsonResponse({'records': data})


@login_required
@require_POST
def workspace_meeting_summarize(request, ws_id, record_id):
    """Manually trigger AI summary for a specific meeting record."""
    import json as _json
    from community.models import MeetingRecord
    from ai_community.ai_engine import analyze_meeting_transcript
    ws, _ = _ws_member_or_404(request, ws_id)
    record = get_object_or_404(MeetingRecord, id=record_id, workspace=ws)

    all_members = list(WorkspaceMember.objects.filter(workspace=ws).values_list('user__username', flat=True))
    analysis = analyze_meeting_transcript(
        messages=record.chat_log,
        workspace_name=ws.name,
        members=all_members,
    )
    if analysis:
        record.ai_summary = analysis.get('summary', '')
        record.decisions = analysis.get('decisions', [])
        record.action_items = analysis.get('action_items', [])
        record.key_topics = analysis.get('key_topics', [])
        record.save()
        return JsonResponse({'ok': True, 'summary': record.ai_summary, 'decisions': record.decisions, 'action_items': record.action_items})
    return JsonResponse({'error': 'Could not generate summary'}, status=500)
