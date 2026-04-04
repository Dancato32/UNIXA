"""
AI Community models — additive only, no changes to existing community models.
"""
import uuid
from django.conf import settings
from django.db import models


def _uuid():
    return uuid.uuid4()


class UserAIProfile(models.Model):
    """Extended AI profile storing skills, interests, goals for matching."""
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='ai_profile'
    )
    skills = models.TextField(blank=True, help_text="Comma-separated skills")
    interests = models.TextField(blank=True, help_text="Comma-separated interests")
    courses = models.TextField(blank=True, help_text="Comma-separated courses")
    goals = models.TextField(blank=True)
    availability = models.CharField(max_length=50, blank=True)  # e.g. "weekends", "evenings"
    looking_for = models.CharField(max_length=100, blank=True)  # study-partner, collaborator, etc.
    startup_interest = models.BooleanField(default=False)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'AIProfile({self.user})'


class AIMatch(models.Model):
    """Cached people-matching results."""
    MATCH_STUDY = 'study'
    MATCH_PROJECT = 'project'
    MATCH_STARTUP = 'startup'
    MATCH_GENERAL = 'general'
    MATCH_TYPES = [
        (MATCH_STUDY, 'Study Partner'),
        (MATCH_PROJECT, 'Project Collaborator'),
        (MATCH_STARTUP, 'Startup Teammate'),
        (MATCH_GENERAL, 'General Connection'),
    ]
    id = models.UUIDField(primary_key=True, default=_uuid, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='ai_matches'
    )
    matched_user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='matched_by'
    )
    match_type = models.CharField(max_length=20, choices=MATCH_TYPES, default=MATCH_GENERAL)
    score = models.FloatField(default=0.0)
    reason = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-score']
        unique_together = ('user', 'matched_user', 'match_type')

    def __str__(self):
        return f'{self.user} → {self.matched_user} ({self.match_type}, {self.score:.2f})'


class StartupTeam(models.Model):
    """A startup team created via the AI matcher."""
    STATUS_FORMING = 'forming'
    STATUS_ACTIVE = 'active'
    STATUS_CLOSED = 'closed'
    STATUS_CHOICES = [
        (STATUS_FORMING, 'Forming'),
        (STATUS_ACTIVE, 'Active'),
        (STATUS_CLOSED, 'Closed'),
    ]
    id = models.UUIDField(primary_key=True, default=_uuid, editable=False)
    name = models.CharField(max_length=255)
    idea = models.TextField()
    industry = models.CharField(max_length=100, blank=True)
    stage = models.CharField(max_length=50, blank=True)
    founder = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='founded_startups'
    )
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=STATUS_FORMING)
    required_roles = models.TextField(blank=True, help_text="Comma-separated roles needed")
    team_size = models.PositiveSmallIntegerField(default=4)
    remote = models.BooleanField(default=True)
    ai_intro = models.TextField(blank=True, help_text="AI-generated team introduction")
    # Link to existing GroupWorkspace once created
    workspace_id = models.UUIDField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.name


class StartupTeamMember(models.Model):
    """Member of a startup team."""
    STATUS_INVITED = 'invited'
    STATUS_ACCEPTED = 'accepted'
    STATUS_DECLINED = 'declined'
    STATUS_CHOICES = [
        (STATUS_INVITED, 'Invited'),
        (STATUS_ACCEPTED, 'Accepted'),
        (STATUS_DECLINED, 'Declined'),
    ]
    id = models.UUIDField(primary_key=True, default=_uuid, editable=False)
    team = models.ForeignKey(StartupTeam, on_delete=models.CASCADE, related_name='members')
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='startup_memberships'
    )
    role = models.CharField(max_length=100, blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=STATUS_INVITED)
    ai_reason = models.TextField(blank=True)
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('team', 'user')

    def __str__(self):
        return f'{self.user} in {self.team} ({self.role})'


class AIOpportunity(models.Model):
    """Detected opportunity from community posts."""
    TYPE_GRANT = 'grant'
    TYPE_FREELANCE = 'freelance'
    TYPE_OTHER = 'other'
    TYPE_CHOICES = [
        (TYPE_GRANT, 'Grant'),
        (TYPE_FREELANCE, 'Freelance Gig'),
        (TYPE_OTHER, 'Other'),
    ]
    id = models.UUIDField(primary_key=True, default=_uuid, editable=False)
    title = models.CharField(max_length=300)
    description = models.TextField()
    opp_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default=TYPE_OTHER)
    source_post_id = models.UUIDField(null=True, blank=True)
    deadline = models.DateField(null=True, blank=True)
    url = models.URLField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title


class ExpertBadge(models.Model):
    """AI-assigned expertise badge for a user."""
    id = models.UUIDField(primary_key=True, default=_uuid, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='expert_badges'
    )
    label = models.CharField(max_length=100)  # e.g. "Top Math Helper"
    subject = models.CharField(max_length=100, blank=True)
    score = models.FloatField(default=0.0)
    awarded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-score']

    def __str__(self):
        return f'{self.label} → {self.user}'
