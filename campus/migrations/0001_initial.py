import uuid
import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('community', '0024_add_interests_to_communityprofile'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        # ── UserReputation ────────────────────────────────────────────────────
        migrations.CreateModel(
            name='UserReputation',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ('score', models.PositiveIntegerField(default=0)),
                ('deals_completed', models.PositiveIntegerField(default=0)),
                ('help_given', models.PositiveIntegerField(default=0)),
                ('avg_rating', models.FloatField(default=0.0)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='campus_reputation', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        # ── SkillListing ──────────────────────────────────────────────────────
        migrations.CreateModel(
            name='SkillListing',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('listing_type', models.CharField(choices=[('offer', 'I can offer'), ('request', 'I need help with')], default='offer', max_length=10)),
                ('title', models.CharField(max_length=200)),
                ('description', models.TextField(blank=True, max_length=1000)),
                ('skill_tag', models.CharField(choices=[('coding', 'Coding'), ('design', 'Design'), ('writing', 'Writing'), ('tutoring', 'Tutoring'), ('math', 'Mathematics'), ('science', 'Science'), ('music', 'Music'), ('video', 'Video Editing'), ('photography', 'Photography'), ('language', 'Language'), ('business', 'Business'), ('research', 'Research'), ('data', 'Data Analysis'), ('marketing', 'Marketing'), ('law', 'Law'), ('medicine', 'Medicine'), ('engineering', 'Engineering'), ('other', 'Other')], default='other', max_length=20)),
                ('exchange_for', models.CharField(blank=True, max_length=200)),
                ('urgency', models.CharField(choices=[('low', 'Flexible'), ('medium', 'This week'), ('high', 'Urgent')], default='low', max_length=10)),
                ('status', models.CharField(choices=[('open', 'Open'), ('matched', 'In Progress'), ('done', 'Completed')], default='open', max_length=10)),
                ('view_count', models.PositiveIntegerField(default=0)),
                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('expires_at', models.DateTimeField(blank=True, null=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='skill_listings', to=settings.AUTH_USER_MODEL)),
                ('school_community', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='skill_listings', to='community.schoolcommunity')),
            ],
            options={'ordering': ['-created_at']},
        ),
        migrations.AddIndex(model_name='skilllisting', index=models.Index(fields=['skill_tag', 'status', 'created_at'], name='campus_skil_skill_t_idx')),
        migrations.AddIndex(model_name='skilllisting', index=models.Index(fields=['listing_type', 'status'], name='campus_skil_listing_idx')),
        # ── SkillDeal ─────────────────────────────────────────────────────────
        migrations.CreateModel(
            name='SkillDeal',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('message', models.TextField(blank=True, max_length=500)),
                ('status', models.CharField(choices=[('pending', 'Pending'), ('active', 'Active'), ('done', 'Completed'), ('cancelled', 'Cancelled')], default='pending', max_length=12)),
                ('initiator_rating', models.PositiveSmallIntegerField(blank=True, null=True)),
                ('receiver_rating', models.PositiveSmallIntegerField(blank=True, null=True)),
                ('initiator_review', models.TextField(blank=True, max_length=300)),
                ('receiver_review', models.TextField(blank=True, max_length=300)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('initiator', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='deals_initiated', to=settings.AUTH_USER_MODEL)),
                ('receiver', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='deals_received', to=settings.AUTH_USER_MODEL)),
                ('listing', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='deals', to='campus.skilllisting')),
            ],
            options={'ordering': ['-created_at']},
        ),
        # ── Confession ────────────────────────────────────────────────────────
        migrations.CreateModel(
            name='Confession',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('content', models.TextField(max_length=2000)),
                ('category', models.CharField(choices=[('academic', 'Academic'), ('mental_health', 'Mental Health'), ('relationships', 'Relationships'), ('finance', 'Finance'), ('career', 'Career'), ('social', 'Social'), ('funny', 'Funny'), ('advice', 'Advice Needed'), ('other', 'Other')], default='other', max_length=20)),
                ('status', models.CharField(choices=[('visible', 'Visible'), ('flagged', 'Flagged'), ('removed', 'Removed')], default='visible', max_length=10)),
                ('is_crisis', models.BooleanField(db_index=True, default=False)),
                ('upvote_count', models.PositiveIntegerField(default=0)),
                ('reply_count', models.PositiveIntegerField(default=0)),
                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('author', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='confessions', to=settings.AUTH_USER_MODEL)),
                ('school_community', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='confessions', to='community.schoolcommunity')),
            ],
            options={'ordering': ['-created_at']},
        ),
        migrations.AddIndex(model_name='confession', index=models.Index(fields=['category', 'status', 'created_at'], name='campus_conf_cat_idx')),
        migrations.AddIndex(model_name='confession', index=models.Index(fields=['status', 'upvote_count'], name='campus_conf_upvote_idx')),
        # ── ConfessionUpvote ──────────────────────────────────────────────────
        migrations.CreateModel(
            name='ConfessionUpvote',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='confession_upvotes', to=settings.AUTH_USER_MODEL)),
                ('confession', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='upvotes', to='campus.confession')),
            ],
        ),
        migrations.AlterUniqueTogether(name='confessionupvote', unique_together={('user', 'confession')}),
        # ── ConfessionReply ───────────────────────────────────────────────────
        migrations.CreateModel(
            name='ConfessionReply',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('content', models.TextField(max_length=1000)),
                ('is_anonymous', models.BooleanField(default=False)),
                ('is_helpful', models.BooleanField(default=False)),
                ('is_solved', models.BooleanField(default=False)),
                ('helpful_count', models.PositiveIntegerField(default=0)),
                ('is_flagged', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('confession', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='replies', to='campus.confession')),
                ('author', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='confession_replies', to=settings.AUTH_USER_MODEL)),
            ],
            options={'ordering': ['created_at']},
        ),
        # ── Startup ───────────────────────────────────────────────────────────
        migrations.CreateModel(
            name='Startup',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=200)),
                ('tagline', models.CharField(blank=True, max_length=300)),
                ('description', models.TextField(blank=True)),
                ('industry', models.CharField(blank=True, max_length=100)),
                ('stage', models.CharField(choices=[('idea', '💡 Idea'), ('forming', '🧩 Forming Team'), ('building', '🔨 Building'), ('demo', '🎤 Demo Ready'), ('launched', '🚀 Launched')], default='idea', max_length=12)),
                ('logo', models.ImageField(blank=True, null=True, upload_to='campus/startups/logos/')),
                ('website', models.URLField(blank=True)),
                ('looking_for', models.CharField(blank=True, max_length=500)),
                ('follower_count', models.PositiveIntegerField(default=0)),
                ('is_recruiting', models.BooleanField(db_index=True, default=True)),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('founder', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='startups_founded', to=settings.AUTH_USER_MODEL)),
                ('school_community', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='startups', to='community.schoolcommunity')),
            ],
            options={'ordering': ['-created_at']},
        ),
        # ── StartupMember ─────────────────────────────────────────────────────
        migrations.CreateModel(
            name='StartupMember',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('role', models.CharField(choices=[('founder', 'Founder'), ('cofounder', 'Co-Founder'), ('developer', 'Developer'), ('designer', 'Designer'), ('marketing', 'Marketing'), ('advisor', 'Advisor'), ('other', 'Other')], default='other', max_length=12)),
                ('status', models.CharField(choices=[('pending', 'Pending'), ('active', 'Active')], default='pending', max_length=10)),
                ('joined_at', models.DateTimeField(auto_now_add=True)),
                ('startup', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='members', to='campus.startup')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='startup_memberships', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.AlterUniqueTogether(name='startupmember', unique_together={('startup', 'user')}),
        # ── StartupUpdate ─────────────────────────────────────────────────────
        migrations.CreateModel(
            name='StartupUpdate',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('content', models.TextField(max_length=2000)),
                ('milestone', models.CharField(blank=True, max_length=200)),
                ('media', models.FileField(blank=True, null=True, upload_to='campus/startups/updates/')),
                ('like_count', models.PositiveIntegerField(default=0)),
                ('comment_count', models.PositiveIntegerField(default=0)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('startup', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='updates', to='campus.startup')),
                ('author', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='startup_updates', to=settings.AUTH_USER_MODEL)),
            ],
            options={'ordering': ['-created_at']},
        ),
        # ── StartupFollow ─────────────────────────────────────────────────────
        migrations.CreateModel(
            name='StartupFollow',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='startups_followed', to=settings.AUTH_USER_MODEL)),
                ('startup', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='followers', to='campus.startup')),
            ],
        ),
        migrations.AlterUniqueTogether(name='startupfollow', unique_together={('user', 'startup')}),
        # ── StartupSupportInterest ────────────────────────────────────────────
        migrations.CreateModel(
            name='StartupSupportInterest',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('interest_type', models.CharField(choices=[('mentor', 'Mentor'), ('investor', 'Investor'), ('collaborator', 'Collaborator')], max_length=14)),
                ('message', models.TextField(blank=True, max_length=500)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='startup_interests', to=settings.AUTH_USER_MODEL)),
                ('startup', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='support_interests', to='campus.startup')),
            ],
        ),
        migrations.AlterUniqueTogether(name='startupsupportinterest', unique_together={('user', 'startup', 'interest_type')}),
        # ── VoiceRoom ─────────────────────────────────────────────────────────
        migrations.CreateModel(
            name='VoiceRoom',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('topic', models.CharField(max_length=200)),
                ('status', models.CharField(choices=[('open', 'Open'), ('locked', 'Locked'), ('closed', 'Closed')], default='open', max_length=8)),
                ('participant_count', models.PositiveSmallIntegerField(default=1)),
                ('max_participants', models.PositiveSmallIntegerField(default=20)),
                ('is_low_bandwidth', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('ended_at', models.DateTimeField(blank=True, null=True)),
                ('host', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='voice_rooms_hosted', to=settings.AUTH_USER_MODEL)),
                ('school_community', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='voice_rooms', to='community.schoolcommunity')),
            ],
            options={'ordering': ['-created_at']},
        ),
        # ── VoiceRoomParticipant ──────────────────────────────────────────────
        migrations.CreateModel(
            name='VoiceRoomParticipant',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('is_muted', models.BooleanField(default=False)),
                ('joined_at', models.DateTimeField(auto_now_add=True)),
                ('left_at', models.DateTimeField(blank=True, null=True)),
                ('room', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='participants', to='campus.voiceroom')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='voice_room_sessions', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.AlterUniqueTogether(name='voiceroomparticipant', unique_together={('room', 'user')}),
        # ── PulseActivity ─────────────────────────────────────────────────────
        migrations.CreateModel(
            name='PulseActivity',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('activity_type', models.CharField(choices=[('study', '📚 Study Group'), ('event', '🎉 Event'), ('social', '👋 Social'), ('recruitment', '🔍 Recruitment'), ('academic', '🎓 Academic'), ('online', '💻 Online Only'), ('voice_room', '🎤 Voice Room'), ('help', '🆘 Help Needed'), ('startup', '🚀 Startup')], db_index=True, max_length=12)),
                ('title', models.CharField(max_length=200)),
                ('description', models.TextField(blank=True, max_length=500)),
                ('location_name', models.CharField(blank=True, max_length=200)),
                ('latitude', models.DecimalField(blank=True, decimal_places=6, max_digits=9, null=True)),
                ('longitude', models.DecimalField(blank=True, decimal_places=6, max_digits=9, null=True)),
                ('max_participants', models.PositiveSmallIntegerField(default=0)),
                ('participant_count', models.PositiveIntegerField(default=1)),
                ('is_private', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('expires_at', models.DateTimeField(db_index=True)),
                ('host', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='pulse_activities', to=settings.AUTH_USER_MODEL)),
                ('school_community', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='pulse_activities', to='community.schoolcommunity')),
                ('voice_room', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='pulse_entries', to='campus.voiceroom')),
                ('help_beacon', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='pulse_entries', to='campus.helpbeacon')),
                ('startup', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='pulse_entries', to='campus.startup')),
            ],
            options={'ordering': ['-created_at']},
        ),
        migrations.AddIndex(model_name='pulseactivity', index=models.Index(fields=['activity_type', 'expires_at'], name='campus_puls_type_exp_idx')),
        migrations.AddIndex(model_name='pulseactivity', index=models.Index(fields=['school_community', 'expires_at'], name='campus_puls_school_idx')),
        # ── PulseJoin ─────────────────────────────────────────────────────────
        migrations.CreateModel(
            name='PulseJoin',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('joined_at', models.DateTimeField(auto_now_add=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='pulse_joins', to=settings.AUTH_USER_MODEL)),
                ('activity', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='joins', to='campus.pulseactivity')),
            ],
        ),
        migrations.AlterUniqueTogether(name='pulsejoin', unique_together={('user', 'activity')}),
        # ── HelpBeacon ────────────────────────────────────────────────────────
        migrations.CreateModel(
            name='HelpBeacon',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('title', models.CharField(max_length=200)),
                ('description', models.TextField(blank=True, max_length=1000)),
                ('category', models.CharField(choices=[('math', '📐 Math'), ('coding', '💻 Coding'), ('writing', '✍️ Writing'), ('science', '🔬 Science'), ('exam', '📝 Exam Prep'), ('personal', '🤝 Personal'), ('tech', '🛠️ Tech Help'), ('other', '❓ Other')], default='other', max_length=10)),
                ('urgency', models.CharField(choices=[('low', 'Today'), ('medium', 'Within 2 hours'), ('high', 'Right now')], default='medium', max_length=8)),
                ('help_mode', models.CharField(choices=[('chat', 'Chat'), ('voice', 'Voice'), ('either', 'Either')], default='either', max_length=6)),
                ('status', models.CharField(choices=[('open', 'Open'), ('claimed', 'Helper Found'), ('resolved', 'Resolved'), ('expired', 'Expired')], db_index=True, default='open', max_length=10)),
                ('reputation_reward', models.PositiveSmallIntegerField(default=10)),
                ('helper_rating', models.PositiveSmallIntegerField(blank=True, null=True)),
                ('helper_review', models.TextField(blank=True, max_length=300)),
                ('deadline', models.DateTimeField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('resolved_at', models.DateTimeField(blank=True, null=True)),
                ('requester', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='help_beacons', to=settings.AUTH_USER_MODEL)),
                ('helper', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='help_claims', to=settings.AUTH_USER_MODEL)),
                ('school_community', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='help_beacons', to='community.schoolcommunity')),
            ],
            options={'ordering': ['-created_at']},
        ),
        migrations.AddIndex(model_name='helpbeacon', index=models.Index(fields=['status', 'urgency', 'created_at'], name='campus_help_status_idx')),
        migrations.AddIndex(model_name='helpbeacon', index=models.Index(fields=['category', 'status'], name='campus_help_cat_idx')),
    ]
