"""Saves the downloaded (certified true copy) PDF of a record, for the printed guide."""
import os
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(BASE))
os.chdir(BASE)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
import django  # noqa: E402

django.setup()
from django.conf import settings  # noqa: E402
from django.test import Client  # noqa: E402
from django.urls import reverse  # noqa: E402

from accounts.models import User  # noqa: E402
from documents.models import Document  # noqa: E402

settings.ALLOWED_HOSTS = list(settings.ALLOWED_HOSTS) + ["testserver"]
OUT = Path(__file__).resolve().parent / "out"
OUT.mkdir(exist_ok=True)
log = open(OUT / "ctc_log.txt", "w", encoding="utf-8")
admin = User.objects.filter(role=User.Role.ADMIN, is_active=True).order_by("id").first()
c = Client()
c.force_login(admin)
for doc in Document.objects.filter(is_deleted=False).exclude(file="").order_by("-created_at")[:3]:
    r = c.get(reverse("documents:document_download", args=[doc.pk]))
    body = b"".join(r.streaming_content) if getattr(r, "streaming", False) else r.content
    name = f"ctc_{doc.pk}.pdf" if body[:4] == b"%PDF" else f"ctc_{doc.pk}.bin"
    (OUT / name).write_bytes(body)
    log.write(f"{doc.pk} {doc} {r.status_code} {r.get('Content-Disposition')} {len(body)} -> {name}\n")
log.write("DONE\n")
log.close()
