"""Helpers for moving Record Keeper from PostgreSQL to XAMPP (MariaDB).

    python scripts/database/xampp_tools.py createdb        make the docarchive_db database in XAMPP
    python scripts/database/xampp_tools.py count OUT.json  count the rows of every table (current DB_ENGINE)
    python scripts/database/xampp_tools.py compare A B     compare two count files
    python scripts/database/xampp_tools.py use-mysql       write DB_ENGINE=mysql into .env

No password is printed or saved by this script.
"""
import json
import os
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(BASE))
os.chdir(BASE)


def env(name, default=""):
    from dotenv import dotenv_values
    return os.environ.get(name) or dotenv_values(BASE / ".env").get(name) or default


def createdb():
    import pymysql
    name = env("MYSQL_NAME", "docarchive_db")
    try:
        con = pymysql.connect(host=env("MYSQL_HOST", "127.0.0.1"), port=int(env("MYSQL_PORT", "3306")),
                              user=env("MYSQL_USER", "root"), password=env("MYSQL_PASSWORD", ""), charset="utf8mb4")
    except pymysql.err.OperationalError as e:
        code = e.args[0]
        if code == 1045:
            print("[X] XAMPP refused the sign-in for user root. If you gave root a password in XAMPP,")
            print("    add a line MYSQL_PASSWORD=yourpassword to the .env file, then run this again.")
        else:
            print("[X] Could not reach XAMPP's MySQL on port 3306. Start MySQL in the XAMPP Control Panel.")
            print("   ", e)
        sys.exit(1)
    with con.cursor() as cur:
        cur.execute("SELECT VERSION()")
        print("[OK] Connected to XAMPP database server:", cur.fetchone()[0])
        cur.execute(f"CREATE DATABASE IF NOT EXISTS `{name}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
        print(f"[OK] Database '{name}' is ready (utf8mb4).")
    con.close()


def count(out):
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
    import django
    django.setup()
    from django.apps import apps
    from django.db import connection
    skip = {"contenttypes.contenttype", "auth.permission", "sessions.session"}
    counts = {}
    for model in apps.get_models():
        label = model._meta.label_lower
        if label in skip or model._meta.proxy or not model._meta.managed:
            continue
        counts[label] = model._base_manager.count()
    print(f"[OK] Counted {sum(counts.values())} rows in {len(counts)} tables on {connection.vendor} "
          f"({connection.settings_dict['NAME']}).")
    Path(out).write_text(json.dumps(counts, indent=1), encoding="utf-8")


def compare(a, b):
    ca = json.loads(Path(a).read_text(encoding="utf-8"))
    cb = json.loads(Path(b).read_text(encoding="utf-8"))
    bad = 0
    print(f"{'Table':45} {'PostgreSQL':>10} {'XAMPP':>10}")
    for label in sorted(set(ca) | set(cb)):
        x, y = ca.get(label, 0), cb.get(label, 0)
        mark = "" if x == y else "   <-- different"
        bad += x != y
        print(f"{label:45} {x:>10} {y:>10}{mark}")
    print(f"TOTAL{'':40} {sum(ca.values()):>10} {sum(cb.values()):>10}")
    if bad:
        print(f"[X] {bad} table(s) do not match. The .env file was NOT changed; the system still uses PostgreSQL.")
        sys.exit(1)
    print("[OK] Every table matches: all records were copied to XAMPP.")


def use_mysql():
    path = BASE / ".env"
    lines = path.read_text(encoding="utf-8").splitlines() if path.exists() else []
    lines = [ln for ln in lines if not ln.strip().upper().startswith("DB_ENGINE=")]
    lines.append("DB_ENGINE=mysql")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("[OK] .env now says DB_ENGINE=mysql, so Record Keeper uses XAMPP from now on.")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd == "createdb":
        createdb()
    elif cmd == "count":
        count(sys.argv[2])
    elif cmd == "compare":
        compare(sys.argv[2], sys.argv[3])
    elif cmd == "use-mysql":
        use_mysql()
    else:
        print(__doc__)
