from typing import Protocol, runtime_checkable


@runtime_checkable
class Authorizer(Protocol):
    def is_authorized(self, user_id: int) -> bool: ...


class FakeAuthorizer:
    def __init__(self, allow: bool = True) -> None:
        self._allow = allow

    def is_authorized(self, user_id: int) -> bool:
        return self._allow


class AllowlistAuthorizer:
    def __init__(self, allowlist: set[int]) -> None:
        self._allowlist = allowlist

    def is_authorized(self, user_id: int) -> bool:
        if not self._allowlist:
            return True
        return user_id in self._allowlist
