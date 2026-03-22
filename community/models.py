"""
Community app models.
All models use UUID PKs for scalability.
Fully self-contained — no modifications to existing apps required.
"""

import uuid
from django.conf import settings
from django.db import models
from django.utils.text import slugify


# ── Helpers ───────────────────────────────────────────────────────────────────

def _uuid():
    return uuid.uuid4()


# ── School (Official) Community ───────────────────────────────────────────────

class SchoolCommunity(models.Model):
    """
    Official, verified school communities (e.g. University of Ghana).
    Pre-seeded via data migration. Not deletable by normal users.
    """
    id = models.UUIDField(primary_key=True, default=_uuid, editable=False)
    name = models.CharField(max_length=255, unique=True)
    slug = models.SlugField(max_length=255, unique=True, blank=True)
    description = models.TextField(blank=True)
    logo = models.ImageField(upload_to='community/school/logos/', null=True, blank=True)
    logo_url = models.URLField(max_length=500, blank=True, default='')
    banner = models.ImageField(upload_to='community/school/banners/', null=True, blank=True)
    verified = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'School Community'
        verbose_name_plural = 'School Communities'
        ordering = ['name']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


# ── Community Membership ──────────────────────────────────────────────────────

class CommunityMembership(models.Model):
    """Tracks which users belong to which SchoolCommunity and their role."""

    ROLE_MEMBER = 'member'
    ROLE_MOD = 'mod'
    ROLE_ADMIN = 'admin'
    ROLE_CHOICES = [
        (ROLE_MEMBER, 'Member'),
        (ROLE_MOD, 'Moderator'),
        (ROLE_ADMIN, 'Admin'),
    ]

    id = models.UUIDField(primary_key=True, default=_uuid, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='community_memberships',
    )
    community = models.ForeignKey(
        SchoolCommunity,
        on_delete=models.CASCADE,
        related_name='memberships',
    )
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default=ROLE_MEMBER)
    joined_at = models.DateTimeField(auto_now_add=True)
    notifications_enabled = models.BooleanField(default=True)

    class Meta:
        unique_together = ('user', 'community')
        verbose_name = 'Community Membership'
        verbose_name_plural = 'Community Memberships'

    def __str__(self):
        return f'{self.user} → {self.community} ({self.role})'


# ── Custom (User-Created) Community ──────────────────────────────────────────

class CustomCommunity(models.Model):
    """User-created communities with public/private privacy settings."""

    PRIVACY_PUBLIC = 'public'
    PRIVACY_RESTRICTED = 'restricted'
    PRIVACY_PRIVATE = 'private'
    PRIVACY_CHOICES = [
        (PRIVACY_PUBLIC, 'Public'),
        (PRIVACY_RESTRICTED, 'Restricted'),
        (PRIVACY_PRIVATE, 'Private'),
    ]

    id = models.UUIDField(primary_key=True, default=_uuid, editable=False)
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True, blank=True)
    description = models.TextField(blank=True)
    creator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_communities',
    )
    privacy = models.CharField(
        max_length=10, choices=PRIVACY_CHOICES, default=PRIVACY_PUBLIC
    )
    logo = models.ImageField(upload_to='community/custom/logos/', null=True, blank=True)
    banner = models.ImageField(upload_to='community/custom/banners/', null=True, blank=True)
    rules = models.TextField(blank=True)
    is_mature = models.BooleanField(default=False)
    topic = models.CharField(max_length=100, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Custom Community'
        verbose_name_plural = 'Custom Communities'
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.name)
            slug = base
            n = 1
            while CustomCommunity.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f'{base}-{n}'
                n += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


# ── Post ──────────────────────────────────────────────────────────────────────

