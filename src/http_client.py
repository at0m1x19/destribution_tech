import logging
from enum import Enum
from json import JSONDecodeError
from pprint import pformat
from typing import Any, Mapping, Optional

import allure
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)


class HttpMethod(str, Enum):
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    PATCH = "PATCH"
    DELETE = "DELETE"


class HttpClient:
    """
    HTTP client wrapper around requests.Session with:
    - base_url handling
    - default headers and cookies
    - retries for transient errors
    - expected status code assertion
    - Allure attachments for request/response
    """

    def __init__(
        self,
        *,
        base_url: str,
        default_headers: Optional[Mapping[str, str]] = None,
        default_cookies: Optional[Mapping[str, str]] = None,
        verify: bool | str = True,
        timeout: int | float | tuple | None = 30,
        retries_total: int = 3,
        backoff_factor: float = 0.3,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        self.session.headers.update(default_headers or {})
        self.session.cookies.update(default_cookies or {})
        self.session.verify = verify
        self._default_timeout = timeout

        retry = Retry(
            total=retries_total,
            connect=retries_total,
            read=retries_total,
            backoff_factor=backoff_factor,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=frozenset(["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"]),
            raise_on_status=False,
        )
        adapter = HTTPAdapter(max_retries=retry)
        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)

    def request(
        self,
        *,
        method: HttpMethod | str,
        url: str,
        params: Optional[dict[str, Any]] = None,
        headers: Optional[Mapping[str, str]] = None,
        cookies: Optional[dict[str, str]] = None,
        files: Optional[dict[str, Any]] = None,
        json: Any | None = None,
        data: Any | None = None,
        expected_status: int | None = None,
        allow_redirects: bool = True,
        timeout: int | float | tuple | None = None,
    ) -> requests.Response:
        if url.startswith(("http://", "https://")):
            full_url = url
        else:
            full_url = f"{self.base_url}{url}"

        orig_cookies = None
        if cookies:
            orig_cookies = self.session.cookies.copy()
            self.session.cookies.update(cookies)

        req = requests.Request(
            method=method, url=full_url, headers=headers, params=params, json=json, data=data, files=files
        )
        prep = self.session.prepare_request(req)

        resp = None
        try:
            resp = self.session.send(
                prep,
                allow_redirects=allow_redirects,
                timeout=timeout or self._default_timeout,
                verify=self.session.verify,
            )
            self._attach_allure(resp)
            if expected_status is not None:
                assert resp.status_code == expected_status, (
                    f"Unexpected status {resp.status_code}, expected {expected_status}.\n"
                    f"URL: {full_url}\nBody: {self._safe_body(resp)}"
                )
            return resp
        finally:
            if orig_cookies is not None:
                self.session.cookies = orig_cookies

    def get(self, url: str, **kw) -> requests.Response:
        return self.request(method=HttpMethod.GET, url=url, **kw)

    def post(self, url: str, **kw) -> requests.Response:
        return self.request(method=HttpMethod.POST, url=url, **kw)

    def put(self, url: str, **kw) -> requests.Response:
        return self.request(method=HttpMethod.PUT, url=url, **kw)

    def patch(self, url: str, **kw) -> requests.Response:
        return self.request(method=HttpMethod.PATCH, url=url, **kw)

    def delete(self, url: str, **kw) -> requests.Response:
        return self.request(method=HttpMethod.DELETE, url=url, **kw)

    @staticmethod
    def _safe_body(resp: requests.Response) -> str:
        try:
            return pformat(resp.json(), indent=2)
        except (JSONDecodeError, ValueError, TypeError):
            try:
                return resp.text
            except Exception:
                return "<unreadable>"

    @staticmethod
    def _attach_allure(response: requests.Response) -> None:
        try:
            indent = 2
            req = response.request
            try:
                resp_body = pformat(response.json(), indent=indent)
            except (JSONDecodeError, ValueError, TypeError):
                resp_body = response.text

            try:
                req_body = pformat(req.body, indent=indent)
            except Exception:
                req_body = str(req.body)

            allure.attach(
                body=(
                    f"Request:\n{req.method} {req.url}\n\n"
                    f"Headers:\n{pformat(dict(req.headers), indent=indent)}\n\n"
                    f"Body:\n{req_body}\n"
                ),
                name=f"{req.method} {req.url}",
                attachment_type=allure.attachment_type.TEXT,
            )
            allure.attach(
                body=(
                    f"Status: {response.status_code} {response.reason}\n\n"
                    f"Headers:\n{pformat(dict(response.headers), indent=indent)}\n\n"
                    f"Body:\n{resp_body}\n"
                ),
                name=f"Response {response.status_code}",
                attachment_type=allure.attachment_type.TEXT,
            )
        except Exception as e:
            logger.debug(f"Failed to attach allure data: {e}")
