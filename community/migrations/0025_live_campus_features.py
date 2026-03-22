import uuid
import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


def _uuid():
    return uuid.uuid4()


class Migration(migrations.Migration):

    dependencies = [
        ('community', '0024_add_interests_to_communityprofile'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        # ── SkillOffer ──
        migrations.CreateModel(
            name='SkillOffer',
            fields=[
                ('id', models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, serialize=False)),
                ('listing_type', models.CharField(choices=[('offer', 'Offering'), ('request', 'Requesting')], default='offer', max_length=10)),
                ('title', models.CharField(max_length=120)),
                ('description', models.TextField(blank=True, max_length=500)),
                ('skill_tag', models.CharField(max_length=50)),
                ('wants_tag', models.CharField(blank=True, max_length=50)),
                ('urgency', models.CharField(choices=[('low', 'Flexible'), ('medium', 'This week'), ('high', 'Urgent')], default='low', max_length=10)),
                ('status', models.CharField(choices=[('open', 'Open'), ('matched', 'Matched'), ('closed', 'Closed')], default='open', max_length=10)),
                ('upvote_count', models.PositiveIntegerField(default=0)),
                ('view_count', models.PositiveIntegerField(default=0)),
                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('expires_at', models.DateTimeField(blank=True, null=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='skill_offers', to=settings.AUTH_USER_MODEL)),
                ('school_community', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='skill_offers', to='community.schoolcommunity')),
            ],
            options={'ordering': ['-created_at']},
        ),
        # ── SkillDeal ──
        migrations.CreateModel(
            name='SkillDeal',
            fields=[
                ('id', models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, serialize=False)),
                ('message', models.TextField(blank=True, max_length=300)),
                ('status', models.CharField(choices=[('pending', 'Pending'), ('active', 'In Progress'), ('complete', 'Complete'), ('cancelled', 'Cancelled')], default='pending', max_length=12)),
                ('initiator_rating', models.PositiveSmallIntegerField(blank=True, null=True)),
                ('responder_rating', models.PositiveSmallIntegerField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('offer', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='deals', to='community.skilloffer')),
                ('initiator', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='initiated_deals', to=settings.AUTH_USER_MODEL)),
                ('responder', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='received_deals', to=settings.AUTH_USER_MODEL)),
                ('conversation', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='skill_deals', to='community.conversation')),
            ],
            options={'ordering': ['-created_at']},
        ),
        # ── Confession ──
        migrations.CreateModel(
            name='Confession',
            fields=[
                ('id', models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, serialize=False)),
                ('content', models.TextField(max_length=1000)),
                ('category', models.CharField(choices=[('academic', 'Academic'), ('mental_health', 'Mental Health'), ('relationships', 'Relationships'), ('finance', 'Finance'), ('career', 'Career'), ('social', 'Social'), ('general', 'General')], default='general', max_length=20)),
                ('status', models.CharField(choices=[('active', 'Active'), ('flagged', 'Flagged'), ('removed', 'Removed')], default='active', max_length=10)),
                ('upvote_count', models.PositiveIntegerField(default=0)),
                ('reply_count', models.PositiveIntegerField(default=0)),
                ('is_crisis', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('author', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='confessions', to=settings.AUTH_USER_MODEL)),
                ('school_community', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='confessions', to='community.schoolcommunity')),
            ],
            options={'ordering': ['-created_at']},
        ),
        # ── ConfessionUpvote ──
        migrations.CreateModel(
            name='ConfessionUpvote',
            fields=[
                ('id', models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='confession_upvotes', to=settings.AUTH_USER_MODEL)),
                ('confession', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='upvotes', to='community.confession')),
            ],
            options={'unique_together': {('user', 'confession')}},
        ),
        # ── ConfessionReply ──
        migrations.CreateModel(
            name='ConfessionReply',
            fields=[
                ('id', models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, serialize=False)),
                ('content', models.TextField(max_length=500)),
                ('is_anonymous', models.BooleanField(default=False)),
                ('is_helpful', models.BooleanField(default=False)),
                ('is_solved', models.BooleanField(default=False)),
                ('upvote_count', models.PositiveIntegerField(default=0)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('confession', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='replies', to='community.confession')),
                ('author', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='confession_replies', to=settings.AUTH_USER_MODEL)),
            ],
            options={'ordering': ['created_at']},
        ),
        # ── Startup ──
        migrations.CreateModel(
            name='Startup',
            fields=[
                ('id', models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, serialize=False)),
                ('name', models.CharField(max_length=120)),
                ('slug', models.SlugField(blank=True, max_length=140, unique=True)),
                ('tagline', models.CharField(blank=True, max_length=200)),
                ('description', models.TextField(blank=True)),
                ('logo', models.ImageField(blank=True, null=True, upload_to='community/startups/logos/')),
                ('stage', models.CharField(choices=[('idea', 'Idea'), ('team', 'Team Formation'), ('build', 'Building'), ('demo', 'Demo Ready'), ('launch', 'Launched')], default='idea', max_length=10)),
                ('skills_needed', models.CharField(blank=True, max_length=300)),
                ('follower_count', models.PositiveIntegerField(default=0)),
                ('is_recruiting', models.BooleanField(default=False)),
                ('demo_url', models.URLField(blank=True)),
                ('support_interest_count', models.PositiveIntegerField(default=0)),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('founder', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='community_founded_startups', to=settings.AUTH_USER_MODEL)),
                ('school_community', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='startups', to='community.schoolcommunity')),
            ],
            options={'ordering': ['-created_at']},
        ),
        # ── StartupMember ──
        migrations.CreateModel(
            name='StartupMember',
            fields=[
                ('id', models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, serialize=False)),
                ('role', models.CharField(choices=[('founder', 'Founder'), ('cofounder', 'Co-Founder'), ('member', 'Team Member')], default='member', max_length=12)),
                ('skill_contribution', models.CharField(blank=True, max_length=100)),
                ('joined_at', models.DateTimeField(auto_now_add=True)),
                ('startup', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='members', to='community.startup')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='community_startup_memberships', to=settings.AUTH_USER_MODEL)),
            ],
            options={'unique_together': {('startup', 'user')}},
        ),
        # ── StartupUpdate ──
        migrations.CreateModel(
            name='StartupUpdate',
            fields=[
                ('id', models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, serialize=False)),
                ('content', models.TextField(max_length=1000)),
                ('milestone', models.CharField(blank=True, max_length=120)),
                ('media', models.FileField(blank=True, null=True, upload_to='community/startups/updates/')),
                ('like_count', models.PositiveIntegerField(default=0)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('startup', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='updates', to='community.startup')),
                ('author', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='startup_updates', to=settings.AUTH_USER_MODEL)),
            ],
            options={'ordering': ['-created_at']},
        ),
        # ── StartupFollow ──
        migrations.CreateModel(
            name='StartupFollow',
            fields=[
                ('id', models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='startup_follows', to=settings.AUTH_USER_MODEL)),
                ('startup', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='followers', to='community.startup')),
            ],
            options={'unique_together': {('user', 'startup')}},
        ),
        # ── PulseEvent ──
        migrations.CreateModel(
            name='PulseEvent',
            fields=[
                ('id', models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, serialize=False)),
                ('title', models.CharField(max_length=120)),
                ('description', models.TextField(blank=True, max_length=300)),
                ('event_type', models.CharField(choices=[('study', 'Study Group'), ('event', 'Event'), ('social', 'Social'), ('recruitment', 'Recruitment'), ('academic', 'Academic'), ('online', 'Online Only'), ('voice_room', 'Voice Room'), ('help', 'Help Needed')], default='study', max_length=15)),
                ('location_name', models.CharField(blank=True, max_length=120)),
                ('lat', models.FloatField(blank=True, null=True)),
                ('lng', models.FloatField(blank=True, null=True)),
                ('is_online', models.BooleanField(default=False)),
                ('max_participants', models.PositiveSmallIntegerField(default=0)),
                ('participant_count', models.PositiveIntegerField(default=1)),
                ('is_private', models.BooleanField(default=False)),
                ('starts_at', models.DateTimeField()),
                ('expires_at', models.DateTimeField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('host', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='pulse_events', to=settings.AUTH_USER_MODEL)),
                ('school_community', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='pulse_events', to='community.schoolcommunity')),
            ],
            options={'ordering': ['expires_at'], 'indexes': [models.Index(fields=['expires_at', 'is_private'], name='community_p_expires_idx')]},
        ),
        # ── PulseJoin ──
        migrations.CreateModel(
            name='PulseJoin',
            fields=[
                ('id', models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, serialize=False)),
                ('joined_at', models.DateTimeField(auto_now_add=True)),
                ('event', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='joins', to='community.pulseevent')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='pulse_joins', to=settings.AUTH_USER_MODEL)),
            ],
            options={'unique_together': {('event', 'user')}},
        ),
        # ── MicroRoom ──
        migrations.CreateModel(
            name='MicroRoom',
            fields=[
                ('id', models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, serialize=False)),
                ('topic', models.CharField(max_length=120)),
                ('status', models.CharField(choices=[('open', 'Open'), ('locked', 'Locked'), ('closed', 'Closed')], default='open', max_length=8)),
                ('participant_count', models.PositiveSmallIntegerField(default=1)),
                ('max_participants', models.PositiveSmallIntegerField(default=20)),
                ('peer_room_id', models.CharField(blank=True, max_length=64)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('closed_at', models.DateTimeField(blank=True, null=True)),
                ('host', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='hosted_micro_rooms', to=settings.AUTH_USER_MODEL)),
                ('school_community', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='micro_rooms', to='community.schoolcommunity')),
            ],
            options={'ordering': ['-created_at']},
        ),
        # ── MicroRoomParticipant ──
        migrations.CreateModel(
            name='MicroRoomParticipant',
            fields=[
                ('id', models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, serialize=False)),
                ('is_muted', models.BooleanField(default=False)),
                ('joined_at', models.DateTimeField(auto_now_add=True)),
                ('left_at', models.DateTimeField(blank=True, null=True)),
                ('room', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='participants', to='community.microroom')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='micro_room_participations', to=settings.AUTH_USER_MODEL)),
            ],
            options={'unique_together': {('room', 'user')}},
        ),
        # ── HelpBeacon ──
        migrations.CreateModel(
            name='HelpBeacon',
            fields=[
                ('id', models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, serialize=False)),
                ('title', models.CharField(max_length=120)),
                ('description', models.TextField(blank=True, max_length=500)),
                ('category', models.CharField(choices=[('academic', 'Academic'), ('tech', 'Tech / Coding'), ('design', 'Design'), ('writing', 'Writing'), ('math', 'Math'), ('other', 'Other')], default='other', max_length=12)),
                ('urgency', models.CharField(choices=[('low', 'Flexible'), ('medium', 'Today'), ('high', 'Right Now')], default='medium', max_length=8)),
                ('status', models.CharField(choices=[('open', 'Open'), ('claimed', 'Claimed'), ('resolved', 'Resolved'), ('expired', 'Expired')], default='open', max_length=10)),
                ('helper_rating', models.PositiveSmallIntegerField(blank=True, null=True)),
                ('prefer_voice', models.BooleanField(default=False)),
                ('deadline', models.DateTimeField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('resolved_at', models.DateTimeField(blank=True, null=True)),
                ('requester', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='help_beacons', to=settings.AUTH_USER_MODEL)),
                ('helper', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='claimed_beacons', to=settings.AUTH_USER_MODEL)),
                ('school_community', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='help_beacons', to='community.schoolcommunity')),
                ('conversation', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='help_beacons', to='community.conversation')),
            ],
            options={'ordering': ['-created_at']},
        ),
    ]
