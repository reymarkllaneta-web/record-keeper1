"""Like test_settings, but runs the tests on a throwaway database in XAMPP (MariaDB).

Django creates test_docarchive_db, runs every test in it, then deletes it.
The real docarchive_db database, Cloudinary and email are never touched.
"""
import os

os.environ["DB_ENGINE"] = "mysql"

from test_settings import *  # noqa: E402,F401,F403
from config.settings import DATABASES as _REAL  # noqa: E402

DATABASES = {"default": dict(_REAL["default"])}
