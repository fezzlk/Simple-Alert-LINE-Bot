import os
import urllib.error
import urllib.request

import pytest
import google.auth
from google.auth.exceptions import DefaultCredentialsError


def _has_adc() -> bool:
    try:
        google.auth.default()
        return True
    except DefaultCredentialsError:
        return False


def _emulator_host() -> str:
    return (os.getenv("FIRESTORE_EMULATOR_HOST") or "").strip()


def _has_emulator() -> bool:
    return _emulator_host() != ""


def _clear_emulator() -> None:
    host = _emulator_host()
    if not host:
        return
    project_id = os.getenv("FIRESTORE_PROJECT_ID") or "simple-alert-line-bot"
    url = (
        f"http://{host}/emulator/v1/projects/{project_id}/databases/(default)/documents"
    )
    req = urllib.request.Request(url, method="DELETE")
    with urllib.request.urlopen(req) as resp:
        if resp.status not in (200, 204):
            raise RuntimeError(f"Failed to clear Firestore emulator data: {resp.status}")


@pytest.fixture(autouse=True)
def _clear_firestore_emulator_between_tests():
    if not _has_emulator():
        yield
        return
    _clear_emulator()
    yield
    _clear_emulator()


def pytest_collection_modifyitems(config, items):
    if _has_emulator() or _has_adc():
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
