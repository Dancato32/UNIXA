from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('community', '0022_add_reply_to_workspace_message'),
    ]

    operations = [
        migrations.CreateModel(
            name='NexaWorkspaceLink',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('linked_at', models.DateTimeField(auto_now_add=True)),
                ('nexa_workspace', models.ForeignKey(
                    limit_choices_to={'is_personal': True, 'workspace_type': 'nexa'},
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='linked_group_workspaces',
                    to='community.groupworkspace',
                )),
                ('linked_workspace', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='nexa_links',
                    to='community.groupworkspace',
                )),
            ],
            options={
                'ordering': ['-linked_at'],
                'unique_together': {('nexa_workspace', 'linked_workspace')},
            },
        ),
    ]
