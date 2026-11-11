"""Fixed identifiers and public demo adapters."""

from __future__ import annotations

TOOL_NAME = "Engineering Doctor"
TOOL_VERSION = "0.1.0"
TOOL_STATUS = "LIMITED"
CLASSIFICATION = "PUBLIC_CANDIDATE"
BANNER = (
    "A pass is not authorization, scientific validation, or independent verification."
)

# Default GitHub owner used when --owner is omitted. This is the public
# organization that hosts this repository.
DEFAULT_GITHUB_OWNER = "C2O-Chaos-to-Order"

# Pinned snapshot of this public repository used by the demo adapters.
PUBLIC_DEMO_SHA = "3c521a82ee1404bd09d219c59ff6a466cb0721d0"
PUBLIC_DEMO_REPO = "The-UNIVERSALIS-Ecosystem"

PUBLIC_DEMO_ADAPTERS: tuple[dict[str, object], ...] = (
    {
        "id": "universalis-prototype",
        "owner": DEFAULT_GITHUB_OWNER,
        "repo": PUBLIC_DEMO_REPO,
        "pinned_sha": PUBLIC_DEMO_SHA,
        "workdir": ".",
        "argv_suffix": ("-m", "unittest", "discover", "-s", "prototype/tests", "-v"),
    },
    {
        "id": "universalis-scaffold",
        "owner": DEFAULT_GITHUB_OWNER,
        "repo": PUBLIC_DEMO_REPO,
        "pinned_sha": PUBLIC_DEMO_SHA,
        "workdir": ".",
        "argv_suffix": ("-m", "unittest", "discover", "-s", "scaffold/tests", "-v"),
    },
)

SEVERITIES: tuple[str, ...] = ("Critical", "High", "Medium", "Low")
DEFAULT_SUITE_TIMEOUT_SEC = 180
