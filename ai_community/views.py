"""
AI Community views — all new, no existing views modified.
"""
import json
import logging
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.views.decorators.http import require_POST
from django.utils import timezone

from community.models import (
    Post, CommunityProfile, CommunityMembership, CustomCommunityMembership,
    GroupWorkspace, WorkspaceMember, WorkspaceMessage, Conversation,
)
from ai_community.models import (
    UserAIProfile, AIMatch, StartupTeam, StartupTeamMember,
    AIOpportunity, ExpertBadge,
)
from ai_community import ai_engine

User = get_user_model()
logger = logging.getLogger(__name__)


def _get_or_create_ai_profile(user):
    profile, _ = UserAIProfile.objects.get_or_create(user=user)
    return profile


def _user_to_dict(user):
    """Serialize a user for AI engine consumption."""
    try:
        cp = user.community_profile
        bio = cp.bio
        location = cp.location
    except Exception:
        bio = ''
        location = ''
    try:
        ai_p = user.ai_profile
        skills = ai_p.skills
        interests = ai_p.interests
        courses = ai_p.courses
        goals = ai_p.goals
    except Exception:
        skills = interests = courses = goals = ''
    return {
        'username': user.username,
        'bio': bio,
        'location': location,
        'skills': skills,
        'interests': interests,
        'courses': courses,
        'goals': goals,
    }


# ── Hub page ──────────────────────────────────────────────────────────────────

@login_required
def ai_hub(request):
    """Main AI Community hub — all features in one page."""
    ai_profile = _get_or_create_ai_profile(request.user)
    my_startups = StartupTeam.objects.filter(founder=request.user).order_by('-created_at')[:5]
    my_invites = StartupTeamMember.objects.filter(
        user=request.user, status=StartupTeamMember.STATUS_INVITED
    ).select_related('team', 'team__founder')[:5]
    opportunities = AIOpportunity.objects.filter(is_active=True).order_by('-created_at')[:10]
    badges = ExpertBadge.objects.filter(user=request.user)
    matches = AIMatch.objects.filter(user=request.user).select_related(
        'matched_user', 'matched_user__community_profile'
    )[:12]

    return render(request, 'ai_community/hub.html', {
        'ai_profile': ai_profile,
        'my_startups': my_startups,
        'my_invites': my_invites,
        'opportunities': opportunities,
        'badges': badges,
        'matches': matches,
    })


# ── Profile setup ─────────────────────────────────────────────────────────────

@login_required
@require_POST
def save_ai_profile(request):
    data = json.loads(request.body)
    profile = _get_or_create_ai_profile(request.user)
    profile.skills = data.get('skills', '')
    profile.interests = data.get('interests', '')
    profile.courses = data.get('courses', '')
    profile.goals = data.get('goals', '')
    profile.availability = data.get('availability', '')
    profile.looking_for = data.get('looking_for', '')
    profile.startup_interest = data.get('startup_interest', False)
    profile.save()
    return JsonResponse({'ok': True})


# ── People matching ───────────────────────────────────────────────────────────

@login_required
def find_people(request):
    """Run AI people matching and return results."""
    current = _user_to_dict(request.user)
    # Get candidates: other users with AI profiles, exclude self and blocked
    from django.db.models import Q
    blocked_ids = set(
        request.user.blocking.values_list('blocked_id', flat=True)
    )
    candidates_qs = User.objects.exclude(
        id__in=blocked_ids | {request.user.id}
    ).select_related('community_profile').prefetch_related('ai_profile')[:60]

    candidates = [_user_to_dict(u) for u in candidates_qs]
    if not candidates:
        return JsonResponse({'matches': []})

    results = ai_engine.match_people(current, candidates)

    # Cache results
    AIMatch.objects.filter(user=request.user).delete()
    for r in results:
        try:
            matched_user = User.objects.get(username=r['username'])
            AIMatch.objects.update_or_create(
                user=request.user,
                matched_user=matched_user,
                match_type=r.get('match_type', 'general'),
                defaults={'score': r.get('score', 0), 'reason': r.get('reason', '')},
            )
        except User.DoesNotExist:
            pass

    return JsonResponse({'matches': results})


# ── Campus assistant ──────────────────────────────────────────────────────────

