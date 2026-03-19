"""
Initial migration for the community app.
Creates all tables from scratch — safe to run on any existing DB.
"""

import uuid
import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        # ── SchoolCommunity ───────────────────────────────────────────────────
        migrations.CreateModel(
            name='SchoolCommunity',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=255, unique=True)),
                ('slug', models.SlugField(blank=True, max_length=255, unique=True)),
                ('description', models.TextField(blank=True)),
                ('logo', models.ImageField(blank=True, null=True, upload_to='community/school/logos/')),
                ('banner', models.ImageField(blank=True, null=True, upload_to='community/school/banners/')),
                ('verified', models.BooleanField(default=True)),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={'verbose_name': 'School Community', 'verbose_name_plural': 'School Communities', 'ordering': ['name']},
        ),
        # ── CommunityMembership ───────────────────────────────────────────────
        migrations.CreateModel(
            name='CommunityMembership',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('role', models.CharField(choices=[('member', 'Member'), ('mod', 'Moderator'), ('admin', 'Admin')], default='member', max_length=10)),
                ('joined_at', models.DateTimeField(auto_now_add=True)),
                ('notifications_enabled', models.BooleanField(default=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='community_memberships', to=settings.AUTH_USER_MODEL)),
                ('community', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='memberships', to='community.schoolcommunity')),
            ],
            options={'verbose_name': 'Community Membership', 'verbose_name_plural': 'Community Memberships'},
        ),
        migrations.AddConstraint(
            model_name='communitymembership',
            constraint=models.UniqueConstraint(fields=('user', 'community'), name='unique_user_community'),
        ),
        # ── CustomCommunity ───────────────────────────────────────────────────
        migrations.CreateModel(
            name='CustomCommunity',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=255)),
                ('slug', models.SlugField(blank=True, max_length=255, unique=True)),
                ('description', models.TextField(blank=True)),
                ('privacy', models.CharField(choices=[('public', 'Public'), ('private', 'Private')], default='public', max_length=10)),
                ('logo', models.ImageField(blank=True, null=True, upload_to='community/custom/logos/')),
                ('banner', models.ImageField(blank=True, null=True, upload_to='community/custom/banners/')),
                ('rules', models.TextField(blank=True)),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('creator', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_communities', to=settings.AUTH_USER_MODEL)),
            ],
            options={'verbose_name': 'Custom Community', 'verbose_name_plural': 'Custom Communities', 'ordering': ['-created_at']},
        ),
        # ── Post ──────────────────────────────────────────────────────────────
        migrations.CreateModel(
            name='Post',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('content', models.TextField()),
                ('media', models.FileField(blank=True, null=True, upload_to='community/posts/media/')),
                ('media_type', models.CharField(choices=[('image', 'Image'), ('video', 'Video'), ('file', 'File'), ('none', 'None')], default='none', max_length=10)),
                ('category', models.CharField(blank=True, max_length=100)),
                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('like_count', models.PositiveIntegerField(default=0)),
                ('comment_count', models.PositiveIntegerField(default=0)),
                ('share_count', models.PositiveIntegerField(default=0)),
                ('is_deleted', models.BooleanField(db_index=True, default=False)),
                ('author', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='community_posts', to=settings.AUTH_USER_MODEL)),
                ('school_community', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='posts', to='community.schoolcommunity')),
                ('custom_community', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='posts', to='community.customcommunity')),
            ],
            options={'ordering': ['-created_at']},
        ),
        migrations.AddIndex(
            model_name='post',
            index=models.Index(fields=['created_at'], name='post_created_idx'),
        ),
        migrations.AddIndex(
            model_name='post',
            index=models.Index(fields=['school_community', 'created_at'], name='post_school_comm_idx'),
        ),
        migrations.AddIndex(
            model_name='post',
            index=models.Index(fields=['custom_community', 'created_at'], name='post_custom_comm_idx'),
        ),
        migrations.AddIndex(
            model_name='post',
            index=models.Index(fields=['author', 'created_at'], name='post_author_idx'),
        ),
        migrations.AddIndex(
            model_name='post',
            index=models.Index(fields=['is_deleted', 'created_at'], name='post_deleted_idx'),
        ),
        # ── PostLike ──────────────────────────────────────────────────────────
        migrations.CreateModel(
            name='PostLike',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='post_likes', to=settings.AUTH_USER_MODEL)),
                ('post', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='likes', to='community.post')),
            ],
        ),
        migrations.AddConstraint(
            model_name='postlike',
            constraint=models.UniqueConstraint(fields=('user', 'post'), name='unique_user_post_like'),
        ),
        migrations.AddIndex(
            model_name='postlike',
            index=models.Index(fields=['post', 'created_at'], name='postlike_post_idx'),
        ),
        # ── Comment ───────────────────────────────────────────────────────────
        migrations.CreateModel(
            name='Comment',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('content', models.TextField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('like_count', models.PositiveIntegerField(default=0)),
                ('post', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='comments', to='community.post')),
                ('author', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='community_comments', to=settings.AUTH_USER_MODEL)),
                ('parent', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='replies', to='community.comment')),
            ],
            options={'ordering': ['created_at']},
        ),
        # ── Follow ────────────────────────────────────────────────────────────
        migrations.CreateModel(
            name='Follow',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('follower', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='following_set', to=settings.AUTH_USER_MODEL)),
                ('following', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='followers_set', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.AddConstraint(
            model_name='follow',
            constraint=models.UniqueConstraint(fields=('follower', 'following'), name='unique_follow'),
        ),
        # ── Conversation ──────────────────────────────────────────────────────
        migrations.CreateModel(
            name='Conversation',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('is_group', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True, db_index=True)),
                ('participants', models.ManyToManyField(blank=True, related_name='conversations', to=settings.AUTH_USER_MODEL)),
            ],
            options={'ordering': ['-updated_at']},
        ),
        # ── Message ───────────────────────────────────────────────────────────
        migrations.CreateModel(
            name='Message',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('content', models.TextField(blank=True)),
                ('media', models.FileField(blank=True, null=True, upload_to='community/messages/')),
                ('message_type', models.CharField(choices=[('text', 'Text'), ('image', 'Image'), ('file', 'File')], default='text', max_length=10)),
                ('is_read', models.BooleanField(db_index=True, default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('conversation', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='messages', to='community.conversation')),
                ('sender', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='sent_messages', to=settings.AUTH_USER_MODEL)),
            ],
            options={'ordering': ['created_at']},
        ),
        migrations.AddIndex(
            model_name='message',
            index=models.Index(fields=['conversation', 'created_at'], name='msg_conv_idx'),
        ),
        migrations.AddIndex(
            model_name='message',
            index=models.Index(fields=['sender', 'created_at'], name='msg_sender_idx'),
        ),
        # ── Space ─────────────────────────────────────────────────────────────
        migrations.CreateModel(
            name='Space',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('title', models.CharField(max_length=255)),
                ('description', models.TextField(blank=True)),
                ('is_live', models.BooleanField(default=False)),
                ('allow_video', models.BooleanField(default=False)),
                ('max_participants', models.PositiveIntegerField(default=50)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('ended_at', models.DateTimeField(blank=True, null=True)),
                ('host', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='hosted_spaces', to=settings.AUTH_USER_MODEL)),
                ('school_community', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='spaces', to='community.schoolcommunity')),
                ('custom_community', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='spaces', to='community.customcommunity')),
            ],
            options={'ordering': ['-created_at']},
        ),
        # ── Notification ──────────────────────────────────────────────────────
        migrations.CreateModel(
            name='Notification',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('type', models.CharField(choices=[('like', 'Like'), ('comment', 'Comment'), ('follow', 'Follow'), ('mention', 'Mention'), ('join', 'Join')], max_length=20)),
                ('is_read', models.BooleanField(db_index=True, default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('recipient', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='community_notifications', to=settings.AUTH_USER_MODEL)),
                ('actor', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='community_actions', to=settings.AUTH_USER_MODEL)),
                ('post', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='notifications', to='community.post')),
                ('comment', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='notifications', to='community.comment')),
            ],
            options={'ordering': ['-created_at']},
        ),
        # ── Block ─────────────────────────────────────────────────────────────
        migrations.CreateModel(
            name='Block',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('blocker', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='blocking', to=settings.AUTH_USER_MODEL)),
                ('blocked', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='blocked_by', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.AddConstraint(
            model_name='block',
            constraint=models.UniqueConstraint(fields=('blocker', 'blocked'), name='unique_block'),
        ),
    ]
