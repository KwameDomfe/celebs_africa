from django.db import migrations


def create_celeb_groups(apps, schema_editor):
    Group = apps.get_model('auth', 'Group')
    Permission = apps.get_model('auth', 'Permission')

    celeb_group, _ = Group.objects.get_or_create(name='Celeb')
    manager_group, _ = Group.objects.get_or_create(name='Manager')

    perms = Permission.objects.filter(
        content_type__app_label='celebs',
        content_type__model='celeb',
        codename__in=['add_celeb', 'change_celeb', 'delete_celeb', 'view_celeb'],
    )
    celeb_group.permissions.set(perms)
    manager_group.permissions.set(perms)


def delete_celeb_groups(apps, schema_editor):
    Group = apps.get_model('auth', 'Group')
    Group.objects.filter(name__in=['Celeb', 'Manager']).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0003_userprofile_role'),
        ('celebs', '0009_celeb_managers'),
        ('contenttypes', '0002_remove_content_type_name'),
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.RunPython(create_celeb_groups, reverse_code=delete_celeb_groups),
    ]
