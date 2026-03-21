from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('community', '0019_workspace_new_types_personal'),
    ]

    operations = [
        migrations.AlterField(
            model_name='groupworkspace',
            name='workspace_type',
            field=models.CharField(
                choices=[
                    ('startup', 'Startup'),
                    ('study_group', 'Study Group'),
                    ('group_project', 'Group Project'),
                    ('general', 'General Collaboration'),
                    ('ai_tutor', 'AI Tutor Workspace'),
                    ('assignment', 'Assignment Solver'),
                    ('exam_prep', 'Exam Prep'),
                    ('research', 'Research'),
                    ('nexa', 'Nexa Workspace'),
                ],
                default='general',
                max_length=20,
            ),
        ),
    ]