@login_required
@require_POST
def campus_assistant(request):
    data = json.loads(request.body)
    question = data.get('question', '').strip()[:500]
    if not question:
        return JsonResponse({'error': 'No question provided'}, status=400)

    # Build context from platform data
    recent_posts = Post.objects.filter(is_deleted=False).order_by('-created_at')[:20]
    users_sample = User.objects.exclude(id=request.user.id).select_related(
        'community_profile'
    )[:20]
    from community.models import SchoolCommunity, CustomCommunity
    communities = list(SchoolCommunity.objects.filter(is_active=True).values('name', 'description')[:10])
    communities += list(CustomCommunity.objects.filter(is_active=True).values('name', 'description')[:10])

    context = {
        'recent_posts': [
            {'content': p.content[:150], 'author': p.author.username, 'community': str(p.school_community or p.custom_community or 'feed')}
            for p in recent_posts
        ],
        'users': [_user_to_dict(u) for u in users_sample],
        'communities': communities,
    }

    result = ai_engine.campus_assistant_query(question, context)
    return JsonResponse(result)


# ── Study group generator ─────────────────────────────────────────────────────

@login_required
@require_POST
def create_study_group(request):
    data = json.loads(request.body)
    subject = data.get('subject', '').strip()[:100]
    if not subject:
        return JsonResponse({'error': 'Subject required'}, status=400)

    # Find users interested in same subject
    from django.db.models import Q
    candidates = User.objects.filter(
        Q(ai_profile__courses__icontains=subject) |
        Q(ai_profile__interests__icontains=subject)
    ).exclude(id=request.user.id)[:8]

    members_data = [_user_to_dict(u) for u in candidates]
    members_data.insert(0, _user_to_dict(request.user))

    group_info = ai_engine.generate_study_group(subject, members_data)

    # Create a GroupWorkspace
    ws = GroupWorkspace.objects.create(
        name=group_info['group_name'],
        description=f'AI-matched study group for {subject}',
        subject=subject,
        owner=request.user,
        privacy=GroupWorkspace.PRIVACY_REQUEST,
    )
    WorkspaceMember.objects.create(workspace=ws, user=request.user, role=WorkspaceMember.ROLE_OWNER)
    for u in candidates[:5]:
        WorkspaceMember.objects.get_or_create(workspace=ws, user=u, defaults={'role': WorkspaceMember.ROLE_MEMBER})

    # Post intro message
    WorkspaceMessage.objects.create(
        workspace=ws,
        sender=request.user,
        content=f'🤖 {group_info["intro_message"]}',
    )

    return JsonResponse({
        'ok': True,
        'workspace_id': str(ws.id),
        'group_name': group_info['group_name'],
        'member_count': WorkspaceMember.objects.filter(workspace=ws).count(),
    })


# ── Startup team ──────────────────────────────────────────────────────────────

@login_required
def startup_page(request):
    ai_profile = _get_or_create_ai_profile(request.user)
    my_teams = StartupTeam.objects.filter(founder=request.user).order_by('-created_at')
    invites = StartupTeamMember.objects.filter(
        user=request.user, status=StartupTeamMember.STATUS_INVITED
    ).select_related('team', 'team__founder')
    return render(request, 'ai_community/startup.html', {
        'ai_profile': ai_profile,
        'my_teams': my_teams,
        'invites': invites,
    })


