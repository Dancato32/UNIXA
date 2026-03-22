"""
Campus app models — 6 interconnected features:
  1. Skill Trading Marketplace
  2. Anonymous Confession + Wisdom Feed
  3. Startup Command Center
  4. Campus Pulse Map (live activity)
  5. Voice-Only Micro Rooms
  6. Need Help NOW Beacon
"""
import uuid
from django.conf import settings
from django.db import models
from django.utils import timezone


def _uuid():
    return uuid.uuid4()


# ─────────────────────────────────────────────────────────────────────────────
# 1. SKILL TRADING MARKETPLACE
# ─────────────────────────────────────────────────────────────────────────────

SKILL_TAGS = [
    ('coding', 'Coding'), ('design', 'Design'), ('writing', 'Writing'),
    ('tutoring', 'Tutoring'), ('math', 'Mathematics'), ('science', 'Science'),
    ('music', 'Music'), ('video', 'Video Editing'), ('photography', 'Photography'),
    ('language', 'Language'), ('business', 'Business'), ('research', 'Research'),
    ('data', 'Data Analysis'), ('marketing', 'Marketing'), ('law', 'Law'),
    ('medicine', 'Medicine'), ('engineering', 'Engineering'), ('other', 'Other'),
]


class SkillListing(models.Model):
    """A skill offer or request posted by a user."""
    TYPE_OFFER = 'offer'
    TYPE_REQUEST = 'request'
    TYPE_CHOICES = [(TYPE_OFFER, 'I can offer'), (TYPE_REQUEST, 'I need help with')]

    URGENCY_LOW = 'low'
    URGENCY_MEDIUM = 'medium'
    URGENCY_HIGH = 'high'
    URGENCY_CHOICES = [
        (URGENCY_LOW, 'Flexible'), (URGENCY_MEDIUM, 'This week'), (URGENCY_HIGH, 'Urgent'),
    ]

    STATUS_OPEN = 'open'
    STATUS_MATCHED = 'matched'
    STATUS_DONE = 'done'
    STATUS_CHOICES = [
        (STATUS_OPEN, 'Open'), (STATUS_MATCHED, 'In Progress'), (STATUS_DONE, 'Completed'),
    ]

    id = models.UUIDField(primary_key=True, default=_uuid, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='skill_listings')
    listing_type = models.CharField(max_length=10, choices=TYPE_CHOICES, default=TYPE_OFFER)
    title = models.CharField(max_length=200)
    description = models.TextField(max_length=1000, blank=True)
    skill_tag = models.CharField(max_length=20, choices=SKILL_TAGS, default='other')
    # What they want in return (for offers) or what they offer in return (for requests)
    exchange_for = models.CharField(max_length=200, blank=True, help_text='What you want in exchange')
    urgency = models.CharField(max_length=10, choices=URGENCY_CHOICES, default=URGENCY_LOW)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=STATUS_OPEN)
    school_community = models.ForeignKey(
        'community.SchoolCommunity', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='skill_listings',
    )
    view_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    expires_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['skill_tag', 'status', 'created_at']),
            models.Index(fields=['listing_type', 'status']),
        ]

    def __str__(self):
        return f'{self.get_listing_type_display()}: {self.title} by {self.user}'

    @property
    def is_expired(self):
        return self.expires_at and timezone.now() > self.expires_at


class SkillDeal(models.Model):
    """A barter deal between two users."""
    STATUS_PENDING = 'pending'
    STATUS_ACTIVE = 'active'
    STATUS_DONE = 'done'
    STATUS_CANCELLED = 'cancelled'
    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending'), (STATUS_ACTIVE, 'Active'),
        (STATUS_DONE, 'Completed'), (STATUS_CANCELLED, 'Cancelled'),
    ]

    id = models.UUIDField(primary_key=True, default=_uuid, editable=False)
    initiator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='deals_initiated')
    receiver = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='deals_received')
    listing = models.ForeignKey(SkillListing, on_delete=models.CASCADE, related_name='deals')
    message = models.TextField(blank=True, max_length=500)
    status = models.CharField(max_length=12, choices=STATUS_CHOICES, default=STATUS_PENDING)
    # Ratings after completion
    initiator_rating = models.PositiveSmallIntegerField(null=True, blank=True)  # 1-5
    receiver_rating = models.PositiveSmallIntegerField(null=True, blank=True)
    initiator_review = models.TextField(blank=True, max_length=300)
    receiver_review = models.TextField(blank=True, max_length=300)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'Deal: {self.initiator} ↔ {self.receiver} ({self.status})'


