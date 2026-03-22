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
    HelpBeacon,
    Message,
    MicroRoom,
    NexaWorkspaceLink,
    Notification,
    Post,
    PostLike,
    PulseEvent,
    SchoolCommunity,
    SkillOffer,
    Startup,
    WorkspaceFile,
    WorkspaceMember,
    WorkspaceMessage,
    WorkspaceTask,
    MicroRoomParticipant,
    RoomSignal,
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
        # Personal workspace — any is_personal=True workspace
        personal_ws = GroupWorkspace.objects.filter(
            owner=request.user, is_personal=True, is_active=True,
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
        'last_workspace': last_workspace,
        'unread_msgs': unread_msgs,
        'workspace_type_choices': GroupWorkspace.TYPE_CHOICES,
        'show_onboarding': not request.user.onboarding_complete,
        'all_schools': list(SchoolCommunity.objects.filter(is_active=True).values('id', 'name', 'logo_url').order_by('name')),
        'ob_interest_tags': [
            'Mathematics', 'Science', 'Engineering', 'Business', 'Arts', 'Law',
            'Medicine', 'Technology', 'Sports', 'Music', 'Literature', 'Economics',
            'Psychology', 'Design', 'History', 'Politics', 'Philosophy',
            'Computer Science', 'Finance', 'Education',
        ],
    })


# ── Onboarding ────────────────────────────────────────────────────────────────

@login_required
@require_POST
def onboarding_join_school(request):
    """Step 1: join a school community (or skip)."""
    import json as _json
    data = _json.loads(request.body)
    school_id = data.get('school_id')
    if school_id:
        try:
            school = SchoolCommunity.objects.get(id=school_id, is_active=True)
            CommunityMembership.objects.get_or_create(
                user=request.user,
                community=school,
                defaults={'role': CommunityMembership.ROLE_MEMBER},
            )
        except SchoolCommunity.DoesNotExist:
            pass
    return JsonResponse({'ok': True})


@login_required
@require_POST
def onboarding_save_profile(request):
    """Step 2: save display name, bio, interests, avatar to CommunityProfile."""
    profile, _ = CommunityProfile.objects.get_or_create(user=request.user)
    display_name = request.POST.get('display_name', '').strip()
    bio = request.POST.get('bio', '').strip()
    interests = request.POST.get('interests', '').strip()
    if display_name:
        profile.display_name = display_name
    if bio:
        profile.bio = bio
    if interests:
        profile.interests = interests
    if 'avatar' in request.FILES:
        profile.avatar = request.FILES['avatar']
    profile.save()
    return JsonResponse({'ok': True})


@login_required
@require_POST
def onboarding_follow_users(request):
    """Step 3: follow suggested users (or skip). Marks onboarding complete."""
    import json as _json
    from community.models import Follow
    data = _json.loads(request.body)
    usernames = data.get('usernames', [])
    for uname in usernames:
        try:
            target = User.objects.get(username=uname)
            if target != request.user:
                Follow.objects.get_or_create(follower=request.user, following=target)
        except User.DoesNotExist:
            pass
    # Mark onboarding done regardless of whether they followed anyone
    request.user.onboarding_complete = True
    request.user.save(update_fields=['onboarding_complete'])
    return JsonResponse({'ok': True})


@login_required
def onboarding_suggested_users(request):
    """Return users who share school community or interests with the current user."""
    from community.models import Follow, CommunityProfile
    # Get schools the user just joined or is in
    my_school_ids = CommunityMembership.objects.filter(
        user=request.user
    ).values_list('community_id', flat=True)

    already_following = Follow.objects.filter(
        follower=request.user
    ).values_list('following_id', flat=True)

    # Get current user's interests
    my_interests = set()
    try:
        my_profile = request.user.community_profile
        if my_profile.interests:
            my_interests = {i.strip().lower() for i in my_profile.interests.split(',') if i.strip()}
    except Exception:
        pass

    if my_school_ids:
        candidates = User.objects.filter(
            community_memberships__community_id__in=my_school_ids
        ).exclude(
            id=request.user.id
        ).exclude(
            id__in=already_following
        ).distinct()[:40]
    else:
        candidates = User.objects.exclude(id=request.user.id).order_by('-date_joined')[:40]

    def _score(u):
        """Higher score = better match."""
        score = 0
        try:
            p = u.community_profile
            if p.interests and my_interests:
                other = {i.strip().lower() for i in p.interests.split(',') if i.strip()}
                score = len(my_interests & other)
        except Exception:
            pass
        return score

    scored = sorted(candidates, key=_score, reverse=True)[:20]

    users_data = []
    for u in scored:
        try:
            avatar = u.community_profile.avatar.url if u.community_profile.avatar else None
            interests_list = [i.strip() for i in (u.community_profile.interests or '').split(',') if i.strip()]
        except Exception:
            avatar = None
            interests_list = []
        users_data.append({
            'username': u.username,
            'display_name': getattr(getattr(u, 'community_profile', None), 'display_name', '') or u.username,
            'avatar': avatar,
            'interests': interests_list[:3],
        })
    return JsonResponse({'users': users_data})


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
        # "Following" tab — only posts from people you follow + communities you're in
        from django.db.models import Q
        following_ids = Follow.objects.filter(follower=request.user).values_list('following_id', flat=True)
        joined_school_ids = CommunityMembership.objects.filter(user=request.user).values_list('community_id', flat=True)
        joined_custom_ids = CustomCommunityMembership.objects.filter(user=request.user).values_list('community_id', flat=True)
        qs = qs.filter(
            Q(author_id__in=following_ids) |
            Q(author=request.user) |
            Q(school_community_id__in=joined_school_ids) |
            Q(custom_community_id__in=joined_custom_ids)
        ).distinct()
    elif tab == 'liked':
        # "Liked" tab — only posts this user has liked
        liked_post_ids = PostLike.objects.filter(user=request.user).values_list('post_id', flat=True)
        qs = qs.filter(id__in=liked_post_ids)
    # "For You" (tab == 'all') — all posts, no filter

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


@login_required
@require_POST
def upload_avatar(request):
    """Quick AJAX avatar upload from the home page avatar widget."""
    if 'avatar' not in request.FILES:
        return JsonResponse({'ok': False, 'error': 'No file'}, status=400)
    profile, _ = CommunityProfile.objects.get_or_create(user=request.user)
    profile.avatar = request.FILES['avatar']
    profile.save(update_fields=['avatar'])
    return JsonResponse({'ok': True, 'url': profile.avatar.url})


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
    """Personal Nexa AI page — SciSpace-style interface."""
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
    return render(request, 'community/nexa_home.html', {'ws': ws})