class Post(models.Model):
    """
    A post inside either a SchoolCommunity or a CustomCommunity.
    Exactly one of school_community / custom_community should be set.
    Denormalized counts avoid expensive COUNT queries on hot paths.
    """

    MEDIA_IMAGE = 'image'
    MEDIA_VIDEO = 'video'
    MEDIA_FILE = 'file'
    MEDIA_NONE = 'none'
    MEDIA_TYPE_CHOICES = [
        (MEDIA_IMAGE, 'Image'),
        (MEDIA_VIDEO, 'Video'),
        (MEDIA_FILE, 'File'),
        (MEDIA_NONE, 'None'),
    ]

    id = models.UUIDField(primary_key=True, default=_uuid, editable=False)
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='community_posts',
    )
    school_community = models.ForeignKey(
        SchoolCommunity,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='posts',
    )
    custom_community = models.ForeignKey(
        CustomCommunity,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='posts',
    )
    # feed_only=True means the post is not tied to any community (global feed post)
    feed_only = models.BooleanField(default=False, db_index=True)
    title = models.CharField(max_length=300, blank=True)
    content = models.TextField()
    media = models.FileField(upload_to='community/posts/media/', null=True, blank=True)
    media_type = models.CharField(
        max_length=10, choices=MEDIA_TYPE_CHOICES, default=MEDIA_NONE
    )
    category = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    # Denormalized counters — updated via signals
    like_count = models.PositiveIntegerField(default=0)
    comment_count = models.PositiveIntegerField(default=0)
    share_count = models.PositiveIntegerField(default=0)
    is_deleted = models.BooleanField(default=False, db_index=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['created_at']),
            models.Index(fields=['school_community', 'created_at']),
            models.Index(fields=['custom_community', 'created_at']),
            models.Index(fields=['author', 'created_at']),
            models.Index(fields=['is_deleted', 'created_at']),
        ]

    def __str__(self):
        return f'Post by {self.author} @ {self.created_at:%Y-%m-%d %H:%M}'


# ── Post Like ─────────────────────────────────────────────────────────────────

class PostLike(models.Model):
    """One like per user per post. Signals update Post.like_count."""

    id = models.UUIDField(primary_key=True, default=_uuid, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='post_likes',
    )
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='likes')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'post')
        indexes = [models.Index(fields=['post', 'created_at'])]

    def __str__(self):
        return f'{self.user} likes {self.post_id}'


# ── Comment ───────────────────────────────────────────────────────────────────

class Comment(models.Model):
    """Threaded comments. parent=None means top-level."""

    id = models.UUIDField(primary_key=True, default=_uuid, editable=False)
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='community_comments',
    )
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='replies',
    )
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    like_count = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f'Comment by {self.author} on {self.post_id}'


# ── Follow ────────────────────────────────────────────────────────────────────

class Follow(models.Model):
    """User-to-user follow graph."""

    id = models.UUIDField(primary_key=True, default=_uuid, editable=False)
    follower = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='following_set',
    )
    following = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='followers_set',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('follower', 'following')

    def __str__(self):
        return f'{self.follower} → {self.following}'


# ── Conversation (DMs) ────────────────────────────────────────────────────────

class Conversation(models.Model):
    """A DM thread between 2+ users. Supports group chats."""

    id = models.UUIDField(primary_key=True, default=_uuid, editable=False)
    participants = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='conversations',
        blank=True,
    )
    is_group = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True, db_index=True)

    class Meta:
        ordering = ['-updated_at']

    def __str__(self):
        return f'Conversation {self.id}'


# ── Message ───────────────────────────────────────────────────────────────────

class Message(models.Model):
    """A single message inside a Conversation. Optimised for chat."""

    TYPE_TEXT = 'text'
    TYPE_IMAGE = 'image'
    TYPE_FILE = 'file'
    TYPE_VOICE = 'voice'
    TYPE_VIDEO = 'video'
    TYPE_CHOICES = [
        (TYPE_TEXT, 'Text'),
        (TYPE_IMAGE, 'Image'),
        (TYPE_FILE, 'File'),
        (TYPE_VOICE, 'Voice Note'),
        (TYPE_VIDEO, 'Video'),
    ]

    id = models.UUIDField(primary_key=True, default=_uuid, editable=False)
    conversation = models.ForeignKey(
        Conversation, on_delete=models.CASCADE, related_name='messages'
    )
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='sent_messages',
    )
    content = models.TextField(blank=True)
    media = models.FileField(upload_to='community/messages/', null=True, blank=True)
    voice_note = models.FileField(upload_to='community/voice_notes/', null=True, blank=True)
    message_type = models.CharField(
        max_length=10, choices=TYPE_CHOICES, default=TYPE_TEXT
    )
    is_read = models.BooleanField(default=False, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['conversation', 'created_at']),
            models.Index(fields=['sender', 'created_at']),
        ]

    def __str__(self):
        return f'Message {self.id} in {self.conversation_id}'


# ── Space (Voice/Video Room) ──────────────────────────────────────────────────

