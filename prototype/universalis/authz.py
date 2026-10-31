"""In-memory authorization stub.

IN-MEMORY AUTHORIZATION STUB. This stub proves nothing about a real identity
provider. It is not an identity provider, it does not verify a credential,
and a decision it returns is not evidence that any principal is authenticated.
"""

from __future__ import annotations

from dataclasses import dataclass

from universalis.errors import AuthorizationNotImplied
from universalis.states import Readiness

STUB_NOTICE = (
    "IN-MEMORY AUTHORIZATION STUB. This stub proves nothing about a real "
    "identity provider. It is not an identity provider and it is not evidence "
    "that any principal is authenticated."
)

_DIMENSIONS = ("principal", "purpose", "project", "credential", "action")


@dataclass(frozen=True)
class AuthorizationDecision:
    permitted: bool
    failed_dimensions: tuple
    path: str | None
    path_visible: bool
    stub: bool
    notice: str
    reason: str

    def __post_init__(self) -> None:
        if not self.stub or STUB_NOTICE not in self.notice:
            raise AuthorizationNotImplied(
                "an authorization decision from this module must be labelled as the stub"
            )


class InMemoryAuthorizationStub:
    """IN-MEMORY AUTHORIZATION STUB.

    This stub proves nothing about a real identity provider.
    It is not an identity provider and it stores no credentials.
    """

    def __init__(self) -> None:
        self.notice = STUB_NOTICE
        self.stub = True
        self._grants: set[tuple[str, str, str, str, str]] = set()
        self._visible: set[str] = set()
        self._declines: list[dict] = []
        self.standing = {
            "access": {"archive": True},
            "data": {"rows": 3},
            "standing": "member",
            "debt": 0,
        }

    def __repr__(self) -> str:
        return f"InMemoryAuthorizationStub({STUB_NOTICE})"

    def grant(
        self,
        *,
        principal: str,
        purpose: str,
        project: str,
        credential: str,
        action: str,
    ) -> None:
        self._grants.add((principal, purpose, project, credential, action))

    def show_path(self, path: str) -> None:
        self._visible.add(path)

    def authorize(
        self,
        *,
        principal: str | None = None,
        purpose: str | None = None,
        project: str | None = None,
        credential: str | None = None,
        action: str | None = None,
        path: str | None = None,
    ) -> AuthorizationDecision:
        supplied = {
            "principal": principal,
            "purpose": purpose,
            "project": project,
            "credential": credential,
            "action": action,
        }
        failed = tuple(
            name
            for name in _DIMENSIONS
            if supplied[name] is None or str(supplied[name]).strip() == ""
        )
        visible = path is not None and path in self._visible
        if failed:
            return AuthorizationDecision(
                permitted=False,
                failed_dimensions=failed,
                path=path,
                path_visible=visible,
                stub=True,
                notice=STUB_NOTICE,
                reason="missing authorization dimensions: " + ", ".join(failed),
            )
        key = (
            str(principal),
            str(purpose),
            str(project),
            str(credential),
            str(action),
        )
        permitted = key in self._grants
        if visible and not permitted:
            reason = "path is visible and authorization is still refused"
        elif permitted:
            reason = "stub grant matched all five dimensions; this proves nothing about an identity provider"
        else:
            reason = "no stub grant matched all five dimensions"
        return AuthorizationDecision(
            permitted=permitted,
            failed_dimensions=() if permitted else ("grant",),
            path=path,
            path_visible=visible,
            stub=True,
            notice=STUB_NOTICE,
            reason=reason,
        )

    def authorize_from_passing_test(self, *, test_passed: bool, **_ignored: object) -> None:
        raise AuthorizationNotImplied(
            "ULC-00-11: a passing test does not supply consent or authorization"
        )

    def authorize_from_mapping(self, mapping: object, **_ignored: object) -> None:
        raise AuthorizationNotImplied(
            "ULC-00-11: a mapping does not supply consent or authorization"
        )

    def authorize_from_equation(self, equation: object, **_ignored: object) -> None:
        raise AuthorizationNotImplied(
            "ULC-00-11: an equation or symbolic interpretation does not supply "
            "consent or authorization"
        )

    def decline_suggestion(self, *, principal: str, suggestion_id: str) -> dict:
        before = _copy_standing(self.standing)
        grants_before = set(self._grants)
        self._declines.append(
            {"principal": principal, "suggestion_id": suggestion_id, "debt": 0}
        )
        if self.standing != before or self._grants != grants_before:
            raise AuthorizationNotImplied(
                "ULC-26-05: declining a suggestion must not change access, data, or standing"
            )
        return {
            "declined": suggestion_id,
            "principal": principal,
            "debt": 0,
            "standing_unchanged": True,
            "notice": STUB_NOTICE,
        }

    def declines(self) -> list[dict]:
        return list(self._declines)


def readiness_from_stub(decision: AuthorizationDecision) -> Readiness:
    """A stub permit does not evaluate evidence and is not readiness."""

    if decision.stub:
        return Readiness.UNEXECUTED
    return Readiness.ABSENT


def _copy_standing(standing: dict) -> dict:
    return {
        "access": dict(standing["access"]),
        "data": dict(standing["data"]),
        "standing": standing["standing"],
        "debt": standing["debt"],
    }
