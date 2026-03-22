from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('community', '0023_nexa_workspace_links'),
    ]

    operations = [
        migrations.AddField(
            model_name='communityprofile',
            name='interests',
            field=models.CharField(
                blank=True,
                help_text='Comma-separated interest tags',
                max_length=500,
            ),
        ),
    ]
