from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='UserAIProfile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('skills', models.TextField(blank=True)),
                ('interests', models.TextField(blank=True)),
                ('courses', models.TextField(blank=True)),
                ('goals', models.TextField(blank=True)),
                ('availability', models.CharField(blank=True, max_length=50)),
                ('looking_for', models.CharField(blank=True, max_length=100)),
                ('startup_interest', models.BooleanField(default=False)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='ai_profile', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='StartupTeam',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=255)),
                ('idea', models.TextField()),
                ('industry', models.CharField(blank=True, max_length=100)),
                ('stage', models.CharField(blank=True, max_length=50)),
                ('status', models.CharField(choices=[('forming', 'Forming'), ('active', 'Active'), ('closed', 'Closed')], default='forming', max_length=10)),
                ('required_roles', models.TextField(blank=True)),
                ('team_size', models.PositiveSmallIntegerField(default=4)),
                ('remote', models.BooleanField(default=True)),
                ('ai_intro', models.TextField(blank=True)),
                ('workspace_id', models.UUIDField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('founder', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='founded_startups', to=settings.AUTH_USER_MODEL)),
            ],
            options={'ordering': ['-created_at']},
        ),
        migrations.CreateModel(
            name='StartupTeamMember',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('role', models.CharField(blank=True, max_length=100)),
                ('status', models.CharField(choices=[('invited', 'Invited'), ('accepted', 'Accepted'), ('declined', 'Declined')], default='invited', max_length=10)),
                ('ai_reason', models.TextField(blank=True)),
                ('joined_at', models.DateTimeField(auto_now_add=True)),
                ('team', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='members', to='ai_community.startupteam')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='startup_memberships', to=settings.AUTH_USER_MODEL)),
            ],
            options={'unique_together': {('team', 'user')}},
        ),
        migrations.CreateModel(
            name='AIMatch',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('match_type', models.CharField(choices=[('study', 'Study Partner'), ('project', 'Project Collaborator'), ('startup', 'Startup Teammate'), ('general', 'General Connection')], default='general', max_length=20)),
                ('score', models.FloatField(default=0.0)),
                ('reason', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('matched_user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='matched_by', to=settings.AUTH_USER_MODEL)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='ai_matches', to=settings.AUTH_USER_MODEL)),
            ],
            options={'ordering': ['-score'], 'unique_together': {('user', 'matched_user', 'match_type')}},
        ),
        migrations.CreateModel(
            name='AIOpportunity',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('title', models.CharField(max_length=300)),
                ('description', models.TextField()),
                ('opp_type', models.CharField(choices=[('internship', 'Internship'), ('scholarship', 'Scholarship'), ('job', 'Job'), ('competition', 'Competition'), ('research', 'Research'), ('grant', 'Grant'), ('other', 'Other')], default='other', max_length=20)),
                ('source_post_id', models.UUIDField(blank=True, null=True)),
                ('deadline', models.DateField(blank=True, null=True)),
                ('url', models.URLField(blank=True)),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={'ordering': ['-created_at']},
        ),
        migrations.CreateModel(
            name='ExpertBadge',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('label', models.CharField(max_length=100)),
                ('subject', models.CharField(blank=True, max_length=100)),
                ('score', models.FloatField(default=0.0)),
                ('awarded_at', models.DateTimeField(auto_now_add=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='expert_badges', to=settings.AUTH_USER_MODEL)),
            ],
            options={'ordering': ['-score']},
        ),
    ]