# ─────────────────────────────────────────────────────────────────────────────
# 2. ANONYMOUS CONFESSION + WISDOM FEED
# ─────────────────────────────────────────────────────────────────────────────

class Confession(models.Model):
    """Fully anonymous post. author stored but never exposed in API."""
    CAT_ACADEMIC = 'academic'
    CAT_MENTAL = 'mental_health'
    CAT_RELATIONSHIPS = 'relationships'
    CAT_FINANCE = 'finance'
    CAT_CAREER = 'career'
    CAT_SOCIAL = 'social'
    CAT_FUNNY = 'funny'
    CAT_ADVICE = 'advice'
    CAT_OTHER = 'other'
    CATEGORY_CHOICES = [
        (CAT_ACADEMIC, 'Academic'), (CAT_MENTAL, 'Mental Health'),
        (CAT_RELATIONSHIPS, 'Relationships'), (CAT_FINANCE, 'Finance'),
        (CAT_CAREER, 'Career'), (CAT_SOCIAL, 'Social'),
        (CAT_FUNNY, 'Funny'), (CAT_ADVICE, 'Advice Needed'), (CAT_OTHER, 'Other'),
    ]

    STATUS_VISIBLE = 'visible'
    STATUS_FLAGGED = 'flagged'
    STATUS_REMOVED = 'removed'
    STATUS_CHOICES = [
        (STATUS_VISIBLE, 'Visible'), (STATUS_FLAGGED, 'Flagged'), (STATUS_REMOVED, 'Removed'),
    ]

    id = models.UUIDField(primary_key=True, default=_uuid, editable=False)
    # author stored for moderation only — never returned in public API
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
        related_name='confessions',
    )
    content = models.TextField(max_length=2000)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default=CAT_OTHER)
    school_community = models.ForeignKey(
        'community.SchoolCommunity', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='confessions',
    )
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=STATUS_VISIBLE)
    is_crisis = models.BooleanField(default=False, db_index=True)  # AI-flagged crisis content
    upvote_count = models.PositiveIntegerField(default=0)
    reply_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['category', 'status', 'created_at']),
            models.Index(fields=['status', 'upvote_count']),
        ]

    def __str__(self):
        return f'Confession #{str(self.id)[:8]} [{self.category}]'


class ConfessionUpvote(models.Model):
    """One upvote per user per confession."""
    id = models.UUIDField(primary_key=True, default=_uuid, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='confession_upvotes')
    confession = models.ForeignKey(Confession, on_delete=models.CASCADE, related_name='upvotes')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'confession')


class ConfessionReply(models.Model):
    """Reply to a confession. Can be anonymous or identified."""
    id = models.UUIDField(primary_key=True, default=_uuid, editable=False)
    confession = models.ForeignKey(Confession, on_delete=models.CASCADE, related_name='replies')
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='confession_replies')
    content = models.TextField(max_length=1000)
    is_anonymous = models.BooleanField(default=False)
    is_helpful = models.BooleanField(default=False)  # marked by confession author
    is_solved = models.BooleanField(default=False)   # marks the confession as resolved
    helpful_count = models.PositiveIntegerField(default=0)
    is_flagged = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f'Reply to {self.confession_id} by {self.author}'


# ─────────────────────────────────────────────────────────────────────────────
# 3. STARTUP COMMAND CENTER
# ─────────────────────────────────────────────────────────────────────────────

