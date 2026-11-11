"""Runtime configuration for a corpus-agnostic Engineering Doctor run."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .constants import (
    BANNER,
    CLASSIFICATION,
    DEFAULT_GITHUB_OWNER,
    PUBLIC_DEMO_ADAPTERS,
    TOOL_NAME,
    TOOL_STATUS,
    TOOL_VERSION,
)


@dataclass
class RuntimeConfig:
    """Operator- or adapter-supplied settings. The default allowlist is empty."""

    tool_name: str = TOOL_NAME
    tool_version: str = TOOL_VERSION
    tool_status: str = TOOL_STATUS
    classification: str = CLASSIFICATION
    banner: str = BANNER
    github_owner: str = DEFAULT_GITHUB_OWNER
    allowlist: tuple[str, ...] = ()
    excluded: tuple[str, ...] = ()
    suite_adapters: tuple[dict[str, object], ...] = PUBLIC_DEMO_ADAPTERS
    known_skip_markers: tuple[str, ...] = ()
    extra_limitations: tuple[str, ...] = ()
    extra_inputs: dict[str, Any] = field(default_factory=dict)
