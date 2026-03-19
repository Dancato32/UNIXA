"""
Migration: add feed_only + title to Post, add CommentLike, add CommunityProfile.
"""

import uuid
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('community', '0002_seed_school_communities'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        # Post: feed_only flag
        migrations.AddField(
            model_name='post',
            name='feed_only',
            field=models.BooleanField(default=False, db_index=True),
        ),
        # Post: optional title
        migrations.AddField(
            model_name='post',
            name='title',
            field=models.CharField(blank=True, max_length=300),
        ),
        # CommentLike
        migrations.CreateModel(
            name='CommentLike',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='comment_likes', to=settings.AUTH_USER_MODEL)),
                ('comment', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='comment_likes', to='community.comment')),
            ],
        ),
        migrations.AlterUniqueTogether(
            name='commentlike',
            unique_together={('user', 'comment')},
        ),
        # CommunityProfile
        migrations.CreateModel(
            name='CommunityProfile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('bio', models.TextField(blank=True, max_length=500)),
                ('avatar', models.ImageField(blank=True, null=True, upload_to='community/profiles/avatars/')),
                ('banner', models.ImageField(blank=True, null=True, upload_to='community/profiles/banners/')),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='community_profile', to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