class Startup(models.Model):
    """Public startup profile — the live show people can follow."""
    STAGE_IDEA = 'idea'
    STAGE_FORMING = 'forming'
    STAGE_BUILDING = 'building'
    STAGE_DEMO = 'demo'
    STAGE_LAUNCHED = 'launched'
    STAGE_CHOICES = [
        (STAGE_IDEA, '💡 Idea'), (STAGE_FORMING, '🧩 Forming Team'),
        (STAGE_BUILDING, '🔨 Building'), (STAGE_DEMO, '🎤 Demo Ready'),
        (STAGE_LAUNCHED, '🚀 Launched'),
    ]

    id = models.UUIDField(primary_key=True, default=_uuid, editable=False)
    founder = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='startups_founded')
    name = models.CharField(max_length=200)
    tagline = models.CharField(max_length=300, blank=True)
    description = models.TextField(blank=True)
    industry = models.CharField(max_length=100, blank=True)
    stage = models.CharField(max_length=12, choices=STAGE_CHOICES, default=STAGE_IDEA)
    logo = models.ImageField(upload_to='campus/startups/logos/', null=True, blank=True)
    website = models.URLField(blank=True)
    looking_for = models.CharField(max_length=500, blank=True, help_text='Comma-separated skills needed')
    school_community = models.ForeignKey(
        'community.SchoolCommunity', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='startups',
    )
    follower_count = models.PositiveIntegerField(default=0)
    is_recruiting = models.BooleanField(default=True, db_index=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.name


class StartupMember(models.Model):
    """Team member of a startup."""
    ROLE_FOUNDER = 'founder'
    ROLE_COFOUNDER = 'cofounder'
    ROLE_DEV = 'developer'
    ROLE_DESIGN = 'designer'
    ROLE_MARKETING = 'marketing'
    ROLE_ADVISOR = 'advisor'
    ROLE_OTHER = 'other'
    ROLE_CHOICES = [
        (ROLE_FOUNDER, 'Founder'), (ROLE_COFOUNDER, 'Co-Founder'),
        (ROLE_DEV, 'Developer'), (ROLE_DESIGN, 'Designer'),
        (ROLE_MARKETING, 'Marketing'), (ROLE_ADVISOR, 'Advisor'), (ROLE_OTHER, 'Other'),
    ]
    STATUS_PENDING = 'pending'
    STATUS_ACTIVE = 'active'
    STATUS_CHOICES = [(STATUS_PENDING, 'Pending'), (STATUS_ACTIVE, 'Active')]

    id = models.UUIDField(primary_key=True, default=_uuid, editable=False)
    startup = models.ForeignKey(Startup, on_delete=models.CASCADE, related_name='members')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='startup_memberships')
    role = models.CharField(max_length=12, choices=ROLE_CHOICES, default=ROLE_OTHER)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=STATUS_PENDING)
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('startup', 'user')

    def __str__(self):
        return f'{self.user} @ {self.startup} ({self.role})'


class StartupUpdate(models.Model):
    """Dev log / progress update posted by the startup team."""
    id = models.UUIDField(primary_key=True, default=_uuid, editable=False)
    startup = models.ForeignKey(Startup, on_delete=models.CASCADE, related_name='updates')
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='startup_updates')
    content = models.TextField(max_length=2000)
    milestone = models.CharField(max_length=200, blank=True)
    media = models.FileField(upload_to='campus/startups/updates/', null=True, blank=True)
    like_count = models.PositiveIntegerField(default=0)
    comment_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'Update for {self.startup} @ {self.created_at:%Y-%m-%d}'


class StartupFollow(models.Model):
    """User following a startup."""
    id = models.UUIDField(primary_key=True, default=_uuid, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='startups_followed')
    startup = models.ForeignKey(Startup, on_delete=models.CASCADE, related_name='followers')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'startup')


class StartupSupportInterest(models.Model):
    """Mentor / investor / collaborator interest in a startup."""
    TYPE_MENTOR = 'mentor'
    TYPE_INVESTOR = 'investor'
    TYPE_COLLABORATOR = 'collaborator'
    TYPE_CHOICES = [
        (TYPE_MENTOR, 'Mentor'), (TYPE_INVESTOR, 'Investor'), (TYPE_COLLABORATOR, 'Collaborator'),
    ]
    id = models.UUIDField(primary_key=True, default=_uuid, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='startup_interests')
    startup = models.ForeignKey(Startup, on_delete=models.CASCADE, related_name='support_interests')
    interest_type = models.CharField(max_length=14, choices=TYPE_CHOICES)
    message = models.TextField(blank=True, max_length=500)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'startup', 'interest_type')


# ─────────────────────────────────────────────────────────────────────────────
# 4. CAMPUS PULSE MAP
# ─────────────────────────────────────────────────────────────────────────────

