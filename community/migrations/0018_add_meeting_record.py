from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('community', '0017_add_task_submission_fields'),
    ]

    operations = [
        migrations.CreateModel(
            name='MeetingRecord',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('started_at', models.DateTimeField()),
                ('ended_at', models.DateTimeField(blank=True, null=True)),
                ('participants', models.JSONField(default=list)),
                ('chat_log', models.JSONField(default=list)),
                ('ai_summary', models.TextField(blank=True)),
                ('decisions', models.JSONField(default=list)),
                ('action_items', models.JSONField(default=list)),
                ('key_topics', models.JSONField(default=list)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('workspace', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='meeting_records',
                    to='community.groupworkspace',
                )),
            ],
            options={
                'verbose_name': 'Meeting Record',
                'ordering': ['-started_at'],
            },
        ),
    ]