class Space(models.Model):
    """
    Metadata for a live voice/video room.
    Actual real-time transport is handled externally (e.g. WebRTC/Channels).
    """

    id = models.UUIDField(primary_key=True, default=_uuid, editable=False)
    host = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='hosted_spaces',
    )
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    school_community = models.ForeignKey(
        SchoolCommunity,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='spaces',
    )
    custom_community = models.ForeignKey(
        CustomCommunity,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='spaces',
    )
    is_live = models.BooleanField(default=False)
    allow_video = models.BooleanField(default=False)
    max_participants = models.PositiveIntegerField(default=50)
    created_at = models.DateTimeField(auto_now_add=True)
    ended_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'Space: {self.title}'


# ── Notification ──────────────────────────────────────────────────────────────

class Notification(models.Model):
    """In-app notifications. Designed to be extended for push/WS later."""

    TYPE_LIKE = 'like'
    TYPE_COMMENT = 'comment'
    TYPE_REPLY = 'reply'
    TYPE_COMMENT_LIKE = 'comment_like'
    TYPE_FOLLOW = 'follow'
    TYPE_MENTION = 'mention'
    TYPE_JOIN = 'join'
    TYPE_FRIEND_REQUEST = 'friend_request'
    TYPE_FRIEND_ACCEPTED = 'friend_accepted'
    TYPE_MESSAGE = 'message'
    TYPE_CHOICES = [
        (TYPE_LIKE, 'Like'),
        (TYPE_COMMENT, 'Comment'),
        (TYPE_REPLY, 'Reply'),
        (TYPE_COMMENT_LIKE, 'Comment Like'),
        (TYPE_FOLLOW, 'Follow'),
        (TYPE_MENTION, 'Mention'),
        (TYPE_JOIN, 'Join'),
        (TYPE_FRIEND_REQUEST, 'Friend Request'),
        (TYPE_FRIEND_ACCEPTED, 'Friend Accepted'),
        (TYPE_MESSAGE, 'Message'),
    ]

    id = models.UUIDField(primary_key=True, default=_uuid, editable=False)
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='community_notifications',
    )
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='community_actions',
    )
    type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    post = models.ForeignKey(
        Post, on_delete=models.CASCADE, null=True, blank=True, related_name='notifications'
    )
    comment = models.ForeignKey(
        Comment,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='notifications',
    )
    conversation = models.ForeignKey(
        'Conversation',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='notifications',
    )
    is_read = models.BooleanField(default=False, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'Notification({self.type}) → {self.recipient}'


# ── Comment Like ─────────────────────────────────────────────────────────────

class CommentLike(models.Model):
    """One like per user per comment."""

    id = models.UUIDField(primary_key=True, default=_uuid, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='comment_likes',
    )
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE, related_name='comment_likes')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'comment')

    def __str__(self):
        return f'{self.user} likes comment {self.comment_id}'


# ── Community Profile ─────────────────────────────────────────────────────────

class CommunityProfile(models.Model):
    """Per-user profile visible in the community section."""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='community_profile',
    )
    display_name = models.CharField(max_length=100, blank=True)
    bio = models.TextField(blank=True, max_length=500)
    location = models.CharField(max_length=100, blank=True)
    website = models.URLField(blank=True)
    avatar = models.ImageField(upload_to='community/profiles/avatars/', null=True, blank=True)
    banner = models.ImageField(upload_to='community/profiles/banners/', null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'CommunityProfile({self.user})'


# ── Block ─────────────────────────────────────────────────────────────────────

class Block(models.Model):
    """User blocking. Blocked users are excluded from feeds and DMs."""

    id = models.UUIDField(primary_key=True, default=_uuid, editable=False)
    blocker = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='blocking',
    )
    blocked = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='blocked_by',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('blocker', 'blocked')

    def __str__(self):
        return f'{self.blocker} blocked {self.blocked}'


# ── Group Workspace ───────────────────────────────────────────────────────────

