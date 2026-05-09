import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('celebs', '0006_star_slug'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunSQL('ALTER TABLE stars_star RENAME TO celebs_celeb'),
                migrations.RunSQL('ALTER TABLE stars_like RENAME TO celebs_like'),
                migrations.RunSQL('ALTER TABLE stars_comment RENAME TO celebs_comment'),
                migrations.RunSQL('ALTER TABLE celebs_like RENAME COLUMN star_id TO celeb_id'),
                migrations.RunSQL('ALTER TABLE celebs_comment RENAME COLUMN star_id TO celeb_id'),
            ],
            state_operations=[
                migrations.RenameModel('Star', 'Celeb'),
                migrations.RenameField(model_name='like', old_name='star', new_name='celeb'),
                migrations.RenameField(model_name='comment', old_name='star', new_name='celeb'),
                migrations.AlterUniqueTogether(
                    name='like',
                    unique_together={('celeb', 'user')},
                ),
                migrations.AlterField(
                    model_name='like',
                    name='user',
                    field=models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='celeb_likes',
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                migrations.AlterField(
                    model_name='comment',
                    name='user',
                    field=models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='celeb_comments',
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
        ),
    ]
