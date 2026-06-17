from __future__ import annotations

from dataclasses import dataclass
import json
from typing import Any
from urllib.parse import parse_qs, urlencode, urljoin, urlparse
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError


class CanvasAPIError(RuntimeError):
    pass


@dataclass(frozen=True)
class CanvasClient:
    base_url: str
    token: str
    timeout_seconds: int = 30

    def _api_url(self, path: str, params: dict[str, Any] | None = None) -> str:
        normalized_path = path if path.startswith("/") else f"/{path}"
        url = urljoin(f"{self.base_url.rstrip('/')}/", f"api/v1{normalized_path}")
        if params:
            url = f"{url}?{urlencode(params, doseq=True)}"
        return url

    def get_json(self, path_or_url: str, params: dict[str, Any] | None = None) -> tuple[Any, dict[str, str]]:
        url = path_or_url if path_or_url.startswith(("http://", "https://")) else self._api_url(path_or_url, params)
        request = Request(url, headers={"Authorization": f"Bearer {self.token}", "Accept": "application/json"})
        try:
            with urlopen(request, timeout=self.timeout_seconds) as response:
                body = response.read().decode("utf-8")
                headers = {key.lower(): value for key, value in response.headers.items()}
        except HTTPError as exc:
            raise CanvasAPIError(f"Canvas API request failed with HTTP {exc.code}") from exc
        except URLError as exc:
            raise CanvasAPIError(f"Canvas API request failed: {exc.reason}") from exc

        if not body:
            return None, headers
        try:
            return json.loads(body), headers
        except json.JSONDecodeError as exc:
            raise CanvasAPIError("Canvas API returned invalid JSON") from exc

    def get_paginated(self, path: str, params: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        query = {"per_page": 100}
        if params:
            query.update(params)

        next_url: str | None = self._api_url(path, query)
        items: list[dict[str, Any]] = []
        while next_url:
            payload, headers = self.get_json(next_url)
            if payload is None:
                payload = []
            if not isinstance(payload, list):
                raise CanvasAPIError("Canvas API paginated endpoint returned a non-list response")
            items.extend(payload)
            next_url = parse_next_link(headers.get("link", ""))
        return items

    def get_todo_items(self) -> list[dict[str, Any]]:
        return self.get_paginated("/users/self/todo")

    def get_submission(self, course_id: int | str, assignment_id: int | str) -> dict[str, Any]:
        payload, _ = self.get_json(f"/courses/{course_id}/assignments/{assignment_id}/submissions/self")
        if not isinstance(payload, dict):
            raise CanvasAPIError("Canvas submission endpoint returned a non-object response")
        return payload


def parse_next_link(link_header: str) -> str | None:
    if not link_header:
        return None
    for part in link_header.split(","):
        section = part.strip()
        if 'rel="next"' not in section:
            continue
        start = section.find("<")
        end = section.find(">")
        if start != -1 and end != -1 and end > start:
            return section[start + 1 : end]
    return None


def extract_canvas_id(value: str | None) -> str | None:
    if not value:
        return None
    parsed = urlparse(value)
    query = parse_qs(parsed.query)
    for key in ("assignment_id", "id"):
        if query.get(key):
            return query[key][0]
    segments = [segment for segment in parsed.path.split("/") if segment]
    if segments:
        return segments[-1]
    return None
