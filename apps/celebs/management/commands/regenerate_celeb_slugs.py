import re

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils.text import slugify

from apps.celebs.models import Celeb


class Command(BaseCommand):
    help = (
        'One-time slug cleanup: replace old counter-heavy celeb slugs '
        '(e.g. name-7) with more readable slugs based on current rules.'
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--apply',
            action='store_true',
            help='Persist changes. Without this flag, the command runs in dry-run mode.',
        )
        parser.add_argument(
            '--limit',
            type=int,
            default=0,
            help='Optional max number of records to process (0 = no limit).',
        )

    def handle(self, *args, **options):
        apply_changes = options['apply']
        limit = options['limit']

        candidates = []
        qs = Celeb.objects.all().order_by('pk')
        if limit and limit > 0:
            qs = qs[:limit]

        for celeb in qs.iterator():
            current_slug = (celeb.slug or '').strip()
            if not current_slug:
                continue

            name_slug = slugify(celeb.name or '')
            if not name_slug:
                continue

            # Target only slugs from the old pattern: <name>-<counter>
            if not re.fullmatch(rf'{re.escape(name_slug)}-\d+', current_slug):
                continue

            new_slug = celeb._build_unique_slug()
            if new_slug == current_slug:
                continue

            candidates.append((celeb, current_slug, new_slug))

        if not candidates:
            self.stdout.write(self.style.SUCCESS('No counter-heavy celeb slugs needed updates.'))
            return

        self.stdout.write(f'Found {len(candidates)} counter-heavy slug(s) that can be improved.')
        preview = candidates[:25]
        for celeb, old, new in preview:
            self.stdout.write(f' - pk={celeb.pk}: {old} -> {new}')
        if len(candidates) > len(preview):
            self.stdout.write(f' ... and {len(candidates) - len(preview)} more')

        if not apply_changes:
            self.stdout.write(self.style.WARNING('Dry run only. Re-run with --apply to save changes.'))
            return

        updated = 0
        with transaction.atomic():
            for celeb, old, new in candidates:
                celeb.slug = new
                celeb.save(update_fields=['slug'])
                updated += 1

        self.stdout.write(self.style.SUCCESS(f'Updated {updated} celeb slug(s).'))
