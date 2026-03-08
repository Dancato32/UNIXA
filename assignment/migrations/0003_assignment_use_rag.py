# Generated migration for adding use_rag field

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('assignment', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='assignment',
            name='use_rag',
            field=models.BooleanField(default=True, help_text='Use study materials as reference (RAG)'),
        ),
    ]