@login_required
@require_POST
def nexa_link_workspace(request, ws_id):
    """Toggle link between user's Nexa workspace and a group workspace."""
    group_ws = get_object_or_404(GroupWorkspace, id=ws_id, is_active=True)
    # Must be a member of the group workspace
    if not WorkspaceMember.objects.filter(workspace=group_ws, user=request.user).exists():
        return JsonResponse({'error': 'Not a member of that workspace.'}, status=403)

    nexa_ws = GroupWorkspace.objects.filter(
        owner=request.user,
        workspace_type=GroupWorkspace.TYPE_NEXA,
        is_personal=True,
    ).first()
    if not nexa_ws:
        # Auto-create the Nexa workspace so the user doesn't have to navigate away
        nexa_ws = GroupWorkspace.objects.create(
            name='My Nexa Workspace',
            description='Your personal AI-powered learning hub.',
            workspace_type=GroupWorkspace.TYPE_NEXA,
            privacy=GroupWorkspace.PRIVACY_PRIVATE,
            owner=request.user,
            is_personal=True,
        )
        WorkspaceMember.objects.create(
            workspace=nexa_ws,
            user=request.user,
            role=WorkspaceMember.ROLE_OWNER,
        )

    link, created = NexaWorkspaceLink.objects.get_or_create(
        nexa_workspace=nexa_ws,
        linked_workspace=group_ws,
    )
    if not created:
        link.delete()
        return JsonResponse({'ok': True, 'linked': False})
    return JsonResponse({'ok': True, 'linked': True})


@login_required
def nexa_my_tasks(request):
    """Return tasks assigned to the user across all linked workspaces."""
    nexa_ws = GroupWorkspace.objects.filter(
        owner=request.user,
        workspace_type=GroupWorkspace.TYPE_NEXA,
        is_personal=True,
    ).first()
    if not nexa_ws:
        return JsonResponse({'tasks': []})

    linked_ws_ids = NexaWorkspaceLink.objects.filter(
        nexa_workspace=nexa_ws,
    ).values_list('linked_workspace_id', flat=True)

    tasks = WorkspaceTask.objects.filter(
        workspace_id__in=linked_ws_ids,
        assigned_to=request.user,
    ).exclude(status=WorkspaceTask.STATUS_DONE).select_related('workspace').order_by('due_date', 'created_at')

    data = []
    for t in tasks:
        data.append({
            'id': str(t.id),
            'title': t.title,
            'description': t.description,
            'status': t.status,
            'due_date': t.due_date.isoformat() if t.due_date else None,
            'workspace_id': str(t.workspace_id),
            'workspace_name': t.workspace.name,
            'review_status': t.review_status,
        })
    return JsonResponse({'tasks': data})


@login_required
@require_POST
def nexa_submit_task(request, task_id):
    """Submit task content from Nexa workspace — pushes to group workspace files."""
    import json as _json
    from django.utils import timezone

    task = get_object_or_404(WorkspaceTask, id=task_id, assigned_to=request.user)
    try:
        body = _json.loads(request.body)
    except Exception:
        body = {}

    content = body.get('content', '').strip()
    if not content:
        return JsonResponse({'error': 'No content provided.'}, status=400)

    # Save submission on the task
    task.submission = content
    task.review_status = WorkspaceTask.REVIEW_PENDING
    task.submitted_at = timezone.now()
    task.status = WorkspaceTask.STATUS_DOING
    task.save(update_fields=['submission', 'review_status', 'submitted_at', 'status'])

    # Save as a text file in the group workspace
    import io
    from django.core.files.base import ContentFile
    file_content = f"Task: {task.title}\nSubmitted by: {request.user.username}\n\n{content}"
    file_name = f"{task.title[:40].replace(' ', '_')}_{request.user.username}.txt"
    wf = WorkspaceFile(
        workspace=task.workspace,
        uploaded_by=request.user,
        original_name=file_name,
        file_size=len(file_content.encode()),
    )
    wf.file.save(file_name, ContentFile(file_content.encode()), save=True)

    return JsonResponse({'ok': True, 'task_id': str(task.id), 'file_name': file_name})


def _auto_link_nexa(user, group_ws):
    """Ensure the user's Nexa workspace is linked to group_ws. Creates Nexa ws if needed."""
    if group_ws.workspace_type == GroupWorkspace.TYPE_NEXA:
        return  # don't link a nexa ws to itself
    nexa_ws = GroupWorkspace.objects.filter(
        owner=user,
        workspace_type=GroupWorkspace.TYPE_NEXA,
        is_personal=True,
    ).first()
    if not nexa_ws:
        nexa_ws = GroupWorkspace.objects.create(
            name='My Nexa Workspace',
            description='Your personal AI-powered learning hub.',
            workspace_type=GroupWorkspace.TYPE_NEXA,
            privacy=GroupWorkspace.PRIVACY_PRIVATE,
            owner=user,
            is_personal=True,
        )
        WorkspaceMember.objects.create(
            workspace=nexa_ws,
            user=user,
            role=WorkspaceMember.ROLE_OWNER,
        )
    NexaWorkspaceLink.objects.get_or_create(
        nexa_workspace=nexa_ws,
        linked_workspace=group_ws,
    )


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
        _auto_link_nexa(request.user, ws)

        # Add selected members
        usernames = request.POST.getlist('members')
        for uname in usernames:
            try:
                u = User.objects.get(username=uname)
                if u != request.user:
                    WorkspaceMember.objects.get_or_create(workspace=ws, user=u, defaults={'role': WorkspaceMember.ROLE_MEMBER})
                    _auto_link_nexa(u, ws)
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

    # Nexa link context
    nexa_ws = GroupWorkspace.objects.filter(
        owner=request.user,
        workspace_type=GroupWorkspace.TYPE_NEXA,
        is_personal=True,
    ).first()
    is_linked_to_nexa = False
    if nexa_ws and ws.workspace_type != GroupWorkspace.TYPE_NEXA:
        is_linked_to_nexa = NexaWorkspaceLink.objects.filter(
            nexa_workspace=nexa_ws,
            linked_workspace=ws,
        ).exists()

    # For nexa workspaces: pass linked group workspaces and assigned tasks
    linked_workspaces = []
    my_tasks = []
    if ws.workspace_type == GroupWorkspace.TYPE_NEXA:
        links = NexaWorkspaceLink.objects.filter(
            nexa_workspace=ws,
        ).select_related('linked_workspace')
        linked_workspaces = [lnk.linked_workspace for lnk in links]
        linked_ws_ids = [lw.id for lw in linked_workspaces]
        my_tasks = WorkspaceTask.objects.filter(
            workspace_id__in=linked_ws_ids,
            assigned_to=request.user,
        ).select_related('workspace').order_by('due_date', 'created_at')

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
        'is_linked_to_nexa': is_linked_to_nexa,
        'linked_workspaces': linked_workspaces,
        'my_tasks': my_tasks,
        'nexa_ws': nexa_ws,
    })


@login_required
def workspace_join(request, invite_code):
    """Join a workspace via invite code."""
    ws = get_object_or_404(GroupWorkspace, invite_code=invite_code, is_active=True)
    _, created = WorkspaceMember.objects.get_or_create(
        workspace=ws, user=request.user,
        defaults={'role': WorkspaceMember.ROLE_MEMBER}
    )
    _auto_link_nexa(request.user, ws)
    return redirect('community:workspace_detail', ws_id=ws.id)


@login_required
@require_POST
def workspace_delete_message(request, ws_id, msg_id):
    ws, _ = _ws_member_or_404(request, ws_id)
    try:
        msg = ws.chat_messages.get(id=msg_id, sender=request.user)
    except WorkspaceMessage.DoesNotExist:
        return JsonResponse({'error': 'Not found or not yours'}, status=404)
    msg.delete()
    return JsonResponse({'ok': True})


