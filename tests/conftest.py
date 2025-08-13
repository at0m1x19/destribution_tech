import contextlib
from typing import Generator
from uuid import uuid4

import pytest

from src.http_client import HttpClient
from src.api.gists import GistsAPI
from src.utils.env import load_settings


@pytest.fixture(scope="session")
def settings():
    return load_settings()


@pytest.fixture(scope="session")
def http_client(settings) -> HttpClient:
    headers = {}
    if settings.token:
        headers["Authorization"] = f"Bearer {settings.token}"
    return HttpClient(base_url=settings.base_url, default_headers=headers)


@pytest.fixture(scope="session")
def gists_api(http_client, settings) -> GistsAPI:
    return GistsAPI(http_client, api_version=settings.api_version)


@pytest.fixture()
def temp_gist(gists_api: GistsAPI) -> Generator[dict, None, None]:
    unique_suffix = uuid4().hex[:8]
    payload = {
        "description": f"api-test-temp-{unique_suffix}",
        "public": False,
        "files": {
            f"test_{unique_suffix}.txt": {
                "content": "Hello from automated tests"
            }
        }
    }
    resp = gists_api.create_gist(payload)
    gist = resp.json()
    try:
        yield gist
    finally:
        try:
            gists_api.delete_gist(gist["id"], expected_status=204)
        except Exception:
            pass


@pytest.fixture
def forked_gist(gists_api):
    fork_id = None
    try:
        public = gists_api.list_public_gists().json()
        assert public, "Expected at least one public gist to exist"
        src_gist_id = public[0]["id"]

        resp = gists_api.fork_gist(src_gist_id, expected_status=201)
        fork_id = resp.json()["id"]

        yield {"source_id": src_gist_id, "fork_id": fork_id}
    finally:
        if fork_id:
            with contextlib.suppress(Exception):
                gists_api.delete_gist(fork_id, expected_status=204)
