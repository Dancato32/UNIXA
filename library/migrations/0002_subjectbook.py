from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('library', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='SubjectBook',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('subject', models.CharField(choices=[
                    ('mathematics', 'Mathematics'), ('physics', 'Physics'),
                    ('chemistry', 'Chemistry'), ('biology', 'Biology'),
                    ('economics', 'Economics'), ('world_history', 'World History'),
                    ('english', 'English Language'), ('literature', 'Literature'),
                    ('art_design', 'Art & Design'), ('music_theory', 'Music Theory'),
                    ('programming', 'Programming'), ('geography', 'Geography'),
                ], max_length=50)),
                ('title', models.CharField(max_length=255)),
                ('author', models.CharField(blank=True, default='', max_length=255)),
                ('file', models.FileField(upload_to='library/books/')),
                ('uploaded_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={'ordering': ['subject', 'title']},
        ),
    ]
