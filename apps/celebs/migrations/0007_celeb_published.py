from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('celebs', '0006_remove_net_worth_from_celeb'),
    ]

    operations = [
        migrations.AddField(
            model_name='celeb',
            name='published',
            field=models.BooleanField(default=True, help_text='Unpublished celebs are hidden from all public listings and detail pages'),
        ),
    ]
