"""Takes a screenshot of every page of Record Keeper, per role, for the printed guide.

Run with scripts\\screenshots\\capture_screens.bat while the server is running
(run_in_chrome.bat or start_all.bat). Each role is signed in through Django
itself, so no password is typed. Pictures go to scripts\\screenshots\\out.
"""
import json
import os
import sys
import time
import traceback
from pathlib import Path

BASE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(BASE))
os.chdir(BASE)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
# Playwright runs its own event loop; the pages are read in a separate server process.
os.environ.setdefault("DJANGO_ALLOW_ASYNC_UNSAFE", "true")

import django  # noqa: E402

django.setup()

from django.test import Client  # noqa: E402
from django.urls import reverse  # noqa: E402
from playwright.sync_api import sync_playwright  # noqa: E402

from accounts.models import Office, User  # noqa: E402
from documents.models import Document  # noqa: E402

SITE = "http://127.0.0.1:8000"
OUT = Path(__file__).resolve().parent / "out"
OUT.mkdir(exist_ok=True)
for old in OUT.glob("*.png"):
    old.unlink()
log = open(OUT / "capture_log.txt", "w", encoding="utf-8")


def say(*parts):
    line = " ".join(str(p) for p in parts)
    print(line)
    log.write(line + "\n")
    log.flush()


def pick(role):
    return (User.objects.filter(role=role, is_active=True, approval_status=User.Approval.APPROVED)
            .order_by("id").first())


superadmin, admin, staff = pick(User.Role.SUPERADMIN), pick(User.Role.ADMIN), pick(User.Role.USER)
say("super:", superadmin, "| admin:", admin, "| staff:", staff)

live = Document.objects.filter(is_deleted=False)
doc_any = live.exclude(file="").order_by("-created_at").first() or live.order_by("-created_at").first()
doc_public = (live.filter(classification=Document.Classification.PUBLIC).exclude(file="")
              .order_by("-created_at").first()) or live.filter(
              classification=Document.Classification.PUBLIC).first()
say("record for admin:", doc_any, "| public record for staff:", doc_public)
office = Office.objects.order_by("id").first()

# A sample request so the Account requests page has something to show; removed at the end.
sample = User.objects.create_user(
    "sample_request", email="sample.request@example.com", password=None, is_active=False,
    first_name="Juan", last_name="Dela Cruz (sample)", approval_status=User.Approval.PENDING,
    requested_role=User.Role.USER, position="Administrative Aide", office=office,
)

manifest = []
counter = [0]


def session_for(user):
    client = Client()
    client.force_login(user)
    return client.cookies["sessionid"].value


def shoot(page, role, title, url, note="", before=None, full=True, wait=1.0):
    counter[0] += 1
    name = f"{counter[0]:02d}_{role}.png"
    try:
        page.goto(SITE + url, wait_until="networkidle", timeout=60000)
        if before:
            before(page)
        time.sleep(wait)
        page.screenshot(path=str(OUT / name), full_page=full)
        manifest.append({"file": name, "role": role, "title": title, "note": note, "url": url})
        say("ok  ", name, title, url)
    except Exception as e:  # keep going; the log says what failed
        say("FAIL", name, title, url, repr(e)[:300])


def open_more_filters(page):
    toggle = page.get_by_text("More filters").first
    if toggle.count():
        toggle.click()


def open_user_menu(page):
    page.locator(".user-menu-btn").first.click()


def open_bell(page):
    page.locator("#notif-bell").first.click()


# Sign each role in before the browser starts (the database is not used after this).
SESSIONS = {u.pk: session_for(u) for u in (superadmin, admin, staff) if u}

