from typing import Any

from strawberry.permission import BasePermission
from strawberry.types import Info


class IsAuthenticated(BasePermission):
    """Cross-cutting auth gate — the analogue of DRF's permission_classes.

    Deliberately separate from the AuthPayload | AuthError union pattern:
      * union errors  = expected *business* outcomes the client should render
                        ("email taken", "wrong password");
      * permissions   = "you are not allowed to even call this field",
                        a protocol-level GraphQL error.
    Apply to any field via strawberry.mutation(permission_classes=[...]).
    """

    message: str = "Authentication required"

    def has_permission(self, source: Any, info: Info, **kwargs: Any) -> bool:
        return info.context.get("current_user") is not None
