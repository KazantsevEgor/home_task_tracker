import os
import sys

import django
import pytest
from django.core.management import call_command
from django.test.utils import setup_databases, teardown_databases

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tracker.settings")
django.setup()


@pytest.fixture(scope="session", autouse=True)
def django_database():
    """Тесты работают в отдельной БД, не изменяя пользовательские данные."""
    config = setup_databases(verbosity=0, interactive=False)
    call_command("import_legacy", verbosity=0)
    yield
    teardown_databases(config, verbosity=0)
