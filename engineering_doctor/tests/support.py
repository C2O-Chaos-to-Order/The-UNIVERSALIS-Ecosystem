
"""Test doubles for GitHub GET responses and suite clones."""

from __future__ import annotations

import json
from typing import Any
from urllib.parse import urlsplit


class FakeFetch:
    def __init__(self) -> None:
        self.routes: dict[str, tuple[int, dict[str, str], Any]] = {}
        self.calls: list[str] = []

    def register(self, path: str, body: Any, status: int = 200, headers: dict[str, str] | None = None) -> None:
        self.routes[path] = (status, {k.lower(): v for k, v in (headers or {}).items()}, body)

    def __call__(self, url: str, headers: dict[str, str]) -> tuple[int, dict[str, str], bytes]:
        self.calls.append(url)
        path = urlsplit(url).path
        query = urlsplit(url).query
        key = path if path in self.routes else f"{path}?{query}"
        if key not in self.routes and path not in self.routes:
            # try path plus exact registered query-bearing keys
            for candidate in (path, key):
                if candidate in self.routes:
                    key = candidate
                    break
            else:
                return 404, {}, b'{"message":"not found"}'
        else:
            if key not in self.routes:
                key = path
        status, extra_headers, body = self.routes[key]
        raw = body if isinstance(body, (bytes, bytearray)) else json.dumps(body).encode("utf-8")
        return status, extra_headers, raw
