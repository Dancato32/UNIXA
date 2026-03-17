from django.db import migrations, models

class Migration(migrations.Migration):
    initial = True
    dependencies = []
    operations = [
        migrations.CreateModel(
            name='Resource',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('subject', models.CharField(choices=[
                    ('mathematics','Mathematics'),('physics','Physics'),('chemistry','Chemistry'),
                    ('biology','Biology'),('economics','Economics'),('world_history','World History'),
                    ('literature','Literature'),('art_design','Art & Design'),('music_theory','Music Theory'),
                    ('languages','Languages'),('programming','Programming'),('geography','Geography'),
                ], max_length=50)),
                ('topic', models.CharField(max_length=255)),
                ('title', models.CharField(max_length=255)),
                ('content', models.TextField()),
                ('source', models.CharField(blank=True, default='Nexa Library', max_length=255)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={'ordering': ['subject', 'topic', 'title']},
        ),
    ]
