from typing import Any, Optional

import allure

from src.http_client import HttpClient


class GistsAPI:
    def __init__(self, client: HttpClient, api_version: str = "2022-11-28") -> None:
        self.client = client
        self._headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": api_version,
        }

    def create_gist(self, payload: dict[str, Any], expected_status: int = 201):
        return self.client.post(
            url="/gists",
            json=payload,
            headers=self._headers,
            expected_status=expected_status,
        )

    def get_gist(self, gist_id: str, expected_status: int = 200):
        return self.client.get(
            url=f"/gists/{gist_id}",
            headers=self._headers,
            expected_status=expected_status,
        )

    def update_gist(self, gist_id: str, payload: dict[str, Any], expected_status: int = 200):
        return self.client.patch(
            url=f"/gists/{gist_id}",
            json=payload,
            headers=self._headers,
            expected_status=expected_status,
        )

    def delete_gist(self, gist_id: str, expected_status: int = 204):
        return self.client.delete(
            url=f"/gists/{gist_id}",
            headers=self._headers,
            expected_status=expected_status,
        )

    def list_gists_for_authenticated_user(self, since: Optional[str] = None, expected_status: int = 200):
        params = {"since": since} if since else None
        return self.client.get(
            url="/gists",
            params=params,
            headers=self._headers,
            expected_status=expected_status,
        )

    def list_public_gists(
            self,
            since: Optional[str] = None,
            per_page: int | None = None,
            expected_status: int = 200,
    ):
        params = {}
        if since:
            params["since"] = since
        if per_page:
            params["per_page"] = per_page

        return self.client.get(
            url="/gists/public",
            params=params,
            headers=self._headers,
            expected_status=expected_status,
        )

    def list_starred_gists(self, expected_status: int = 200):
        return self.client.get(
            url="/gists/starred",
            headers=self._headers,
            expected_status=expected_status,
        )

    def list_gists_for_user(self, username: str, since: Optional[str] = None, expected_status: int = 200):
        params = {"since": since} if since else None
        return self.client.get(
            url=f"/users/{username}/gists",
            params=params,
            headers=self._headers,
            expected_status=expected_status,
        )

    def fork_gist(self, gist_id: str, expected_status: int = 201):
        return self.client.post(
            url=f"/gists/{gist_id}/forks",
            headers=self._headers,
            expected_status=expected_status,
        )

    def list_gist_forks(self, gist_id: str, expected_status: int = 200):
        return self.client.get(
            url=f"/gists/{gist_id}/forks",
            headers=self._headers,
            expected_status=expected_status,
        )

    def check_starred(self, gist_id: str, expected_status: int = 204):
        # 204 if starred, 404 if not starred
        return self.client.get(
            url=f"/gists/{gist_id}/star",
            headers=self._headers,
            expected_status=expected_status,
        )

    def star(self, gist_id: str, expected_status: int = 204):
        return self.client.put(
            url=f"/gists/{gist_id}/star",
            headers=self._headers,
            expected_status=expected_status,
        )

    def unstar(self, gist_id: str, expected_status: int = 204):
        return self.client.delete(
            url=f"/gists/{gist_id}/star",
            headers=self._headers,
            expected_status=expected_status,
        )

    def list_gist_commits(self, gist_id: str, expected_status: int = 200):
        return self.client.get(
            url=f"/gists/{gist_id}/commits",
            headers=self._headers,
            expected_status=expected_status,
        )
