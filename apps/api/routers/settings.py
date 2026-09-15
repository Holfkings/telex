"""
settings.py — BYOK API key management endpoints.

Endpoints:
  POST   /api/settings/api-keys          — store (upsert) an encrypted key
  GET    /api/settings/api-keys          — list connected providers (no keys returned)
  DELETE /api/settings/api-keys/{provider} — hard-delete a key

All endpoints require authentication via the existing require_auth dependency.
The plaintext key is only ever held in memory during the POST handler and is
immediately discarded after encryption. It is never written to logs or returned
to the client.
"""
import logging
import uuid
from datetime import datetime, timezone
from typing import Literal, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select

from db.session import AsyncSessionLocal
from db.models import UserApiKey
from routers.auth import require_auth
from services.crypto import encrypt_key, decrypt_key

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/settings", tags=["settings"])

# Supported provider IDs — extend this list as new providers are added.
SUPPORTED_PROVIDERS = frozenset({
    "openai", "anthropic", "gemini", "mistral", "groq",
    "cohere", "xai", "deepseek", "together", "nemotron",
})


# ── Request / Response schemas ───────────────────────────────────────────────

class StoreKeyRequest(BaseModel):
    provider: str = Field(..., description="Provider ID, e.g. 'openai'")
    key: str = Field(..., min_length=1, description="Plaintext API key (POST only — never returned)")


class ApiKeyOut(BaseModel):
    provider: str
    connected: bool
    created_at: Optional[datetime] = None
    last_used_at: Optional[datetime] = None


class StoreKeyResponse(BaseModel):
    provider: str
    connected: bool
    created_at: datetime


class DeleteKeyResponse(BaseModel):
    provider: str
    connected: bool


class ListKeysResponse(BaseModel):
    keys: list[ApiKeyOut]


# ── Helpers ──────────────────────────────────────────────────────────────────

def _parse_user_id(auth: dict) -> Optional[uuid.UUID]:
    """Extract and parse the user UUID from the auth dict returned by require_auth."""
    user_id_str = auth.get("user_id", "")
    if user_id_str == "demo-operator":
        return None  # Demo key has no real user_id
    try:
        return uuid.UUID(user_id_str)
    except (ValueError, AttributeError):
        return None


# ── Endpoints ────────────────────────────────────────────────────────────────

@router.post("/api-keys", response_model=StoreKeyResponse, status_code=201)
async def store_api_key(
    body: StoreKeyRequest,
    auth: dict = Depends(require_auth),
):
    """
    Encrypt and upsert a BYOK API key for the authenticated user.

    The plaintext key is encrypted with Fernet before being stored.
    It is never returned to the client or written to any log.
    """
    if body.provider not in SUPPORTED_PROVIDERS:
        raise HTTPException(
            status_code=422,
            detail=f"Unsupported provider '{body.provider}'. Supported: {sorted(SUPPORTED_PROVIDERS)}",
        )

    user_id = _parse_user_id(auth)
    if user_id is None:
        raise HTTPException(status_code=403, detail="Demo accounts cannot store API keys")

    # Encrypt key — plaintext is only in memory during this call
    ciphertext = encrypt_key(body.key)
    # body.key goes out of scope here and is not stored anywhere

    now = datetime.now(timezone.utc)

    async with AsyncSessionLocal() as session:
        # Upsert: update if provider row already exists for this user
        result = await session.execute(
            select(UserApiKey).where(
                UserApiKey.user_id == user_id,
                UserApiKey.provider == body.provider,
            )
        )
        existing = result.scalar_one_or_none()

        if existing:
            existing.encrypted_key = ciphertext
            existing.created_at = now
            existing.last_used_at = None
            row = existing
        else:
            row = UserApiKey(
                user_id=user_id,
                provider=body.provider,
                encrypted_key=ciphertext,
                created_at=now,
            )
            session.add(row)

        await session.commit()
        await session.refresh(row)

    logger.info("settings: stored BYOK key for provider=%s user=%s", body.provider, user_id)
    return StoreKeyResponse(
        provider=row.provider,
        connected=True,
        created_at=row.created_at,
    )


@router.get("/api-keys", response_model=ListKeysResponse)
async def list_api_keys(auth: dict = Depends(require_auth)):
    """
    Return the list of providers for which the user has stored a key.
    The encrypted key itself is NEVER returned — only connection status.
    """
    user_id = _parse_user_id(auth)
    if user_id is None:
        return ListKeysResponse(keys=[])

    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(UserApiKey).where(UserApiKey.user_id == user_id)
        )
        rows = result.scalars().all()

    keys = [
        ApiKeyOut(
            provider=row.provider,
            connected=True,
            created_at=row.created_at,
            last_used_at=row.last_used_at,
        )
        for row in rows
    ]
    return ListKeysResponse(keys=keys)


@router.delete("/api-keys/{provider}", response_model=DeleteKeyResponse)
async def delete_api_key(
    provider: str,
    auth: dict = Depends(require_auth),
):
    """
    Hard-delete the stored API key for the given provider.
    The row is physically removed from the database (not soft-deleted).
    """
    if provider not in SUPPORTED_PROVIDERS:
        raise HTTPException(status_code=404, detail=f"No key found for provider '{provider}'")

    user_id = _parse_user_id(auth)
    if user_id is None:
        raise HTTPException(status_code=403, detail="Demo accounts cannot manage API keys")

    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(UserApiKey).where(
                UserApiKey.user_id == user_id,
                UserApiKey.provider == provider,
            )
        )
        row = result.scalar_one_or_none()
        if row is None:
            raise HTTPException(status_code=404, detail=f"No key found for provider '{provider}'")
        await session.delete(row)
        await session.commit()

    logger.info("settings: deleted BYOK key for provider=%s user=%s", provider, user_id)
    return DeleteKeyResponse(provider=provider, connected=False)