class PulseActivity(models.Model):
    """A live activity visible on the Campus Pulse map/feed."""
    TYPE_STUDY = 'study'
    TYPE_EVENT = 'event'
    TYPE_SOCIAL = 'social'
    TYPE_RECRUITMENT = 'recruitment'
    TYPE_ACADEMIC = 'academic'
    TYPE_ONLINE = 'online'
    TYPE_VOICE_ROOM = 'voice_room'
    TYPE_HELP = 'help'
    TYPE_STARTUP = 'startup'
    TYPE_CHOICES = [
        (TYPE_STUDY, '📚 Study Group'), (TYPE_EVENT, '🎉 Event'),
        (TYPE_SOCIAL, '👋 Social'), (TYPE_RECRUITMENT, '🔍 Recruitment'),
        (TYPE_ACADEMIC, '🎓 Academic'), (TYPE_ONLINE, '💻 Online Only'),
        (TYPE_VOICE_ROOM, '🎤 Voice Room'), (TYPE_HELP, '🆘 Help Needed'),
        (TYPE_STARTUP, '🚀 Startup'),
    ]

    id = models.UUIDField(primary_key=True, default=_uuid, editable=False)
    host = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='pulse_activities')
    activity_type = models.CharField(max_length=12, choices=TYPE_CHOICES, db_index=True)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, max_length=500)
    location_name = models.CharField(max_length=200, blank=True)
    # Optional lat/lng for map pin (null = online only)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    school_community = models.ForeignKey(
        'community.SchoolCommunity', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='pulse_activities',
    )
    max_participants = models.PositiveSmallIntegerField(default=0)  # 0 = unlimited
    participant_count = models.PositiveIntegerField(default=1)
    is_private = models.BooleanField(default=False)
    # Reference to related object (optional cross-feature links)
    voice_room = models.ForeignKey('VoiceRoom', on_delete=models.SET_NULL, null=True, blank=True, related_name='pulse_entries')
    help_beacon = models.ForeignKey('HelpBeacon', on_delete=models.SET_NULL, null=True, blank=True, related_name='pulse_entries')
    startup = models.ForeignKey(Startup, on_delete=models.SET_NULL, null=True, blank=True, related_name='pulse_entries')
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    expires_at = models.DateTimeField(db_index=True)  # auto-expire

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['activity_type', 'expires_at']),
            models.Index(fields=['school_community', 'expires_at']),
        ]

    def __str__(self):
        return f'[{self.activity_type}] {self.title}'

    @property
    def is_live(self):
        return timezone.now() < self.expires_at


class PulseJoin(models.Model):
    """User joining a pulse activity."""
    id = models.UUIDField(primary_key=True, default=_uuid, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='pulse_joins')
    activity = models.ForeignKey(PulseActivity, on_delete=models.CASCADE, related_name='joins')
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'activity')


# ─────────────────────────────────────────────────────────────────────────────
# 5. VOICE-ONLY MICRO ROOMS
# ─────────────────────────────────────────────────────────────────────────────

class VoiceRoom(models.Model):
    """Lightweight audio space for spontaneous conversation."""
    STATUS_OPEN = 'open'
    STATUS_LOCKED = 'locked'
    STATUS_CLOSED = 'closed'
    STATUS_CHOICES = [
        (STATUS_OPEN, 'Open'), (STATUS_LOCKED, 'Locked'), (STATUS_CLOSED, 'Closed'),
    ]

    id = models.UUIDField(primary_key=True, default=_uuid, editable=False)
    host = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='voice_rooms_hosted')
    topic = models.CharField(max_length=200)
    status = models.CharField(max_length=8, choices=STATUS_CHOICES, default=STATUS_OPEN)
    school_community = models.ForeignKey(
        'community.SchoolCommunity', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='voice_rooms',
    )
    participant_count = models.PositiveSmallIntegerField(default=1)
    max_participants = models.PositiveSmallIntegerField(default=20)
    is_low_bandwidth = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    ended_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'VoiceRoom: {self.topic} ({self.status})'

    @property
    def is_active(self):
        return self.status != self.STATUS_CLOSED and self.ended_at is None


