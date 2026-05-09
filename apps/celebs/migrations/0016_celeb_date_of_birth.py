from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('celebs', '0015_country_celeb_nationality'),
    ]

    operations = [
        migrations.AddField(
            model_name='celeb',
            name='date_of_birth',
            field=models.DateField(blank=True, null=True),
        ),
    ]
