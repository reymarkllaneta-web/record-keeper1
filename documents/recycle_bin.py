"""Automatic clean-up of the Recycle Bin.

A removed record stays in the Recycle Bin for RECYCLE_BIN_RETENTION_DAYS (30 by
default). After that it is deleted permanently, together with its scanned file,
unless an administrator restored it or the super administrator rejected the
deletion first. The super administrator can also approve a deletion earlier.

The clean-up runs whenever the Recycle Bin is opened and each time the system
starts (start_all.bat runs `manage.py purge_recycle_bin`).
"""
import logging
from datetime import timedelta

from django.conf import settings
from django.utils import timezone

from .models import AccessLog, Document, Notification

logger = logging.getLogger(__name__)


def purge_expired():
    """Permanently delete every record that has been in the bin for the full retention period."""
    days = settings.RECYCLE_BIN_RETENTION_DAYS
    cutoff = timezone.now() - timedelta(days=days)
    removed = 0
    for document in Document.objects.filter(is_deleted=True, deleted_at__lte=cutoff).select_related("created_by"):
        summary = (f"Automatically deleted {document.control_number} — {document.subject} "
                   f"after {document.days_in_bin} days in the Recycle Bin")
        AccessLog.objects.create(user=None, action=AccessLog.Action.DELETE, note=summary[:255],
                                 user_agent="Record Keeper (automatic clean-up)")
        if document.created_by:
            Notification.notify(
                recipients=[document.created_by], actor=None,
                verb=(f"{document.control_number} — {document.subject} was deleted permanently "
                      f"after {days} days in the Recycle Bin"),
            )
        if document.file:
            try:
                document.file.delete(save=False)
            except Exception:
                logger.warning("Could not remove the stored file for %s", document.control_number)
        document.delete()
        removed += 1
    return removed
