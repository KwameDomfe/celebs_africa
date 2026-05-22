from django.contrib.auth.backends import ModelBackend


class CelebManagerBackend(ModelBackend):
    """
    Extends Django's ModelBackend with object-level permissions for Celeb pages.

    Rules:
      - Staff users pass every celebs.* permission check automatically.
      - Users in the 'Celeb' or 'Manager' group who are also listed in
        celeb.managers get object-level change/delete rights on that celeb.
      - add_celeb is a model-level permission assigned to the Celeb and
        Manager groups via the data migration, so ModelBackend handles it.
    """

    _CELEB_OBJ_PERMS = frozenset({'celebs.change_celeb', 'celebs.delete_celeb'})

    def has_perm(self, user_obj, perm, obj=None):
        if not user_obj.is_active or user_obj.is_anonymous:
            return False

        # Staff get all celeb-related permissions (matches existing app behaviour).
        if user_obj.is_staff and perm.startswith('celebs.'):
            return True

        # Object-level: users in the celeb's managers list can change/delete it.
        if obj is not None and perm in self._CELEB_OBJ_PERMS:
            return obj.managers.filter(pk=user_obj.pk).exists()

        # Fall through to ModelBackend for everything else (group/user perms).
        return super().has_perm(user_obj, perm)
