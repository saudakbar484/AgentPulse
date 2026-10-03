import uuid
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from app.core.security import (
    create_access_token,
    generate_api_key,
    hash_password,
    verify_password,
)

router = APIRouter(prefix="/auth", tags=["Authentication"])

# In-memory mock user store for fast development and testing
DEMO_USERS: dict[str, dict[str, Any]] = {
    "admin@agentpulse.dev": {
        "id": "11111111-1111-1111-1111-111111111111",
        "email": "admin@agentpulse.dev",
        "password_hash": hash_password("AgentPulse2026!"),
        "full_name": "Demo Admin",
        "org_id": "00000000-0000-0000-0000-000000000001",
        "role": "owner",
    }
}


class RegisterRequest(BaseModel):
    email: str
    password: str
    full_name: str
    organization_name: str = "Default Agency"


class LoginRequest(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict[str, Any]


class APIKeyCreateRequest(BaseModel):
    name: str
    scopes: list[str] = ["ingest", "runs:read"]


class APIKeyResponse(BaseModel):
    name: str
    key_prefix: str
    raw_key: str  # Shown only once!


@router.post("/register", response_model=TokenResponse)
async def register(payload: RegisterRequest) -> TokenResponse:
    if payload.email in DEMO_USERS:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User with this email already exists"
        )

    user_id = str(uuid.uuid4())
    org_id = str(uuid.uuid4())
    user_record = {
        "id": user_id,
        "email": payload.email,
        "password_hash": hash_password(payload.password),
        "full_name": payload.full_name,
        "org_id": org_id,
        "role": "owner",
        "org_name": payload.organization_name,
    }
    DEMO_USERS[payload.email] = user_record

    access_token = create_access_token({"sub": user_id, "org_id": org_id, "email": payload.email})
    return TokenResponse(
        access_token=access_token,
        user={"id": user_id, "email": payload.email, "full_name": payload.full_name, "org_id": org_id}
    )


@router.post("/login", response_model=TokenResponse)
async def login(payload: LoginRequest) -> TokenResponse:
    user = DEMO_USERS.get(payload.email)
    if not user or not verify_password(payload.password, user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )

    access_token = create_access_token({"sub": user["id"], "org_id": user["org_id"], "email": user["email"]})
    return TokenResponse(
        access_token=access_token,
        user={"id": user["id"], "email": user["email"], "full_name": user["full_name"], "org_id": user["org_id"]}
    )


@router.get("/me")
async def get_current_user() -> dict[str, Any]:
    # Returns default demo user profile
    demo = DEMO_USERS["admin@agentpulse.dev"]
    return {
        "id": demo["id"],
        "email": demo["email"],
        "full_name": demo["full_name"],
        "org_id": demo["org_id"],
        "role": demo["role"],
    }


@router.post("/api-keys", response_model=APIKeyResponse)
async def create_new_api_key(payload: APIKeyCreateRequest) -> APIKeyResponse:
    raw_key, prefix, _ = generate_api_key()
    return APIKeyResponse(
        name=payload.name,
        key_prefix=prefix,
        raw_key=raw_key,
    )