try:
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="chrome", headless=True)

        def context(user=None):
            ctx = browser.new_context(viewport={"width": 1366, "height": 768})
            # Keep the left menu open, as it is after clicking the menu button.
            ctx.add_init_script("try{sessionStorage.setItem('sidebar','open')}catch(e){}")
            if user:
                ctx.add_cookies([{"name": "sessionid", "value": SESSIONS[user.pk],
                                  "domain": "127.0.0.1", "path": "/"}])
            return ctx

        # ---------------- Sign-in pages (no account needed)
        ctx = context()
        page = ctx.new_page()
        shoot(page, "public", "Sign-in page", reverse("accounts:login"), full=False)
        shoot(page, "public", "Request an account (sign-up)", reverse("accounts:signup"))
        shoot(page, "public", "Forgot password", reverse("accounts:password_reset"), full=False)
        ctx.close()

        # ---------------- Super administrator
        if superadmin:
            ctx = context(superadmin)
            page = ctx.new_page()
            r = "super"
            shoot(page, r, "Overview", reverse("documents:dashboard"))
            shoot(page, r, "Account requests", reverse("accounts:account_requests"))
            shoot(page, r, "Accounts list", reverse("accounts:user_list"))
            shoot(page, r, "Add an account", reverse("accounts:user_create"))
            target = staff or admin
            if target:
                shoot(page, r, "Edit an account", reverse("accounts:user_update", args=[target.pk]))
                shoot(page, r, "Reset a user's password", reverse("accounts:user_password", args=[target.pk]))
                shoot(page, r, "Send a message to a user", reverse("accounts:user_message", args=[target.pk]))
            shoot(page, r, "Audit trail", reverse("documents:audit_trail"))
            shoot(page, r, "Search records", reverse("documents:document_list"))
            if doc_any:
                shoot(page, r, "Record page", doc_any.get_absolute_url())
            shoot(page, r, "Offices", reverse("accounts:office_list"))
            shoot(page, r, "Notifications", reverse("accounts:notification_list"))
            shoot(page, r, "Notification bell", reverse("documents:dashboard"), before=open_bell, full=False)
            shoot(page, r, "My profile", reverse("accounts:profile"))
            shoot(page, r, "Change my password", reverse("accounts:password_change"))
            shoot(page, r, "Account menu and sign out", reverse("documents:dashboard"),
                  before=open_user_menu, full=False)
            ctx.close()

        # ---------------- Administrator
        if admin:
            ctx = context(admin)
            page = ctx.new_page()
            r = "admin"
            shoot(page, r, "Overview", reverse("documents:dashboard"))
            shoot(page, r, "File a document", reverse("documents:document_create"))
            if doc_any:
                folder = reverse("documents:document_folder", args=[doc_any.doc_type])
                shoot(page, r, "Open a folder (sub-folders by series year)", folder)
                shoot(page, r, "Records inside a year sub-folder", f"{folder}?year={doc_any.series_year}")
                shoot(page, r, "Record page", doc_any.get_absolute_url())
                if doc_any.file:
                    shoot(page, r, "View the scanned copy", reverse("documents:document_viewer", args=[doc_any.pk]),
                          full=False, wait=4)
                shoot(page, r, "Edit a record", reverse("documents:document_update", args=[doc_any.pk]))
                shoot(page, r, "Remove a record (move to Recycle Bin)",
                      reverse("documents:document_delete", args=[doc_any.pk]), full=False)
            shoot(page, r, "Search records", reverse("documents:document_list"))
            shoot(page, r, "Search with more filters", reverse("documents:document_list"), before=open_more_filters)
            shoot(page, r, "Folders", reverse("documents:folder_list"))
            shoot(page, r, "Add a folder", reverse("documents:folder_create"))
            shoot(page, r, "Recycle Bin", reverse("documents:recycle_bin"))
            shoot(page, r, "Accounts list (view only)", reverse("accounts:user_list"))
            shoot(page, r, "Offices", reverse("accounts:office_list"))
            shoot(page, r, "Add an office", reverse("accounts:office_create"))
            if office:
                shoot(page, r, "Send a notice to an office", reverse("accounts:office_notify", args=[office.pk]))
            shoot(page, r, "Notifications", reverse("accounts:notification_list"))
            shoot(page, r, "My profile", reverse("accounts:profile"))
            shoot(page, r, "Change my password", reverse("accounts:password_change"))
            ctx.close()

        # ---------------- Staff user
        if staff:
            ctx = context(staff)
            page = ctx.new_page()
            r = "staff"
            shoot(page, r, "Overview", reverse("documents:dashboard"))
            shoot(page, r, "Search records", reverse("documents:document_list"))
            if doc_public:
                shoot(page, r, "Record page (read only)", doc_public.get_absolute_url())
                if doc_public.file:
                    shoot(page, r, "View the scanned copy",
                          reverse("documents:document_viewer", args=[doc_public.pk]), full=False, wait=4)
            shoot(page, r, "Notifications", reverse("accounts:notification_list"))
            shoot(page, r, "My profile", reverse("accounts:profile"))
            shoot(page, r, "Change my password", reverse("accounts:password_change"))
            shoot(page, r, "Pages outside the role are refused", reverse("documents:document_create"), full=False)
            ctx.close()

        browser.close()
except Exception:
    say("ERROR", traceback.format_exc())
finally:
    sample.delete()
    (OUT / "manifest.json").write_text(json.dumps(manifest, indent=1), encoding="utf-8")
    say("DONE", len(manifest), "screenshots")
    log.close()
