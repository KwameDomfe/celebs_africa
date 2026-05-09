"""
Management command to upload all local media files to DigitalOcean Spaces,
preserving the exact path structure so existing database records continue to work.

Usage:
    python manage.py upload_media_to_spaces
    python manage.py upload_media_to_spaces --dry-run
"""
import os
import boto3
from pathlib import Path
from django.conf import settings
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Upload local media files to DigitalOcean Spaces'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='List files that would be uploaded without actually uploading',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']

        # Validate Spaces config
        access_key = os.environ.get('SPACES_ACCESS_KEY')
        secret_key = os.environ.get('SPACES_SECRET_KEY')
        bucket_name = os.environ.get('SPACES_BUCKET_NAME', '')
        endpoint_url = os.environ.get('SPACES_ENDPOINT_URL', '')

        if not all([access_key, secret_key, bucket_name, endpoint_url]):
            self.stderr.write(self.style.ERROR(
                'Missing Spaces environment variables. Set SPACES_ACCESS_KEY, '
                'SPACES_SECRET_KEY, SPACES_BUCKET_NAME, SPACES_ENDPOINT_URL.'
            ))
            return

        media_root = Path(settings.MEDIA_ROOT)
        if not media_root.exists():
            self.stderr.write(self.style.ERROR(f'MEDIA_ROOT does not exist: {media_root}'))
            return

        # Collect all files under MEDIA_ROOT
        all_files = [f for f in media_root.rglob('*') if f.is_file()]
        if not all_files:
            self.stdout.write('No files found in MEDIA_ROOT.')
            return

        self.stdout.write(f'Found {len(all_files)} file(s) in {media_root}')

        if dry_run:
            self.stdout.write(self.style.WARNING('--- DRY RUN (no files will be uploaded) ---'))
            for f in all_files:
                relative = f.relative_to(media_root)
                self.stdout.write(f'  Would upload: {relative}')
            return

        s3 = boto3.client(
            's3',
            endpoint_url=endpoint_url,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
        )

        uploaded = 0
        skipped = 0
        errors = 0

        for local_path in all_files:
            # Preserve the path relative to MEDIA_ROOT as the Spaces object key
            relative = local_path.relative_to(media_root)
            object_key = str(relative).replace('\\', '/')

            # Check if already exists in Spaces
            try:
                s3.head_object(Bucket=bucket_name, Key=object_key)
                self.stdout.write(f'  Skipped (exists): {object_key}')
                skipped += 1
                continue
            except s3.exceptions.ClientError:
                pass  # Does not exist, proceed with upload

            try:
                s3.upload_file(
                    str(local_path),
                    bucket_name,
                    object_key,
                    ExtraArgs={'ACL': 'public-read'},
                )
                self.stdout.write(self.style.SUCCESS(f'  Uploaded: {object_key}'))
                uploaded += 1
            except Exception as e:
                self.stderr.write(self.style.ERROR(f'  ERROR uploading {object_key}: {e}'))
                errors += 1

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS(
            f'Done. Uploaded: {uploaded}, Skipped: {skipped}, Errors: {errors}'
        ))
