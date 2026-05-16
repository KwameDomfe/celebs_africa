from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('celebs', '0007_celeb_published'),
    ]

    operations = [
        migrations.CreateModel(
            name='CelebSocialLink',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('platform', models.CharField(choices=[
                    ('website', 'Website'), ('instagram', 'Instagram'),
                    ('twitter', 'Twitter / X'), ('facebook', 'Facebook'),
                    ('tiktok', 'TikTok'), ('youtube', 'YouTube'),
                    ('snapchat', 'Snapchat'), ('threads', 'Threads'),
                    ('linkedin', 'LinkedIn'), ('spotify', 'Spotify'),
                    ('soundcloud', 'SoundCloud'), ('apple_music', 'Apple Music'),
                    ('deezer', 'Deezer'), ('audiomack', 'Audiomack'),
                    ('boomplay', 'Boomplay'), ('telegram', 'Telegram'),
                    ('whatsapp', 'WhatsApp'), ('twitch', 'Twitch'),
                    ('vimeo', 'Vimeo'), ('pinterest', 'Pinterest'),
                    ('other', 'Other'),
                ], max_length=20)),
                ('url', models.URLField(max_length=500)),
                ('order', models.PositiveSmallIntegerField(default=0)),
                ('celeb', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='social_links',
                    to='celebs.celeb',
                )),
            ],
            options={'ordering': ['order', 'platform']},
        ),
    ]