class VoiceRoomParticipant(models.Model):
    """Tracks who is currently in a voice room."""
    id = models.UUIDField(primary_key=True, default=_uuid, editable=False)
    room = models.ForeignKey(VoiceRoom, on_delete=models.CASCADE, related_name='participants')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='voice_room_sessions')
    is_muted = models.BooleanField(default=False)
    joined_at = models.DateTimeField(auto_now_add=True)
    left_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ('room', 'user')

    def __str__(self):
        return f'{self.user} in {self.room}'


# ─────────────────────────────────────────────────────────────────────────────
# 6. NEED HELP NOW BEACON
# ─────────────────────────────────────────────────────────────────────────────

class HelpBeacon(models.Model):
    """Urgent assistance request with countdown timer."""
    CAT_MATH = 'math'
    CAT_CODING = 'coding'
    CAT_WRITING = 'writing'
    CAT_SCIENCE = 'science'
    CAT_EXAM = 'exam'
    CAT_PERSONAL = 'personal'
    CAT_TECH = 'tech'
    CAT_OTHER = 'other'
    CATEGORY_CHOICES = [
        (CAT_MATH, '📐 Math'), (CAT_CODING, '💻 Coding'), (CAT_WRITING, '✍️ Writing'),
        (CAT_SCIENCE, '🔬 Science'), (CAT_EXAM, '📝 Exam Prep'), (CAT_PERSONAL, '🤝 Personal'),
        (CAT_TECH, '🛠️ Tech Help'), (CAT_OTHER, '❓ Other'),
    ]

    URGENCY_LOW = 'low'
    URGENCY_MEDIUM = 'medium'
    URGENCY_HIGH = 'high'
    URGENCY_CHOICES = [
        (URGENCY_LOW, 'Today'), (URGENCY_MEDIUM, 'Within 2 hours'), (URGENCY_HIGH, 'Right now'),
    ]

    MODE_CHAT = 'chat'
    MODE_VOICE = 'voice'
    MODE_EITHER = 'either'
    MODE_CHOICES = [
        (MODE_CHAT, 'Chat'), (MODE_VOICE, 'Voice'), (MODE_EITHER, 'Either'),
    ]

    STATUS_OPEN = 'open'
    STATUS_CLAIMED = 'claimed'
    STATUS_RESOLVED = 'resolved'
    STATUS_EXPIRED = 'expired'
    STATUS_CHOICES = [
        (STATUS_OPEN, 'Open'), (STATUS_CLAIMED, 'Helper Found'),
        (STATUS_RESOLVED, 'Resolved'), (STATUS_EXPIRED, 'Expired'),
    ]

    id = models.UUIDField(primary_key=True, default=_uuid, editable=False)
    requester = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='help_beacons')
    helper = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='help_claims',
    )
    title = models.CharField(max_length=200)
    description = models.TextField(max_length=1000, blank=True)
    category = models.CharField(max_length=10, choices=CATEGORY_CHOICES, default=CAT_OTHER)
    urgency = models.CharField(max_length=8, choices=URGENCY_CHOICES, default=URGENCY_MEDIUM)
    help_mode = models.CharField(max_length=6, choices=MODE_CHOICES, default=MODE_EITHER)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=STATUS_OPEN, db_index=True)
    school_community = models.ForeignKey(
        'community.SchoolCommunity', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='help_beacons',
    )
    # Reputation reward for helper
    reputation_reward = models.PositiveSmallIntegerField(default=10)
    # Ratings after resolution
    helper_rating = models.PositiveSmallIntegerField(null=True, blank=True)  # 1-5
    helper_review = models.TextField(blank=True, max_length=300)
    deadline = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'urgency', 'created_at']),
            models.Index(fields=['category', 'status']),
        ]

    def __str__(self):
        return f'Beacon: {self.title} [{self.status}]'

    @property
    def is_expired(self):
        return self.deadline and timezone.now() > self.deadline and self.status == self.STATUS_OPEN


# ─────────────────────────────────────────────────────────────────────────────
# REPUTATION SYSTEM (cross-feature)
# ─────────────────────────────────────────────────────────────────────────────

class UserReputation(models.Model):
    """Aggregated reputation score per user across all campus features."""
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='campus_reputation'
    )
    score = models.PositiveIntegerField(default=0)
    deals_completed = models.PositiveIntegerField(default=0)
    help_given = models.PositiveIntegerField(default=0)
    avg_rating = models.FloatField(default=0.0)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'Rep({self.user}): {self.score}'