@login_required
@require_POST
def create_startup(request):
    data = json.loads(request.body)
    idea = data.get('idea', '').strip()
    if not idea:
        return JsonResponse({'error': 'Idea required'}, status=400)

    # Rate limit: max 3 active startups per user
    active_count = StartupTeam.objects.filter(
        founder=request.user, status__in=[StartupTeam.STATUS_FORMING, StartupTeam.STATUS_ACTIVE]
    ).count()
    if active_count >= 3:
        return JsonResponse({'error': 'You can have at most 3 active startup teams.'}, status=400)

    founder_data = _user_to_dict(request.user)
    idea_data = {
        'idea': idea,
        'industry': data.get('industry', ''),
        'stage': data.get('stage', 'idea'),
        'required_roles': data.get('required_roles', ''),
        'team_size': int(data.get('team_size', 4)),
        'remote': data.get('remote', True),
    }

    # Find candidates
    candidates_qs = User.objects.exclude(id=request.user.id).select_related(
        'community_profile'
    ).prefetch_related('ai_profile')[:50]
    candidates = [_user_to_dict(u) for u in candidates_qs]

    result = ai_engine.assemble_startup_team(founder_data, idea_data, candidates)
    if not result:
        return JsonResponse({'error': 'AI matching failed. Please try again.'}, status=500)

    # Create team
    team = StartupTeam.objects.create(
        name=result.get('team_name', f"{request.user.username}'s Startup"),
        idea=idea,
        industry=idea_data['industry'],
        stage=idea_data['stage'],
        founder=request.user,
        required_roles=idea_data['required_roles'],
        team_size=idea_data['team_size'],
        remote=idea_data['remote'],
        ai_intro=result.get('intro', ''),
    )

    # Add founder as accepted member
    StartupTeamMember.objects.create(
        team=team, user=request.user, role='Founder', status=StartupTeamMember.STATUS_ACCEPTED
    )

    # Invite matched members
    invited = []
    for m in result.get('members', []):
        if m['username'] == request.user.username:
            continue
        try:
            u = User.objects.get(username=m['username'])
            StartupTeamMember.objects.create(
                team=team, user=u,
                role=m.get('role', 'Member'),
                status=StartupTeamMember.STATUS_INVITED,
                ai_reason=m.get('reason', ''),
            )
            invited.append(m['username'])
        except User.DoesNotExist:
            pass

    # Create workspace
    ws = GroupWorkspace.objects.create(
        name=team.name,
        description=f'Startup workspace: {idea[:100]}',
        owner=request.user,
        privacy=GroupWorkspace.PRIVACY_PRIVATE,
    )
    WorkspaceMember.objects.create(workspace=ws, user=request.user, role=WorkspaceMember.ROLE_OWNER)
    team.workspace_id = ws.id
    team.save(update_fields=['workspace_id'])

    WorkspaceMessage.objects.create(
        workspace=ws, sender=request.user,
        content=f'🚀 {result.get("intro", "Your startup team has been assembled by AI!")}',
    )

    return JsonResponse({
        'ok': True,
        'team_id': str(team.id),
        'team_name': team.name,
        'workspace_id': str(ws.id),
        'invited': invited,
        'intro': result.get('intro', ''),
    })


@login_required
@require_POST
def respond_startup_invite(request, team_id):
    data = json.loads(request.body)
    accept = data.get('accept', False)
    member = get_object_or_404(
        StartupTeamMember, team_id=team_id, user=request.user,
        status=StartupTeamMember.STATUS_INVITED
    )
    if accept:
        member.status = StartupTeamMember.STATUS_ACCEPTED
        member.save()
        # Add to workspace
        if member.team.workspace_id:
            try:
                ws = GroupWorkspace.objects.get(id=member.team.workspace_id)
                WorkspaceMember.objects.get_or_create(
                    workspace=ws, user=request.user,
                    defaults={'role': WorkspaceMember.ROLE_MEMBER}
                )
            except GroupWorkspace.DoesNotExist:
                pass
        return JsonResponse({'ok': True, 'status': 'accepted'})
    else:
        member.status = StartupTeamMember.STATUS_DECLINED
        member.save()
        return JsonResponse({'ok': True, 'status': 'declined'})


# ── Opportunities ─────────────────────────────────────────────────────────────

@login_required
def opportunities(request):
    opps = AIOpportunity.objects.filter(is_active=True).order_by('-created_at')[:30]
    return JsonResponse({
        'opportunities': [
            {
                'id': str(o.id),
                'title': o.title,
                'type': o.opp_type,
                'description': o.description[:200],
                'created_at': o.created_at.isoformat(),
            }
            for o in opps
        ]
    })


@login_required
def scan_opportunities(request):
    """Scan recent posts for opportunities (called periodically or on demand)."""
    recent_posts = Post.objects.filter(
        is_deleted=False,
        created_at__gte=timezone.now() - timezone.timedelta(days=7)
    ).order_by('-created_at')[:50]

    found = 0
    for post in recent_posts:
        if AIOpportunity.objects.filter(source_post_id=post.id).exists():
            continue
        result = ai_engine.detect_opportunities(post.content)
        if result and result.get('is_opportunity'):
            AIOpportunity.objects.create(
                title=result.get('title', 'Opportunity'),
                description=result.get('description', post.content[:300]),
                opp_type=result.get('type', 'other'),
                source_post_id=post.id,
            )
            found += 1

    return JsonResponse({'ok': True, 'found': found})


# ── Icebreaker ────────────────────────────────────────────────────────────────

@login_required
def get_icebreaker(request, username):
    other_user = get_object_or_404(User, username=username)
    starters = ai_engine.generate_icebreaker(
        _user_to_dict(request.user),
        _user_to_dict(other_user),
    )
    return JsonResponse({'starters': starters})
