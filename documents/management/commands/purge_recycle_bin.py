"""Permanently delete records that have been in the Recycle Bin for 30 days.

    python manage.py purge_recycle_bin

Run automatically by start_all.bat each time the system starts.
"""
from django.core.management.base import BaseCommand

from documents.recycle_bin import purge_expired


class Command(BaseCommand):
    help = "Permanently delete records that have been in the Recycle Bin for the full retention period."

    def handle(self, *args, **options):
        removed = purge_expired()
        self.stdout.write(f"Recycle Bin clean-up: {removed} record(s) deleted permanently.")
