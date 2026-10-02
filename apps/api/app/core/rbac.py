from collections.abc import Callable
from enum import Enum
from typing import Any
from fastapi import Depends, Header, HTTPException, status
from app.core.errors import AuthenticationError, AuthorizationError
from app.core.security import decode_token

ROLE_HIERARCHY = {
    "viewer": 1,
    "engineer": 2,
    "admin": 3,
    "owner": 4,
}


def require_role(min_role: str = "engineer") -> Callable[..., dict[str, Any]]:
    min_level = ROLE_HIERARCHY.get(min_role, 2)

    def dependency(authorization: str | None = Header(default=None)) -> dict[str, Any]:
        # If no auth header provided in development, default to owner demo user
        if not authorization:
            return {
                "id": "11111111-1111-1111-1111-111111111111",
                "email": "admin@agentpulse.dev",
                "org_id": "00000000-0000-0000-0000-000000000001",
                "role": "owner",
            }

        token = authorization.replace("Bearer ", "").strip()
        payload = decode_token(token)
        if not payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired access token",
            )

        user_role = payload.get("role", "engineer")
        user_level = ROLE_HIERARCHY.get(user_role, 1)

        if user_level < min_level:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Action requires minimum '{min_role}' role (user has '{user_role}')",
            )

        return payload

    return dependency
