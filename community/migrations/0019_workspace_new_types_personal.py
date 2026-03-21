from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('community', '0018_add_meeting_record'),
    ]

    operations = [
        # Extend workspace_type choices (no DB change needed — CharField stores raw value)
        # Extend privacy choices (no DB change needed)
        # Add is_personal flag
        migrations.AddField(
            model_name='groupworkspace',
            name='is_personal',
            field=models.BooleanField(default=False, db_index=True),
        ),
    ]