class GroupWorkspace(models.Model):
    """A private collaborative workspace for group study."""

    PRIVACY_PRIVATE = 'private'
    PRIVACY_REQUEST = 'request'
    PRIVACY_PUBLIC = 'public'
    PRIVACY_CHOICES = [
        (PRIVACY_PRIVATE, 'Private (invite only)'),
        (PRIVACY_REQUEST, 'Visible, join by request'),
        (PRIVACY_PUBLIC, 'Public (anyone can join)'),
    ]

    TYPE_STARTUP = 'startup'
    TYPE_STUDY = 'study_group'
    TYPE_PROJECT = 'group_project'
    TYPE_GENERAL = 'general'
    TYPE_AI_TUTOR = 'ai_tutor'
    TYPE_ASSIGNMENT = 'assignment'
    TYPE_EXAM_PREP = 'exam_prep'
    TYPE_RESEARCH = 'research'
    TYPE_NEXA = 'nexa'
    TYPE_CHOICES = [
        (TYPE_STARTUP, 'Startup'),
        (TYPE_STUDY, 'Study Group'),
        (TYPE_PROJECT, 'Group Project'),
        (TYPE_GENERAL, 'General Collaboration'),
        (TYPE_AI_TUTOR, 'AI Tutor Workspace'),
        (TYPE_ASSIGNMENT, 'Assignment Solver'),
        (TYPE_EXAM_PREP, 'Exam Prep'),
        (TYPE_RESEARCH, 'Research'),
        (TYPE_NEXA, 'Nexa Workspace'),
    ]

    id = models.UUIDField(primary_key=True, default=_uuid, editable=False)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    subject = models.CharField(max_length=100, blank=True)
    workspace_type = models.CharField(
        max_length=20, choices=TYPE_CHOICES, default=TYPE_GENERAL
    )
    privacy = models.CharField(max_length=10, choices=PRIVACY_CHOICES, default=PRIVACY_PRIVATE)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='owned_workspaces',
    )
    invite_code = models.CharField(max_length=12, unique=True, blank=True)
    is_active = models.BooleanField(default=True)
    is_personal = models.BooleanField(default=False, db_index=True)  # auto-created personal workspace
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Group Workspace'
        verbose_name_plural = 'Group Workspaces'

    def save(self, *args, **kwargs):
        if not self.invite_code:
            import secrets, string
            alphabet = string.ascii_uppercase + string.digits
            while True:
                code = ''.join(secrets.choice(alphabet) for _ in range(8))
                if not GroupWorkspace.objects.filter(invite_code=code).exists():
                    self.invite_code = code
                    break
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class WorkspaceMember(models.Model):
    """Membership of a user in a GroupWorkspace."""

    ROLE_OWNER = 'owner'
    ROLE_ADMIN = 'admin'
    ROLE_MEMBER = 'member'
    ROLE_CHOICES = [
        (ROLE_OWNER, 'Owner'),
        (ROLE_ADMIN, 'Admin'),
        (ROLE_MEMBER, 'Member'),
    ]

    id = models.UUIDField(primary_key=True, default=_uuid, editable=False)
    workspace = models.ForeignKey(
        GroupWorkspace, on_delete=models.CASCADE, related_name='members'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='workspace_memberships',
    )
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default=ROLE_MEMBER)
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('workspace', 'user')
        verbose_name = 'Workspace Member'

    def __str__(self):
        return f'{self.user} in {self.workspace} ({self.role})'


class WorkspaceMessage(models.Model):
    """Chat message inside a GroupWorkspace."""

    id = models.UUIDField(primary_key=True, default=_uuid, editable=False)
    workspace = models.ForeignKey(
        GroupWorkspace, on_delete=models.CASCADE, related_name='chat_messages'
    )
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='workspace_messages',
    )
    content = models.TextField(blank=True)
    media = models.FileField(upload_to='workspace/files/', null=True, blank=True)
    media_name = models.CharField(max_length=255, blank=True)
    reply_to = models.ForeignKey(
        'self', null=True, blank=True,
        on_delete=models.SET_NULL, related_name='replies'
    )
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f'WS msg {self.id}'


class WorkspaceFile(models.Model):
    """File uploaded to a GroupWorkspace — visible to all members."""

    id = models.UUIDField(primary_key=True, default=_uuid, editable=False)
    workspace = models.ForeignKey(
        GroupWorkspace, on_delete=models.CASCADE, related_name='files'
    )
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='workspace_files',
    )
    file = models.FileField(upload_to='workspace/files/')
    original_name = models.CharField(max_length=255)
    file_size = models.PositiveIntegerField(default=0)  # bytes
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-uploaded_at']

    def __str__(self):
        return self.original_name