@login_required
@require_POST
def workspace_send_message(request, ws_id):
    ws, _ = _ws_member_or_404(request, ws_id)
    content = request.POST.get('content', '').strip()
    file = request.FILES.get('file')
    reply_to_id = request.POST.get('reply_to_id', '').strip()
    if not content and not file:
        return JsonResponse({'error': 'Empty message'}, status=400)

    msg = WorkspaceMessage(workspace=ws, sender=request.user, content=content)
    if file:
        msg.media = file
        msg.media_name = file.name
    if reply_to_id:
        try:
            msg.reply_to_id = reply_to_id
        except Exception:
            pass
    msg.save()
    ws.updated_at = timezone.now()
    ws.save(update_fields=['updated_at'])

    avatar = None
    try:
        avatar = request.user.community_profile.avatar.url if request.user.community_profile.avatar else None
    except Exception:
        pass

    reply_preview = None
    if msg.reply_to_id:
        try:
            rt = msg.reply_to
            is_ai = rt.content.startswith('[AI]')
            reply_preview = {
                'id': str(rt.id),
                'sender': 'Nexa' if is_ai else rt.sender.username,
                'content': rt.content[4:] if is_ai else rt.content,
            }
        except Exception:
            pass

    return JsonResponse({
        'id': str(msg.id),
        'content': msg.content,
        'sender': request.user.username,
        'sender_avatar': avatar,
        'media_url': msg.media.url if msg.media else None,
        'media_name': msg.media_name,
        'reply_preview': reply_preview,
        'created_at': msg.created_at.isoformat(),
    })


