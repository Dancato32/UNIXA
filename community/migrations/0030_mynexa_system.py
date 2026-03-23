"""
Migration 0030: MyNexa local-first workspace system.
Adds NexaDraft and NexaSyncLog models.
"""
import uuid
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


def _uuid():
    return uuid.uuid4()


class Migration(migrations.Migration):

    dependencies = [
        ('community', '0029_roomcomment'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='NexaDraft',
            fields=[
                ('id', models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, serialize=False)),
                ('tool', models.CharField(max_length=50, db_index=True,
                    help_text='Tool key: chat, search, essay, para, cite, extract, lit, topics')),
                ('title', models.CharField(max_length=255, blank=True)),
                ('content', models.TextField(blank=True)),
                ('meta', models.JSONField(default=dict, blank=True,
                    help_text='Tool-specific metadata (mode, style, sources, etc.)')),
                ('sync_status', models.CharField(max_length=10, default='draft',
                    choices=[('draft','Draft'),('pushed','Pushed'),('synced','Synced')])),
                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('owner', models.ForeignKey(
                    settings.AUTH_USER_MODEL, on_delete=django.db.models.deletion.CASCADE,
                    related_name='nexa_drafts')),
                ('source_workspace', models.ForeignKey(
                    'community.GroupWorkspace', on_delete=django.db.models.deletion.CASCADE,
                    related_name='drafts',
                    limit_choices_to={'workspace_type': 'nexa', 'is_personal': True})),
                ('target_workspace', models.ForeignKey(
                    'community.GroupWorkspace', on_delete=django.db.models.deletion.SET_NULL,
                    null=True, blank=True, related_name='received_drafts')),
            ],
            options={'ordering': ['-updated_at']},
        ),
        migrations.CreateModel(
            name='NexaSyncLog',
            fields=[
                ('id', models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, serialize=False)),
                ('action', models.CharField(max_length=20, default='push',
                    choices=[('push','Push'),('sync','Sync'),('recall','Recall')])),
                ('note', models.CharField(max_length=255, blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('draft', models.ForeignKey(
                    'community.NexaDraft', on_delete=django.db.models.deletion.CASCADE,
                    related_name='sync_logs')),
                ('actor', models.ForeignKey(
                    settings.AUTH_USER_MODEL, on_delete=django.db.models.deletion.CASCADE,
                    related_name='nexa_sync_logs')),
                ('target_workspace', models.ForeignKey(
                    'community.GroupWorkspace', on_delete=django.db.models.deletion.SET_NULL,
                    null=True, blank=True, related_name='sync_logs')),
            ],
            options={'ordering': ['-created_at']},
        ),
    ]
