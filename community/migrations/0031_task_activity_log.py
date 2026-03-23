import uuid
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('community', '0030_mynexa_system'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='TaskActivityLog',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('entry_type', models.CharField(
                    choices=[
                        ('ai', 'AI Response'), ('search', 'Search Query'),
                        ('note', 'Note'), ('tool', 'Tool Used'), ('status', 'Status Change'),
                    ],
                    default='note', max_length=10,
                )),
                ('content', models.TextField(blank=True)),
                ('meta', models.JSONField(blank=True, default=dict)),
                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('task', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='activity_logs',
                    to='community.workspacetask',
                )),
                ('user', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='task_activity_logs',
                    to=settings.AUTH_USER_MODEL,
                )),
            ],
            options={'ordering': ['created_at']},
        ),
    ]
