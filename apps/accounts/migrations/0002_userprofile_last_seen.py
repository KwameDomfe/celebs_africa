from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='last_seen',
            field=models.DateTimeField(blank=True, db_index=True, null=True),
        ),
    ]
