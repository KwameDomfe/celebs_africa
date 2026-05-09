import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


def rename_tables(apps, schema_editor):
    """
    Handles both old databases (tables named stars_*) and fresh databases
    (tables already named celebs_* because the app was always called celebs).
    """
    with schema_editor.connection.cursor() as cursor:
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = {row[0] for row in cursor.fetchall()}

        if 'stars_star' in tables:
            cursor.execute('ALTER TABLE stars_star RENAME TO celebs_celeb')
        elif 'celebs_star' in tables:
            cursor.execute('ALTER TABLE celebs_star RENAME TO celebs_celeb')

        if 'stars_like' in tables:
            cursor.execute('ALTER TABLE stars_like RENAME TO celebs_like')

        if 'stars_comment' in tables:
            cursor.execute('ALTER TABLE stars_comment RENAME TO celebs_comment')

        if 'celebs_like' in tables or 'stars_like' in tables:
            cursor.execute('ALTER TABLE celebs_like RENAME COLUMN star_id TO celeb_id')

        if 'celebs_comment' in tables or 'stars_comment' in tables:
            cursor.execute('ALTER TABLE celebs_comment RENAME COLUMN star_id TO celeb_id')


class Migration(migrations.Migration):

    dependencies = [
        ('celebs', '0006_star_slug'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunPython(rename_tables, migrations.RunPython.noop),
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