class WorkspaceTask(models.Model):
    """A task/study item on the workspace board."""

    STATUS_TODO = 'todo'
    STATUS_DOING = 'doing'
    STATUS_DONE = 'done'
    STATUS_CHOICES = [
        (STATUS_TODO, 'To Do'),
        (STATUS_DOING, 'In Progress'),
        (STATUS_DONE, 'Done'),
    ]

    REVIEW_NONE = 'none'
    REVIEW_PENDING = 'pending'
    REVIEW_APPROVED = 'approved'
    REVIEW_REVISION = 'revision'
    REVIEW_CHOICES = [
        (REVIEW_NONE, 'No submission'),
        (REVIEW_PENDING, 'Pending review'),
        (REVIEW_APPROVED, 'Approved'),
        (REVIEW_REVISION, 'Revision requested'),
    ]

    id = models.UUIDField(primary_key=True, default=_uuid, editable=False)
    workspace = models.ForeignKey(
        GroupWorkspace, on_delete=models.CASCADE, related_name='tasks'
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='created_tasks',
    )
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_tasks',
    )
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=STATUS_TODO)
    due_date = models.DateField(null=True, blank=True)
    # Contribution / review fields
    submission = models.TextField(blank=True)
    review_status = models.CharField(max_length=10, choices=REVIEW_CHOICES, default=REVIEW_NONE)
    review_feedback = models.TextField(blank=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['status', 'due_date', 'created_at']

    def __str__(self):
        return self.title


# ── Meeting Record ───────────────────────────────────────────────────────────

class MeetingRecord(models.Model):
    """Auto-captured record of a group call with AI summary."""

    id = models.UUIDField(primary_key=True, default=_uuid, editable=False)
    workspace = models.ForeignKey(
        GroupWorkspace, on_delete=models.CASCADE, related_name='meeting_records'
    )
    started_at = models.DateTimeField()
    ended_at = models.DateTimeField(null=True, blank=True)
    participants = models.JSONField(default=list)   # list of usernames
    chat_log = models.JSONField(default=list)        # messages during call
    ai_summary = models.TextField(blank=True)
    decisions = models.JSONField(default=list)
    action_items = models.JSONField(default=list)
    key_topics = models.JSONField(default=list)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-started_at']
        verbose_name = 'Meeting Record'

    def __str__(self):
        return f'Meeting in {self.workspace} @ {self.started_at:%Y-%m-%d %H:%M}'


# ── Friendship ────────────────────────────────────────────────────────────────

class Friendship(models.Model):
    """Friend request and friendship tracking."""

    STATUS_PENDING = 'pending'
    STATUS_ACCEPTED = 'accepted'
    STATUS_REJECTED = 'rejected'
    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending'),
        (STATUS_ACCEPTED, 'Accepted'),
        (STATUS_REJECTED, 'Rejected'),
    ]

    id = models.UUIDField(primary_key=True, default=_uuid, editable=False)
    requester = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='friend_requests_sent',
    )
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='friend_requests_received',
    )
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=STATUS_PENDING)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('requester', 'recipient')
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.requester} → {self.recipient} ({self.status})'


# ── Nexa Workspace Link ───────────────────────────────────────────────────────

class NexaWorkspaceLink(models.Model):
    """Links a personal Nexa workspace to one or more group workspaces."""

    id = models.UUIDField(primary_key=True, default=_uuid, editable=False)
    nexa_workspace = models.ForeignKey(
        GroupWorkspace,
        on_delete=models.CASCADE,
        related_name='linked_group_workspaces',
        limit_choices_to={'workspace_type': 'nexa', 'is_personal': True},
    )
    linked_workspace = models.ForeignKey(
        GroupWorkspace,
        on_delete=models.CASCADE,
        related_name='nexa_links',
    )
    linked_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('nexa_workspace', 'linked_workspace')
        ordering = ['-linked_at']

    def __str__(self):
        return f'{self.nexa_workspace} → {self.linked_workspace}'


# ── Custom Community Membership ───────────────────────────────────────────────

class CustomCommunityMembership(models.Model):
    """Tracks which users belong to which CustomCommunity."""

    id = models.UUIDField(primary_key=True, default=_uuid, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='custom_community_memberships',
    )
    community = models.ForeignKey(
        CustomCommunity,
        on_delete=models.CASCADE,
        related_name='memberships',
    )
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'community')
        verbose_name = 'Custom Community Membership'
        verbose_name_plural = 'Custom Community Memberships'

    def __str__(self):
        return f'{self.user} → {self.community}'

