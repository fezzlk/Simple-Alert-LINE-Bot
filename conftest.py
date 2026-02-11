import pytest
import google.auth
from google.auth.exceptions import DefaultCredentialsError


def _has_adc() -> bool:
    try:
        google.auth.default()
        return True
    except DefaultCredentialsError:
        return False


def pytest_collection_modifyitems(config, items):
    if _has_adc():
        return

    skip = pytest.mark.skip(
        reason="Skipping Firestore integration tests: Application Default Credentials not configured."
    )
    for item in items:
        path = str(item.fspath)
        if (
            "src/Infrastructure/Repositories/tests" in path
            or "src/UseCases/Web/tests" in path
            or "src/services/tests" in path
            or path.endswith("src/tests/test_db_connect.py")
        ):
            item.add_marker(skip)
