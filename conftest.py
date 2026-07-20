import os
import urllib.error
import urllib.request

import pytest


def _integration_tests_enabled() -> bool:
    return os.getenv("RUN_FIRESTORE_INTEGRATION_TESTS") == "1"


def _configure_firestore_test_project() -> None:
    if not _integration_tests_enabled():
        return

    test_project_id = (os.getenv("FIRESTORE_TEST_PROJECT_ID") or "").strip()
    production_project_id = (
        os.getenv("FIRESTORE_PRODUCTION_PROJECT_ID") or "simple-alert-line-bot"
    ).strip()
    if not test_project_id:
        raise pytest.UsageError(
            "FIRESTORE_TEST_PROJECT_ID is required when "
            "RUN_FIRESTORE_INTEGRATION_TESTS=1."
        )
    if test_project_id == production_project_id:
        raise pytest.UsageError(
            "Firestore integration tests must not use the production project."
        )

    os.environ["FIRESTORE_PROJECT_ID"] = test_project_id


_configure_firestore_test_project()


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
    if _integration_tests_enabled():
        return

    skip = pytest.mark.skip(
        reason=(
            "Skipping Firestore integration tests: set "
            "RUN_FIRESTORE_INTEGRATION_TESTS=1 and FIRESTORE_TEST_PROJECT_ID "
            "to run against a dedicated non-production project."
        )
    )
    for item in items:
        path = str(item.fspath)
        if (
            "src/Infrastructure/Repositories/tests" in path
            or "src/UseCases/Web/tests" in path
            or (
                "src/services/tests" in path
                and "test_line_intent_parser_service" not in path
            )
            or path.endswith("src/tests/test_db_connect.py")
        ):
            item.add_marker(skip)
