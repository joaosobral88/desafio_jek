"""Servidor dos testes de navegador: usa SQLite temporário, nunca db.sqlite3."""
import os
from pathlib import Path
import sys
from tempfile import TemporaryDirectory

import django
from django.conf import settings
from django.core.management import call_command

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "backend"))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

with TemporaryDirectory(prefix="live-pulse-test-") as directory:
    settings.DATABASES["default"]["NAME"] = str(Path(directory) / "test.sqlite3")
    django.setup()
    call_command("migrate", verbosity=0)
    call_command("runserver", "127.0.0.1:8001", use_reloader=False)