@login_required
def workspace_poll_messages(request, ws_id):
    ws, _ = _ws_member_or_404(request, ws_id)
    since_raw = request.GET.get('since')
    qs = ws.chat_messages.select_related(
        'sender', 'sender__community_profile',
        'reply_to', 'reply_to__sender'
    ).order_by('created_at')
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

        reply_preview = None
        if msg.reply_to_id:
            try:
                rt = msg.reply_to
                rt_is_ai = rt.content.startswith('[AI]')
                reply_preview = {
                    'id': str(rt.id),
                    'sender': 'Nexa' if rt_is_ai else rt.sender.username,
                    'content': (rt.content[4:] if rt_is_ai else rt.content)[:80],
                }
            except Exception:
                pass

        data.append({
            'id': str(msg.id),
            'content': content,
            'sender': 'Nexa' if is_ai_msg else msg.sender.username,
            'sender_avatar': avatar,
            'is_mine': (not is_ai_msg) and (msg.sender_id == request.user.id),
            'is_ai': is_ai_msg,
            'media_url': msg.media.url if msg.media else None,
            'media_name': msg.media_name,
            'reply_preview': reply_preview,
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
    _auto_link_nexa(u, ws)
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

    # Pass last 60 messages so Nexa has full conversation context
    recent_chat = list(
        ws.chat_messages.order_by('-created_at')
        .values('sender__username', 'content')[:60]
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
        WorkspaceMessage.objects.create(
            workspace=ws,
            sender=request.user,
            content=f'[AI]{result["reply"]}',
        )

    # Auto deep search triggered by Nexa internally
    if result.get('deep_search'):
        search_result = result['deep_search']
        search_query = result.get('search_query', '')
        summary_msg = (
            f"[AI]🔍 **{search_query}**\n\n"
            f"{search_result.get('summary', '')}\n\n"
            + '\n'.join(f"• {f}" for f in search_result.get('key_findings', [])[:5])
        )
        WorkspaceMessage.objects.create(
            workspace=ws,
            sender=request.user,
            content=summary_msg,
        )
        return JsonResponse({'reply': '', 'actions': [], 'deep_search': search_result})

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


# ── Paraphraser ───────────────────────────────────────────────────────────────

@login_required
@require_POST
def paraphrase_ajax(request):
    """
    Advanced AI paraphraser endpoint.
    Accepts JSON: {text, mode, style_sample, subject}
    Returns JSON: {paraphrased, changes, explanation}
    """
    import json as _json
    import os, re

    try:
        body = _json.loads(request.body)
    except Exception:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    text = (body.get('text') or '').strip()
    mode = (body.get('mode') or 'simple').strip().lower()
    style_sample = (body.get('style_sample') or '').strip()
    subject = (body.get('subject') or '').strip()

    if not text:
        return JsonResponse({'error': 'No text provided'}, status=400)
    if len(text) > 8000:
        return JsonResponse({'error': 'Text too long (max 8000 chars)'}, status=400)

    MODE_INSTRUCTIONS = {
        'simple':   'Rewrite in very simple, easy-to-understand English. Use short sentences. Explain like a teacher to a beginner.',
        'academic': 'Rewrite in formal academic style. Use scholarly vocabulary, complex sentence structures, and passive voice where appropriate.',
        'exam':     'Rewrite as a WAEC/SHS exam-ready answer. Be structured, use key terms, include relevant points a student should mention.',
        'short':    'Rewrite as a concise, compressed version. Remove all redundancy. Keep only the core meaning.',
        'expanded': 'Rewrite with more explanation and detail. Add context, examples, and elaboration to make the content richer.',
        'creative': 'Rewrite in a vivid, expressive, and engaging style. Use metaphors, varied sentence rhythm, and interesting word choices.',
        'bullet':   'Convert the text into clear, well-organised bullet points. Each bullet should be a distinct idea.',
    }

    mode_instruction = MODE_INSTRUCTIONS.get(mode, MODE_INSTRUCTIONS['simple'])

    style_block = ''
    if style_sample:
        style_block = f'\n\nSTYLE CLONING: The user has provided a sample of their writing style. Mirror this tone and voice in your output:\n"""\n{style_sample[:600]}\n"""'

    subject_block = ''
    if subject:
        subject_block = f'\n\nSUBJECT CONTEXT: This text is about "{subject}". Align vocabulary and framing to this subject area.'

    system_prompt = (
        "You are Nexa Smart Paraphraser — an advanced AI writing assistant for students.\n"
        "Your job is to paraphrase text intelligently while teaching the user what changed and why.\n\n"
        "RULES:\n"
        "- Preserve the original meaning 100%\n"
        "- Never distort facts or arguments\n"
        "- Output must sound natural and human-like\n"
        "- Avoid plagiarism by restructuring sentences significantly\n\n"
        "RESPONSE FORMAT (strict JSON, no markdown):\n"
        "{\n"
        '  "paraphrased": "<the rewritten text>",\n'
        '  "changes": [\n'
        '    {"original": "...", "replacement": "...", "reason": "..."}\n'
        "  ],\n"
        '  "explanation": "<2-3 sentence tutor note explaining the overall approach and what improved>"\n'
        "}"
    )

    user_prompt = (
        f"MODE: {mode.upper()} — {mode_instruction}"
        f"{style_block}{subject_block}\n\n"
        f"TEXT TO PARAPHRASE:\n\"\"\"\n{text}\n\"\"\""
    )

    try:
        from openai import OpenAI
        client = OpenAI(api_key=os.environ.get('OPENAI_API_KEY', ''))
        response = client.chat.completions.create(
            model='gpt-4o-mini',
            messages=[
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': user_prompt},
            ],
            temperature=0.7,
            max_tokens=2000,
            response_format={'type': 'json_object'},
        )
        raw = response.choices[0].message.content
        result = _json.loads(raw)
        return JsonResponse({
            'paraphrased': result.get('paraphrased', ''),
            'changes': result.get('changes', []),
            'explanation': result.get('explanation', ''),
        })
    except Exception as e:
        return JsonResponse({'error': f'AI error: {str(e)}'}, status=500)


# ── Citation Intelligence Engine ──────────────────────────────────────────────

@login_required
@require_POST
def citation_ajax(request):
    """
    Nexa Citation Intelligence Engine.
    Actions: detect | generate | fix
    """
    import json as _json
    import os

    try:
        body = _json.loads(request.body)
    except Exception:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    action = body.get('action', 'generate')

    try:
        from openai import OpenAI
        client = OpenAI(api_key=os.environ.get('OPENAI_API_KEY', ''))
    except Exception as e:
        return JsonResponse({'error': f'AI unavailable: {e}'}, status=500)

    # ── ACTION: detect metadata from URL/DOI ──────────────────────────────────
    if action == 'detect':
        url = (body.get('url') or '').strip()
        source_type = (body.get('source_type') or 'website').strip()
        if not url:
            return JsonResponse({'error': 'No URL provided'}, status=400)

        # Try CrossRef for DOIs
        metadata = {}
        if url.startswith('10.') or 'doi.org' in url:
            try:
                import urllib.request
                doi = url.replace('https://doi.org/', '').replace('http://doi.org/', '')
                api_url = f'https://api.crossref.org/works/{doi}'
                req = urllib.request.Request(api_url, headers={'User-Agent': 'Nexa/1.0'})
                with urllib.request.urlopen(req, timeout=6) as resp:
                    cr = _json.loads(resp.read())
                msg = cr.get('message', {})
                authors = msg.get('author', [])
                author_str = '; '.join(
                    f"{a.get('family', '')}, {a.get('given', '')}" for a in authors[:3]
                ).strip('; ')
                issued = msg.get('issued', {}).get('date-parts', [['']])[0]
                year = str(issued[0]) if issued else ''
                metadata = {
                    'author': author_str,
                    'title': ' '.join(msg.get('title', [])),
                    'year': year,
                    'publisher': msg.get('publisher', ''),
                    'journal': ' '.join(msg.get('container-title', [])),
                    'volume': msg.get('volume', ''),
                    'issue': msg.get('issue', ''),
                    'pages': msg.get('page', ''),
                    'doi': doi,
                }
            except Exception:
                pass

        # Fallback: AI-based metadata extraction
        if not metadata.get('title'):
            prompt = (
                f"Extract metadata from this source URL/text: {url}\n"
                f"Source type: {source_type}\n\n"
                "Return strict JSON with keys: author, title, year, publisher, accessed\n"
                "If a field is unknown, use empty string. Today's date for accessed if it's a website."
            )
            try:
                resp = client.chat.completions.create(
                    model='gpt-4o-mini',
                    messages=[
                        {'role': 'system', 'content': 'You are a metadata extraction assistant. Return only valid JSON.'},
                        {'role': 'user', 'content': prompt},
                    ],
                    temperature=0.2,
                    max_tokens=400,
                    response_format={'type': 'json_object'},
                )
                metadata = _json.loads(resp.choices[0].message.content)
            except Exception as e:
                return JsonResponse({'error': f'Detection failed: {e}'}, status=500)

        return JsonResponse({'metadata': metadata})

    # ── ACTION: generate citation ─────────────────────────────────────────────
    elif action == 'generate':
        style = (body.get('style') or 'APA').strip()
        source_type = (body.get('source_type') or 'website').strip()

        fields = {
            'author': body.get('author', ''),
            'title': body.get('title', ''),
            'year': body.get('year', ''),
            'publisher': body.get('publisher', ''),
            'volume': body.get('volume', ''),
            'pages': body.get('pages', ''),
            'url': body.get('url', ''),
            'doi': body.get('doi', ''),
            'accessed': body.get('accessed', ''),
        }

        STYLE_NOTES = {
            'APA': 'APA 7th edition. Author, A. A. (Year). Title. Publisher. https://doi.org/xxx',
            'MLA': 'MLA 9th edition. Author Last, First. "Title." Publisher, Year, URL.',
            'Harvard': 'Harvard referencing. Author (Year) Title. Publisher.',
            'Chicago': 'Chicago 17th edition author-date or notes-bibliography.',
            'IEEE': 'IEEE style. [1] A. Author, "Title," Journal, vol. x, no. x, pp. xx–xx, Year.',
            'WAEC': 'Simplified WAEC/SHS style. Easy format for secondary school students. Author (Year). Title. Publisher.',
        }

        system_prompt = (
            "You are Nexa Citation Intelligence Engine — an expert academic citation assistant.\n"
            "Generate a perfectly formatted citation AND teach the user what each part means.\n\n"
            "RESPONSE FORMAT (strict JSON, no markdown):\n"
            "{\n"
            '  "citation": "<full formatted citation string>",\n'
            '  "in_text": "<in-text citation e.g. (Smith, 2020)>",\n'
            '  "style": "<style name>",\n'
            '  "parts": [\n'
            '    {"label": "Author", "value": "...", "why": "Author comes first in APA because..."}\n'
            "  ],\n"
            '  "note": "<optional tip for the student>",\n'
            '  "credibility": {"score": 75, "label": "Reliable Academic Source", "reasons": ["..."]}\n'
            "}"
        )

        user_prompt = (
            f"Generate a {style} citation for this {source_type}.\n"
            f"Style guide: {STYLE_NOTES.get(style, style)}\n\n"
            f"Fields provided:\n"
            + '\n'.join(f"  {k}: {v}" for k, v in fields.items() if v)
            + "\n\nIf any required fields are missing, infer or note them gracefully."
        )

        try:
            resp = client.chat.completions.create(
                model='gpt-4o-mini',
                messages=[
                    {'role': 'system', 'content': system_prompt},
                    {'role': 'user', 'content': user_prompt},
                ],
                temperature=0.3,
                max_tokens=1200,
                response_format={'type': 'json_object'},
            )
            result = _json.loads(resp.choices[0].message.content)
            return JsonResponse(result)
        except Exception as e:
            return JsonResponse({'error': f'Generation failed: {e}'}, status=500)

    # ── ACTION: fix/reformat citation ─────────────────────────────────────────
    elif action == 'fix':
        raw = (body.get('raw_citation') or '').strip()
        style = (body.get('style') or 'APA').strip()
        if not raw:
            return JsonResponse({'error': 'No citation provided'}, status=400)
        if len(raw) > 2000:
            return JsonResponse({'error': 'Citation too long'}, status=400)

        system_prompt = (
            "You are a citation correction expert. The user has pasted a messy or incorrectly formatted citation.\n"
            "Fix it, reformat it to the requested style, and explain what was wrong.\n\n"
            "RESPONSE FORMAT (strict JSON):\n"
            "{\n"
            '  "citation": "<corrected citation>",\n'
            '  "in_text": "<in-text citation>",\n'
            '  "style": "<style>",\n'
            '  "parts": [{"label": "...", "value": "...", "why": "..."}],\n'
            '  "note": "<what was wrong and what was fixed>",\n'
            '  "credibility": {"score": 0, "label": "", "reasons": []}\n'
            "}"
        )

        try:
            resp = client.chat.completions.create(
                model='gpt-4o-mini',
                messages=[
                    {'role': 'system', 'content': system_prompt},
                    {'role': 'user', 'content': f"Fix this citation to {style} style:\n\n{raw}"},
                ],
                temperature=0.2,
                max_tokens=1000,
                response_format={'type': 'json_object'},
            )
            result = _json.loads(resp.choices[0].message.content)
            return JsonResponse(result)
        except Exception as e:
            return JsonResponse({'error': f'Fix failed: {e}'}, status=500)

    return JsonResponse({'error': 'Unknown action'}, status=400)


# ═══════════════════════════════════════════════════════════════════════════════
# LIVE CAMPUS VIEWS
# ═══════════════════════════════════════════════════════════════════════════════

from community.models import (
    SkillOffer, SkillDeal, Confession, ConfessionUpvote, ConfessionReply,
    Startup, StartupMember, StartupUpdate, StartupFollow,
    PulseEvent, PulseJoin, MicroRoom, MicroRoomParticipant, HelpBeacon,
)


# ── Live Campus Hub ───────────────────────────────────────────────────────────

@login_required
def live_campus(request):
    """The unified Live Campus tab — Pulse + Help + Voice Rooms + Startups + Skills + Feed."""
    from django.utils.dateparse import parse_datetime
    from community.models import Follow
    now = timezone.now()

    pulse_events = list(PulseEvent.objects.filter(
        expires_at__gt=now, is_private=False
    ).select_related('host', 'host__community_profile').order_by('expires_at')[:12])

    micro_rooms = list(MicroRoom.objects.filter(
        status=MicroRoom.STATUS_OPEN
    ).select_related('host', 'host__community_profile').order_by('-created_at')[:8])

    help_beacons = list(HelpBeacon.objects.filter(
        status=HelpBeacon.STATUS_OPEN
    ).select_related('requester', 'requester__community_profile').order_by('-created_at')[:8])

    skill_offers = list(SkillOffer.objects.filter(
        status=SkillOffer.STATUS_OPEN
    ).select_related('user', 'user__community_profile').order_by('-created_at')[:8])

    startups = list(Startup.objects.filter(
        is_active=True
    ).select_related('founder', 'founder__community_profile').order_by('-updated_at')[:6])

    # Feed posts (all, paginated)
    cursor = request.GET.get('cursor')
    limit = 15
    feed_qs = Post.objects.filter(is_deleted=False).select_related(
        'author', 'author__community_profile', 'school_community', 'custom_community'
    ).order_by('-created_at')
    if cursor:
        cursor_dt = parse_datetime(cursor)
        if cursor_dt:
            feed_qs = feed_qs.filter(created_at__lt=cursor_dt)
    feed_posts = list(feed_qs[:limit + 1])
    has_more = len(feed_posts) > limit
    if has_more:
        feed_posts = feed_posts[:limit]
    next_cursor = feed_posts[-1].created_at.isoformat() if has_more and feed_posts else None
    post_ids = [p.id for p in feed_posts]
    liked_ids = set(PostLike.objects.filter(user=request.user, post_id__in=post_ids).values_list('post_id', flat=True))
    following_user_ids = set(Follow.objects.filter(follower=request.user).values_list('following_id', flat=True))

    return render(request, 'community/live_campus.html', {
        'pulse_events': pulse_events,
        'rooms': micro_rooms,
        'beacons': help_beacons,
        'skill_offers': skill_offers,
        'startups': startups,
        'pulse_count': len(pulse_events),
        'beacon_count': HelpBeacon.objects.filter(status=HelpBeacon.STATUS_OPEN).count(),
        'room_count': MicroRoom.objects.filter(status=MicroRoom.STATUS_OPEN).count(),
        'startup_count': Startup.objects.filter(is_active=True).count(),
        'skill_count': SkillOffer.objects.filter(status=SkillOffer.STATUS_OPEN).count(),
        'categories': HelpBeacon.CAT_CHOICES,
        'now': now,
        # feed
        'feed_posts': feed_posts,
        'has_more': has_more,
        'next_cursor': next_cursor,
        'liked_ids': liked_ids,
        'following_user_ids': following_user_ids,
    })


# ── Skill Marketplace ─────────────────────────────────────────────────────────

@login_required
def skill_marketplace(request):
    """Browse all skill offers and requests."""
    tag = request.GET.get('tag', '')
    listing_type = request.GET.get('type', '')
    qs = SkillOffer.objects.filter(status=SkillOffer.STATUS_OPEN).select_related(
        'user', 'user__community_profile', 'school_community'
    )
    if tag:
        qs = qs.filter(skill_tag__iexact=tag)
    if listing_type in ('offer', 'request'):
        qs = qs.filter(listing_type=listing_type)
    offers = qs.order_by('-created_at')[:40]
    from community.models import SKILL_TAGS
    return render(request, 'community/skill_marketplace.html', {
        'offers': offers,
        'skill_tags': SKILL_TAGS,
        'active_tag': tag,
        'active_type': listing_type,
    })


@login_required
def skill_offer_create(request):
    """Create a skill offer or request."""
    if request.method == 'GET':
        return render(request, 'community/skill_offer_create.html')
    import json as _json
    try:
        data = _json.loads(request.body)
    except Exception:
        data = request.POST
    title = data.get('title', '').strip()
    skill_tag = data.get('skill_tag', '').strip()
    if not title or not skill_tag:
        return JsonResponse({'error': 'Title and skill tag required'}, status=400)
    offer = SkillOffer.objects.create(
        user=request.user,
        listing_type=data.get('listing_type', 'offer'),
        title=title,
        description=data.get('description', '').strip(),
        skill_tag=skill_tag,
        wants_tag=data.get('wants_tag', '').strip(),
        urgency=data.get('urgency', 'low'),
    )
    if request.content_type and 'json' in request.content_type:
        return JsonResponse({'ok': True, 'id': str(offer.id)})
    from django.shortcuts import redirect
    return redirect('community:skill_marketplace')


@login_required
@require_POST
def skill_deal_initiate(request, offer_id):
    """Initiate a barter deal on a skill offer."""
    import json as _json
    offer = get_object_or_404(SkillOffer, id=offer_id, status=SkillOffer.STATUS_OPEN)
    if offer.user == request.user:
        return JsonResponse({'error': 'Cannot deal with yourself'}, status=400)
    try:
        data = _json.loads(request.body)
    except Exception:
        data = {}
    # Create or find DM conversation
    existing = (
        Conversation.objects.filter(participants=request.user, is_group=False)
        .filter(participants=offer.user)
        .first()
    )
    if existing:
        convo = existing
    else:
        convo = Conversation.objects.create(is_group=False)
        convo.participants.set([request.user, offer.user])

    deal, created = SkillDeal.objects.get_or_create(
        offer=offer,
        initiator=request.user,
        responder=offer.user,
        defaults={
            'message': data.get('message', '').strip(),
            'conversation': convo,
        }
    )
    if created:
        offer.status = SkillOffer.STATUS_MATCHED
        offer.save(update_fields=['status'])
        Message.objects.create(
            conversation=convo,
            sender=request.user,
            content=f"👋 Hey! I'd like to trade skills with you.\n\nYour offer: *{offer.title}*\n\n{deal.message or 'Let me know if you are interested!'}",
        )
    return JsonResponse({'ok': True, 'convo_id': str(convo.id), 'deal_id': str(deal.id)})


# ── Confession Feed ───────────────────────────────────────────────────────────

@login_required
def confession_feed(request):
    """Browse anonymous confessions."""
    cat = request.GET.get('cat', '')
    qs = Confession.objects.filter(status=Confession.STATUS_ACTIVE)
    if cat:
        qs = qs.filter(category=cat)
    confessions = qs.order_by('-created_at')[:30]
    upvoted_ids = set(
        ConfessionUpvote.objects.filter(user=request.user).values_list('confession_id', flat=True)
    )
    return render(request, 'community/confessions.html', {
        'confessions': confessions,
        'upvoted_ids': upvoted_ids,
        'categories': Confession.CAT_CHOICES,
        'active_cat': cat,
    })


@login_required
@require_POST
def confession_create(request):
    """Post an anonymous confession."""
    import json as _json
    try:
        data = _json.loads(request.body)
    except Exception:
        data = request.POST
    content = data.get('content', '').strip()
    if not content or len(content) < 10:
        return JsonResponse({'error': 'Too short'}, status=400)
    if len(content) > 1000:
        return JsonResponse({'error': 'Too long (max 1000 chars)'}, status=400)

    # Basic crisis keyword detection
    crisis_words = ['suicide', 'kill myself', 'end my life', 'self harm', 'want to die']
    is_crisis = any(w in content.lower() for w in crisis_words)

    confession = Confession.objects.create(
        author=request.user,
        content=content,
        category=data.get('category', 'general'),
        is_crisis=is_crisis,
    )
    return JsonResponse({'ok': True, 'id': str(confession.id), 'is_crisis': is_crisis})


@login_required
@require_POST
def confession_upvote(request, confession_id):
    """Toggle upvote on a confession."""
    confession = get_object_or_404(Confession, id=confession_id, status=Confession.STATUS_ACTIVE)
    upvote, created = ConfessionUpvote.objects.get_or_create(user=request.user, confession=confession)
    if created:
        Confession.objects.filter(pk=confession.pk).update(upvote_count=models.F('upvote_count') + 1)
        return JsonResponse({'ok': True, 'upvoted': True, 'count': confession.upvote_count + 1})
    else:
        upvote.delete()
        Confession.objects.filter(pk=confession.pk).update(upvote_count=models.F('upvote_count') - 1)
        return JsonResponse({'ok': True, 'upvoted': False, 'count': max(0, confession.upvote_count - 1)})


@login_required
@require_POST
def confession_reply(request, confession_id):
    """Reply to a confession."""
    import json as _json
    confession = get_object_or_404(Confession, id=confession_id, status=Confession.STATUS_ACTIVE)
    try:
        data = _json.loads(request.body)
    except Exception:
        data = request.POST
    content = data.get('content', '').strip()
    if not content:
        return JsonResponse({'error': 'Reply cannot be empty'}, status=400)
    is_anon = bool(data.get('is_anonymous', False))
    reply = ConfessionReply.objects.create(
        confession=confession,
        author=request.user,
        content=content,
        is_anonymous=is_anon,
    )
    Confession.objects.filter(pk=confession.pk).update(reply_count=models.F('reply_count') + 1)
    author_display = 'Anonymous' if is_anon else request.user.username
    return JsonResponse({'ok': True, 'id': str(reply.id), 'author': author_display})


# ── Startup Command Center ────────────────────────────────────────────────────

@login_required
def startup_list(request):
    """Browse all public startups."""
    stage = request.GET.get('stage', '')
    qs = Startup.objects.filter(is_active=True).select_related(
        'founder', 'founder__community_profile'
    ).prefetch_related('members')
    if stage:
        qs = qs.filter(stage=stage)
    startups = qs.order_by('-updated_at')[:30]
    followed_ids = set(
        StartupFollow.objects.filter(user=request.user).values_list('startup_id', flat=True)
    )
    return render(request, 'community/startups.html', {
        'startups': startups,
        'stages': Startup.STAGE_CHOICES,
        'active_stage': stage,
        'followed_ids': followed_ids,
    })


@login_required
def startup_detail(request, slug):
    """Startup public profile page."""
    startup = get_object_or_404(Startup, slug=slug, is_active=True)
    members = startup.members.select_related('user', 'user__community_profile').all()
    updates = startup.updates.select_related('author', 'author__community_profile').order_by('-created_at')[:10]
    is_member = startup.members.filter(user=request.user).exists()
    is_following = StartupFollow.objects.filter(user=request.user, startup=startup).exists()
    is_founder = startup.founder == request.user
    return render(request, 'community/startup_detail.html', {
        'startup': startup,
        'members': members,
        'updates': updates,
        'is_member': is_member,
        'is_following': is_following,
        'is_founder': is_founder,
    })
@login_required
def startup_create(request):
    """Create a new startup."""
    if request.method == 'GET':
        return render(request, 'community/startup_create.html', {'stages': Startup.STAGE_CHOICES})
    import json as _json
    try:
        data = _json.loads(request.body)
    except Exception:
        data = request.POST
    name = data.get('name', '').strip()
    if not name:
        return JsonResponse({'error': 'Name required'}, status=400)
    startup = Startup.objects.create(
        founder=request.user,
        name=name,
        tagline=data.get('tagline', '').strip(),
        description=data.get('description', '').strip(),
        stage=data.get('stage', 'idea'),
        skills_needed=data.get('skills_needed', '').strip(),
        is_recruiting=bool(data.get('is_recruiting', False)),
    )
    StartupMember.objects.create(startup=startup, user=request.user, role=StartupMember.ROLE_FOUNDER)
    if request.content_type and 'json' in request.content_type:
        return JsonResponse({'ok': True, 'slug': startup.slug})
    from django.shortcuts import redirect
    return redirect('community:startup_detail', slug=startup.slug)


@login_required
@require_POST
def startup_follow_toggle(request, slug):
    """Follow/unfollow a startup."""
    startup = get_object_or_404(Startup, slug=slug)
    follow, created = StartupFollow.objects.get_or_create(user=request.user, startup=startup)
    if created:
        Startup.objects.filter(pk=startup.pk).update(follower_count=models.F('follower_count') + 1)
        return JsonResponse({'ok': True, 'following': True})
    else:
        follow.delete()
        Startup.objects.filter(pk=startup.pk).update(follower_count=models.F('follower_count') - 1)
        return JsonResponse({'ok': True, 'following': False})


@login_required
@require_POST
def startup_post_update(request, slug):
    """Post a dev log update to a startup."""
    import json as _json
    startup = get_object_or_404(Startup, slug=slug)
    if not startup.members.filter(user=request.user).exists():
        return JsonResponse({'error': 'Not a team member'}, status=403)
    try:
        data = _json.loads(request.body)
    except Exception:
        data = request.POST
    content = data.get('content', '').strip()
    if not content:
        return JsonResponse({'error': 'Content required'}, status=400)
    update = StartupUpdate.objects.create(
        startup=startup,
        author=request.user,
        content=content,
        milestone=data.get('milestone', '').strip(),
    )
    startup.save(update_fields=['updated_at'])
    return JsonResponse({'ok': True, 'id': str(update.id)})


# ── Campus Pulse ─────────────────────────────────────────────────────────────

@login_required
def pulse_map(request):
    """Campus pulse map / list view."""
    now = timezone.now()
    event_type = request.GET.get('type', '')
    qs = PulseEvent.objects.filter(
        expires_at__gt=now, is_private=False
    ).select_related('host', 'host__community_profile')
    if event_type:
        qs = qs.filter(event_type=event_type)
    events = qs.order_by('expires_at')[:30]
    joined_ids = set(
        PulseJoin.objects.filter(user=request.user).values_list('event_id', flat=True)
    )
    return render(request, 'community/pulse_map.html', {
        'events': events,
        'joined_ids': joined_ids,
        'event_types': PulseEvent.TYPE_CHOICES,
        'active_type': event_type,
        'now': now,
    })


@login_required
def pulse_event_create(request):
    """Create a pulse event — supports multipart (photo/video) or JSON."""
    if request.method == 'GET':
        return render(request, 'community/pulse_event_create.html', {'event_types': PulseEvent.TYPE_CHOICES})

    from django.utils.dateparse import parse_datetime

    # Support both multipart form (with media) and JSON
    is_multipart = request.content_type and 'multipart' in request.content_type
    if is_multipart:
        data = request.POST
    else:
        import json as _json
        try:
            data = _json.loads(request.body)
        except Exception:
            data = request.POST

    title = data.get('title', '').strip()
    if not title:
        return JsonResponse({'error': 'Title required'}, status=400)

    starts_at = parse_datetime(data.get('starts_at', '')) or timezone.now()
    expires_at = parse_datetime(data.get('expires_at', '')) or (timezone.now() + timezone.timedelta(hours=2))

    event = PulseEvent.objects.create(
        host=request.user,
        title=title,
        description=data.get('description', '').strip(),
        event_type=data.get('event_type', 'study'),
        location_name=data.get('location', data.get('location_name', '')).strip(),
        is_online=bool(data.get('is_online', False)),
        starts_at=starts_at,
        expires_at=expires_at,
    )

    # Attach photo if provided
    if is_multipart and 'photo' in request.FILES:
        event.photo = request.FILES['photo']
        event.save(update_fields=['photo'])

    if request.content_type and ('json' in request.content_type or is_multipart):
        return JsonResponse({'ok': True, 'id': str(event.id),
                             'photo_url': event.photo.url if event.photo else None})
    from django.shortcuts import redirect
    return redirect('community:pulse_map')


@login_required
@require_POST
def pulse_join(request, event_id):
    """Join a pulse event."""
    event = get_object_or_404(PulseEvent, id=event_id)
    join, created = PulseJoin.objects.get_or_create(user=request.user, event=event)
    if created:
        PulseEvent.objects.filter(pk=event.pk).update(participant_count=models.F('participant_count') + 1)
    return JsonResponse({'ok': True, 'joined': True, 'count': event.participant_count + (1 if created else 0)})


@login_required
def pulse_events_api(request):
    """JSON feed of active pulse events for live updates."""
    now = timezone.now()
    events = PulseEvent.objects.filter(
        expires_at__gt=now, is_private=False
    ).select_related('host').values(
        'id', 'title', 'event_type', 'location_name', 'is_online',
        'participant_count', 'starts_at', 'expires_at', 'host__username',
    ).order_by('expires_at')[:30]
    return JsonResponse({'events': list(events), 'now': now.isoformat()})


# ── Micro Rooms ───────────────────────────────────────────────────────────────

@login_required
def micro_rooms_list(request):
    """List open micro rooms."""
    rooms = MicroRoom.objects.filter(
        status=MicroRoom.STATUS_OPEN
    ).select_related('host', 'host__community_profile').order_by('-created_at')[:20]
    return render(request, 'community/micro_rooms.html', {'rooms': rooms})


@login_required
def micro_room_create(request):
    """Create a micro room instantly — returns JSON with redirect URL."""
    import json as _json, secrets
    if request.method == 'GET':
        return render(request, 'community/micro_rooms.html', {
            'rooms': MicroRoom.objects.filter(status=MicroRoom.STATUS_OPEN)
                .select_related('host', 'host__community_profile').order_by('-created_at')[:20]
        })
    try:
        data = _json.loads(request.body)
    except Exception:
        data = request.POST
    topic = data.get('topic', '').strip() or 'Open Chat'
    room = MicroRoom.objects.create(
        host=request.user,
        topic=topic,
        peer_room_id=secrets.token_urlsafe(16),
    )
    MicroRoomParticipant.objects.create(room=room, user=request.user)

    # ── Notify followers + accepted friends ──────────────────────────────────
    try:
        from community.models import Follow, Friendship, Notification as Notif
        follower_ids = set(
            Follow.objects.filter(following=request.user)
            .values_list('follower_id', flat=True)
        )
        raw_friends = Friendship.objects.filter(
            status=Friendship.STATUS_ACCEPTED
        ).filter(
            models.Q(requester=request.user) | models.Q(recipient=request.user)
        ).values_list('requester_id', 'recipient_id')
        for req_id, rec_id in raw_friends:
            other = rec_id if req_id == request.user.pk else req_id
            follower_ids.add(other)
        follower_ids.discard(request.user.pk)
        if follower_ids:
            Notif.objects.bulk_create([
                Notif(
                    recipient_id=uid,
                    actor=request.user,
                    type=Notif.TYPE_LIVE,
                    extra_data=str(room.id),
                )
                for uid in follower_ids
            ], ignore_conflicts=True)
    except Exception as e:
        import logging
        logging.getLogger(__name__).warning('Live notification failed: %s', e)

    return JsonResponse({'ok': True, 'id': str(room.id), 'redirect': f'/community/rooms/{room.id}/'})


@login_required
def micro_room_detail(request, room_id):
    """The live room page — host streams, viewers watch."""
    room = get_object_or_404(MicroRoom, id=room_id)
    is_host = room.host == request.user
    # Auto-join as participant if not already
    if room.status == MicroRoom.STATUS_OPEN:
        participant, created = MicroRoomParticipant.objects.get_or_create(
            room=room, user=request.user, defaults={'left_at': None}
        )
        if created:
            MicroRoom.objects.filter(pk=room.pk).update(participant_count=models.F('participant_count') + 1)
    participants = MicroRoomParticipant.objects.filter(
        room=room, left_at__isnull=True
    ).select_related('user', 'user__community_profile').order_by('joined_at')
    return render(request, 'community/micro_room_live.html', {
        'room': room,
        'is_host': is_host,
        'participants': participants,
    })


@login_required
@require_POST
def micro_room_signal(request, room_id):
    """Store a WebRTC signal in DB so all workers can read it."""
    import json as _json
    room = get_object_or_404(MicroRoom, id=room_id)
    try:
        data = _json.loads(request.body)
    except Exception:
        return JsonResponse({'error': 'bad json'}, status=400)
    signal_type = data.get('type')
    payload = data.get('payload')
    target = data.get('target', 'all')
    if not signal_type or payload is None:
        return JsonResponse({'error': 'missing fields'}, status=400)

    RoomSignal.objects.create(
        room=room,
        sender=request.user,
        target=target,
        signal_type=signal_type,
        payload=_json.dumps(payload),
    )
    # Clean up old consumed signals older than 5 minutes
    from django.utils import timezone as tz
    import datetime
    RoomSignal.objects.filter(
        room=room, consumed=True,
        created_at__lt=tz.now() - datetime.timedelta(minutes=5)
    ).delete()
    return JsonResponse({'ok': True})


@login_required
def micro_room_poll(request, room_id):
    """Poll for WebRTC signals (DB-backed) + comments + participant list."""
    import json as _json
    username = request.user.username

    # Fetch unconsumed signals addressed to this user or 'all', not sent by self
    qs = RoomSignal.objects.filter(
        room_id=room_id, consumed=False
    ).exclude(sender__username=username).filter(
        models.Q(target=username) | models.Q(target='all')
    ).order_by('created_at').select_related('sender')[:30]

    signals = []
    ids_to_consume = []
    for sig in qs:
        try:
            payload = _json.loads(sig.payload)
        except Exception:
            payload = {}
        signals.append({'type': sig.signal_type, 'payload': payload, 'from': sig.sender.username})
        if sig.target == username:
            ids_to_consume.append(sig.pk)

    if ids_to_consume:
        RoomSignal.objects.filter(pk__in=ids_to_consume).update(consumed=True)

    # Participants
    participants = list(
        MicroRoomParticipant.objects.filter(room_id=room_id, left_at__isnull=True)
        .values_list('user__username', flat=True)
    )
    viewer_count = len(participants)
    room_data = MicroRoom.objects.filter(id=room_id).values('status', 'participant_count').first()
    if room_data:
        room_data['viewer_count'] = viewer_count

    # Comments (cache is fine for comments — single-worker read is ok)
    from django.core.cache import cache
    comments = cache.get(f'room_comments_{room_id}', [])

    return JsonResponse({
        'signals': signals,
        'host_offer': None,
        'participants': participants,
        'room': room_data,
        'comments': comments,
    })


@login_required
@require_POST
def micro_room_comment(request, room_id):
    """Post a live comment to a room — stored in cache, returned via poll."""
    import json as _json
    from django.core.cache import cache
    room = get_object_or_404(MicroRoom, id=room_id)
    try:
        data = _json.loads(request.body)
    except Exception:
        return JsonResponse({'error': 'bad json'}, status=400)
    text = (data.get('text') or '').strip()[:280]
    if not text:
        return JsonResponse({'error': 'empty'}, status=400)
    comment = {
        'id': str(timezone.now().timestamp()),
        'username': request.user.username,
        'text': text,
        'ts': timezone.now().strftime('%H:%M'),
    }
    key = f'room_comments_{room_id}'
    comments = cache.get(key, [])
    comments.append(comment)
    # Keep last 100 comments, expire in 2 hours
    cache.set(key, comments[-100:], 7200)
    return JsonResponse({'ok': True, 'comment': comment})


@login_required
@require_POST
def micro_room_join(request, room_id):
    """Join a micro room."""
    room = get_object_or_404(MicroRoom, id=room_id, status=MicroRoom.STATUS_OPEN)
    participant, created = MicroRoomParticipant.objects.get_or_create(
        room=room, user=request.user,
        defaults={'left_at': None}
    )
    if created:
        MicroRoom.objects.filter(pk=room.pk).update(participant_count=models.F('participant_count') + 1)
    return JsonResponse({'ok': True, 'peer_room_id': room.peer_room_id, 'topic': room.topic})


@login_required
@require_POST
def micro_room_leave(request, room_id):
    """Leave a micro room. Auto-close if empty."""
    room = get_object_or_404(MicroRoom, id=room_id)
    MicroRoomParticipant.objects.filter(room=room, user=request.user).update(left_at=timezone.now())
    active = MicroRoomParticipant.objects.filter(room=room, left_at__isnull=True).count()
    MicroRoom.objects.filter(pk=room.pk).update(participant_count=max(0, active))
    if active == 0:
        MicroRoom.objects.filter(pk=room.pk).update(status=MicroRoom.STATUS_CLOSED, closed_at=timezone.now())
    return JsonResponse({'ok': True})


# ── Help Beacon ───────────────────────────────────────────────────────────────

@login_required
def help_beacon_list(request):
    """Browse open help beacons."""
    cat = request.GET.get('cat', '')
    qs = HelpBeacon.objects.filter(status=HelpBeacon.STATUS_OPEN).select_related(
        'requester', 'requester__community_profile'
    )
    if cat:
        qs = qs.filter(category=cat)
    beacons = qs.order_by('-created_at')[:30]
    return render(request, 'community/help_beacons.html', {
        'beacons': beacons,
        'categories': HelpBeacon.CAT_CHOICES,
        'active_cat': cat,
    })


@login_required
@require_POST
def help_beacon_create(request):
    """Post a help beacon."""
    import json as _json
    try:
        data = _json.loads(request.body)
    except Exception:
        data = request.POST
    title = data.get('title', '').strip()
    if not title:
        return JsonResponse({'error': 'Title required'}, status=400)
    beacon = HelpBeacon.objects.create(
        requester=request.user,
        title=title,
        description=data.get('description', '').strip(),
        category=data.get('category', 'other'),
        urgency=data.get('urgency', 'medium'),
        prefer_voice=bool(data.get('prefer_voice', False)),
    )
    return JsonResponse({'ok': True, 'id': str(beacon.id)})


@login_required
@require_POST
def help_beacon_claim(request, beacon_id):
    """Claim a help beacon as a helper."""
    beacon = get_object_or_404(HelpBeacon, id=beacon_id, status=HelpBeacon.STATUS_OPEN)
    if beacon.requester == request.user:
        return JsonResponse({'error': 'Cannot claim your own beacon'}, status=400)
    # Create DM conversation
    existing = (
        Conversation.objects.filter(participants=request.user, is_group=False)
        .filter(participants=beacon.requester)
        .first()
    )
    if existing:
        convo = existing
    else:
        convo = Conversation.objects.create(is_group=False)
        convo.participants.set([request.user, beacon.requester])
    beacon.helper = request.user
    beacon.status = HelpBeacon.STATUS_CLAIMED
    beacon.conversation = convo
    beacon.save(update_fields=['helper', 'status', 'conversation'])
    Message.objects.create(
        conversation=convo,
        sender=request.user,
        content=f"👋 Hey! I saw your help request: *{beacon.title}*\n\nI can help you with this. Let's talk!",
    )
    return JsonResponse({'ok': True, 'convo_id': str(convo.id)})


@login_required
@require_POST
def help_beacon_resolve(request, beacon_id):
    """Mark a beacon as resolved and optionally rate the helper."""
    import json as _json
    beacon = get_object_or_404(HelpBeacon, id=beacon_id, requester=request.user)
    try:
        data = _json.loads(request.body)
    except Exception:
        data = {}
    beacon.status = HelpBeacon.STATUS_RESOLVED
    beacon.resolved_at = timezone.now()
    rating = data.get('rating')
    if rating and str(rating).isdigit():
        beacon.helper_rating = min(5, max(1, int(rating)))
    beacon.save(update_fields=['status', 'resolved_at', 'helper_rating'])
    return JsonResponse({'ok': True})
