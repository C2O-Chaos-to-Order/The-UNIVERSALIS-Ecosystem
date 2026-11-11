
"""Read-only GitHub HTTP client (GET only)."""

from __future__ import annotations

import json
import os
import re
import subprocess
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Callable
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from .constants import TOOL_NAME, TOOL_VERSION

FetchResult = tuple[int, dict[str, str], bytes]
FetchFn = Callable[[str, dict[str, str]], FetchResult]

_TOKEN_PATTERNS = (
    re.compile(r"ghp_[A-Za-z0-9]{20,}"),
    re.compile(r"gho_[A-Za-z0-9]{20,}"),
    re.compile(r"ghu_[A-Za-z0-9]{20,}"),
    re.compile(r"ghs_[A-Za-z0-9]{20,}"),
    re.compile(r"github_pat_[A-Za-z0-9_]{20,}"),
)


def redact(text: str, token: str | None = None) -> str:
    """Remove credential material from a string before it is recorded or printed."""

    redacted = text
    if token:
        redacted = redacted.replace(token, "<redacted>")
    for pattern in _TOKEN_PATTERNS:
        redacted = pattern.sub("<redacted>", redacted)
    return redacted


def discover_token() -> str | None:
    """Return a token from the environment or `gh auth token`, never printing it."""

    for key in ("GITHUB_TOKEN", "GH_TOKEN"):
        value = os.environ.get(key, "").strip()
        if value:
            return value
    try:
        result = subprocess.run(
            ["gh", "auth", "token"],
            check=False,
            capture_output=True,
            text=True,
            timeout=10,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    token = (result.stdout or "").strip()
    if result.returncode == 0 and token:
        return token
    return None


class GitHubError(Exception):
    """A GET request failed or returned an unusable body."""

    def __init__(self, message: str, status: int | None = None) -> None:
        super().__init__(message)
        self.status = status


class GitHubClient:
    """HTTP client that can only issue GET requests to api.github.com."""

    def __init__(
        self,
        token: str | None = None,
        fetch: FetchFn | None = None,
        api_root: str = "https://api.github.com",
    ) -> None:
        self._token = token
        self._fetch = fetch or self._urllib_fetch
        self.api_root = api_root.rstrip("/")
        self.authenticated = bool(token)

    def __repr__(self) -> str:
        return f"GitHubClient(authenticated={self.authenticated!r}, api_root={self.api_root!r})"

    def _headers(self) -> dict[str, str]:
        headers = {
            "Accept": "application/vnd.github+json",
            "User-Agent": f"{TOOL_NAME.replace(' ', '-')}/{TOOL_VERSION} (read-only)",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        if self._token:
            headers["Authorization"] = f"Bearer {self._token}"
        return headers

    def _urllib_fetch(self, url: str, headers: dict[str, str]) -> FetchResult:
        request = urllib.request.Request(url, headers=headers, method="GET")
        try:
            with urllib.request.urlopen(request, timeout=45) as response:
                body = response.read()
                raw_headers = {k.lower(): v for k, v in response.headers.items()}
                return int(response.status), raw_headers, body
        except urllib.error.HTTPError as exc:
            body = exc.read() if exc.fp else b""
            raw_headers = {k.lower(): v for k, v in exc.headers.items()} if exc.headers else {}
            return int(exc.code), raw_headers, body
        except urllib.error.URLError as exc:
            raise GitHubError(redact(f"network error contacting GitHub: {exc}", self._token)) from exc

    def get(self, path: str, query: dict[str, Any] | None = None) -> tuple[Any, dict[str, str]]:
        """GET a JSON resource. Returns (decoded_body, response_headers)."""

        if not path.startswith("/"):
            raise GitHubError("GitHub path must start with '/'")
        url = self.api_root + path
        if query:
            parts = urlsplit(url)
            merged = dict(parse_qsl(parts.query, keep_blank_values=True))
            merged.update({k: str(v) for k, v in query.items() if v is not None})
            url = urlunsplit(
                (parts.scheme, parts.netloc, parts.path, urlencode(merged), parts.fragment)
            )
        status, headers, body = self._fetch(url, self._headers())
        text = body.decode("utf-8", errors="replace")
        if status >= 400:
            raise GitHubError(
                redact(f"GET {path} failed with HTTP {status}: {text[:300]}", self._token),
                status=status,
            )
        if not text.strip():
            return None, headers
        try:
            return json.loads(text), headers
        except json.JSONDecodeError as exc:
            raise GitHubError(
                redact(f"GET {path} returned non-JSON body: {exc}", self._token),
                status=status,
            ) from exc

    def get_paginated(self, path: str, query: dict[str, Any] | None = None) -> list[Any]:
        """Follow Link rel=next headers until exhausted. Fail closed on error."""

        params = dict(query or {})
        params.setdefault("per_page", 100)
        items: list[Any] = []
        next_path = path
        next_query: dict[str, Any] | None = params
        seen = 0
        while next_path:
            payload, headers = self.get(next_path, next_query)
            if payload is None:
                break
            if isinstance(payload, list):
                items.extend(payload)
            elif isinstance(payload, dict) and isinstance(payload.get("items"), list):
                items.extend(payload["items"])
            else:
                raise GitHubError(
                    f"GET {next_path} did not return a list page; refusing to treat it as empty"
                )
            seen += 1
            if seen > 100:
                raise GitHubError(f"GET {path} exceeded pagination safety limit")
            nxt = _next_link(headers.get("link", ""))
            if nxt:
                parsed = urlsplit(nxt)
                next_path = parsed.path
                next_query = dict(parse_qsl(parsed.query, keep_blank_values=True))
            else:
                next_path = ""
                next_query = None
        return items


def _next_link(link_header: str) -> str | None:
    if not link_header:
        return None
    for part in link_header.split(","):
        section = part.strip()
        if 'rel="next"' not in section:
            continue
        start = section.find("<")
        end = section.find(">", start + 1)
        if start >= 0 and end > start:
            return section[start + 1 : end]
    return None
