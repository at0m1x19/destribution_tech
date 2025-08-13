import time
import uuid

import allure

from src.api.gists import GistsAPI
from src.http_client import HttpClient
from src.utils.wait import wait_until_condition_reached


@allure.title("Create → Get a Gist")
def test_create_and_get_gist(gists_api, temp_gist):
    gist_id = temp_gist.get("id")
    assert gist_id, "Expected a valid gist ID"

    with allure.step("Get created gist"):
        resp = gists_api.get_gist(gist_id)
        data = resp.json()
        assert data["id"] == gist_id, f"Gist ID mismatch: expected {gist_id}, got {data.get('id')}"
        assert "files" in data, "Response JSON should contain 'files' key"


@allure.title("Update an existing Gist")
def test_update_gist(gists_api, temp_gist):
    gist_id = temp_gist["id"]
    assert gist_id, "Expected a valid gist ID"

    filename = list(temp_gist["files"].keys())[0]
    new_desc = f"updated-{int(time.time())}"
    new_content = "Updated content via automated test"

    with allure.step("Update gist description and content"):
        payload = {
            "description": new_desc,
            "files": {filename: {"content": new_content}},
        }
        resp = gists_api.update_gist(gist_id, payload)
        updated = resp.json()
        assert updated["description"] == new_desc, (
            f"Description not updated: expected '{new_desc}', got '{updated.get('description')}'"
        )
        assert filename in updated["files"], (
            f"Updated files should contain '{filename}'. Keys: {list(updated.get('files', {}).keys())}"
        )

    with allure.step("Verify updated gist content"):
        resp = gists_api.get_gist(gist_id)
        data = resp.json()
        assert data["description"] == new_desc, (
            f"Persisted description mismatch: expected '{new_desc}', got '{data.get('description')}'"
        )
        assert filename in data["files"], (
            f"Persisted files should contain '{filename}'. Keys: {list(data.get('files', {}).keys())}"
        )
        assert data["files"][filename]["content"] == new_content, (
            f"File content not updated: expected '{new_content}', got '{data.get('files', {}).get(filename, {}).get('content')}'"
        )


@allure.title("Star and unstar a Gist")
def test_star_unstar_gist(gists_api, temp_gist):
    gist_id = temp_gist["id"]
    assert gist_id, "Expected a valid gist ID"

    with allure.step("Verify gist is not starred"):
        gists_api.check_starred(gist_id, expected_status=404)

    with allure.step("Star gist"):
        gists_api.star(gist_id)

    with allure.step("Check gist is starred"):
        gists_api.check_starred(gist_id, expected_status=204)

    with allure.step("Unstar gist"):
        gists_api.unstar(gist_id)

    with allure.step("Check gist is not starred"):
        gists_api.check_starred(gist_id, expected_status=404)


@allure.title("Delete a Gist")
def test_delete_gist(gists_api, temp_gist):
    gist_id = temp_gist["id"]
    assert gist_id, "Expected a valid gist ID"

    with allure.step("Delete gist"):
        gists_api.delete_gist(gist_id)
    with allure.step("Verify 404 on get after delete"):
        gists_api.get_gist(gist_id, expected_status=404)


@allure.title("List public gists returns an array")
def test_list_public_gists(gists_api):
    with allure.step("List public gists"):
        resp = gists_api.list_public_gists()
        data = resp.json()
        assert isinstance(data, list), f"Expected list of gists, got {type(data).__name__}"


@allure.title("Gist commits contain two versions after an update")
def test_gist_commits(gists_api, temp_gist):
    gist_id = temp_gist["id"]
    assert gist_id, "Expected a valid gist ID"

    filename = list(temp_gist["files"].keys())[0]

    with allure.step("Perform an update to create a second commit"):
        gists_api.update_gist(
            gist_id,
            payload={"files": {filename: {"content": f"bump-{int(time.time())}"}}},
        )

    with allure.step("List gist commits"):
        resp = gists_api.list_gist_commits(gist_id)
        commits = resp.json()
        assert isinstance(commits, list), f"Expected list of commits, got {type(commits).__name__}"
        assert len(commits) == 2, f"Expected exactly 2 commits after one update, got {len(commits)}"


@allure.title("Fork a Gist and verify forks list")
def test_gist_forks(gists_api, forked_gist):
    source_id = forked_gist["source_id"]
    fork_id = forked_gist["fork_id"]

    wait_until_condition_reached(
        condition_summary=f"Wait until fork {fork_id} appears in forks list",
        condition=lambda: any(
            item.get("id") == fork_id for item in gists_api.list_gist_forks(source_id).json()
        ),
        timeout=10,
    )


@allure.title("Get unknown gist returns 404")
def test_get_nonexistent_gist_returns_404(gists_api):
    non_existent = uuid.uuid4().hex
    with allure.step("Request non-existent gist and expect 404"):
        gists_api.get_gist(non_existent, expected_status=404)


@allure.title("Create gist with invalid payload returns 422")
def test_create_gist_invalid_payload_422(gists_api):
    payload = {"description": "invalid payload", "public": False}
    with allure.step("POST invalid payload to create gist and expect 422"):
        gists_api.create_gist(payload, expected_status=422)


@allure.title("Unauthorized on protected endpoint without token")
def test_unauthorized_when_no_token(settings):
    with allure.step("Create client without Authorization header"):
        client = HttpClient(base_url=settings.base_url)
        api = GistsAPI(client, api_version=settings.api_version)
    with allure.step("GET starred gists should require authentication -> 401"):
        api.list_starred_gists(expected_status=401)
