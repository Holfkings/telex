"""
Patch provider factory.

get_patch_provider(name, api_key) returns a PatchProvider for the named
LLM backend. If api_key is provided, that key is used directly (BYOK path).
If api_key is None, the platform's server-side key from settings is used
(hosted-key fallback path — existing behavior unchanged for non-BYOK users).

Provider name → class mapping:
  gemini    → GeminiProvider    (default, platform Gemini key)
  claude    → ClaudeProvider    (Anthropic)
  openai    → OpenAIProvider    (GPT-4o-mini default)
  mistral   → MistralProvider   (mistral-small-latest default)
  groq      → GroqProvider      (llama-3.3-70b-versatile default)
  cohere    → CohereProvider    (command-r-plus-08-2024 default)
  xai       → XAIProvider       (grok-3-mini default)
  deepseek  → DeepSeekProvider  (deepseek-chat default)
  together  → TogetherProvider  (llama-3.3-70B-Instruct-Turbo default)
  nemotron  → NemotronProvider  (nvidia/llama-3.1-nemotron-70b-instruct default)
"""

from .base import PatchProvider


def get_patch_provider(
    name: str | None = None,
    api_key: str | None = None,
) -> PatchProvider:
    """
    Factory for PatchProvider instances.

    Args:
        name:    Provider name. Defaults to settings.llm_provider_default.
        api_key: Plaintext API key. If None, uses the platform server-side key
                 from settings (hosted-key fallback — existing behaviour).

    Returns a PatchProvider implementation.
    Raises ValueError for unknown provider names.
    Raises RuntimeError if the required key is absent.
    """
    from config import settings

    provider_name = (name or settings.llm_provider_default).lower().strip()

    if provider_name == "gemini":
        from .gemini import GeminiProvider

        key = api_key or settings.gemini_api_key
        return GeminiProvider(key)

    if provider_name in ("claude", "anthropic"):
        from .claude import ClaudeProvider

        key = api_key or settings.anthropic_api_key
        return ClaudeProvider(key)

    if provider_name == "openai":
        from .openai_provider import OpenAIProvider

        if not api_key:
            raise RuntimeError(
                "OpenAI is a BYOK-only provider — no platform key is configured. "
                "Add your key in Settings → API Keys."
            )
        return OpenAIProvider(api_key)

    if provider_name == "mistral":
        from .mistral_provider import MistralProvider

        if not api_key:
            raise RuntimeError(
                "Mistral is a BYOK-only provider — add your key in Settings → API Keys."
            )
        return MistralProvider(api_key)

    if provider_name == "groq":
        from .groq_provider import GroqProvider

        if not api_key:
            raise RuntimeError(
                "Groq is a BYOK-only provider — add your key in Settings → API Keys."
            )
        return GroqProvider(api_key)

    if provider_name == "cohere":
        from .extra_providers import CohereProvider

        if not api_key:
            raise RuntimeError(
                "Cohere is a BYOK-only provider — add your key in Settings → API Keys."
            )
        return CohereProvider(api_key)

    if provider_name in ("xai", "grok"):
        from .extra_providers import XAIProvider

        if not api_key:
            raise RuntimeError("xAI is a BYOK-only provider — add your key in Settings → API Keys.")
        return XAIProvider(api_key)

    if provider_name == "deepseek":
        from .extra_providers import DeepSeekProvider

        if not api_key:
            raise RuntimeError(
                "DeepSeek is a BYOK-only provider — add your key in Settings → API Keys."
            )
        return DeepSeekProvider(api_key)

    if provider_name == "together":
        from .extra_providers import TogetherProvider

        if not api_key:
            raise RuntimeError(
                "Together AI is a BYOK-only provider — add your key in Settings → API Keys."
            )
        return TogetherProvider(api_key)

    if provider_name == "nemotron":
        from .extra_providers import NemotronProvider

        if not api_key:
            raise RuntimeError(
                "Nemotron is a BYOK-only provider — add your key in Settings → API Keys."
            )
        return NemotronProvider(api_key)

    raise ValueError(
        f"Unknown LLM provider: {provider_name!r}. "
        "Valid options: 'gemini', 'claude', 'openai', 'mistral', 'groq', "
        "'cohere', 'xai', 'deepseek', 'together', 'nemotron'."
    )


async def get_patch_provider_for_user(
    user_id: str,
    preferred_provider: str | None = None,
) -> PatchProvider:
    """
    BYOK-aware provider factory.

    Looks up the user's stored API key for the requested provider. If found,
    decrypts it and instantiates the BYOK provider. If not found, falls back
    to the platform's hosted Gemini key.

    Args:
        user_id:            UUID string of the authenticated user.
        preferred_provider: Provider name to try first. Falls back to 'gemini'.
    """
    import uuid as uuid_module

    from sqlalchemy import select

    from config import settings
    from db.models import UserApiKey
    from db.session import AsyncSessionLocal
    from services.crypto import decrypt_key

    provider_name = (preferred_provider or settings.llm_provider_default).lower().strip()

    try:
        uid = uuid_module.UUID(user_id)
    except (ValueError, AttributeError):
        # Demo operator or invalid — fall back to hosted Gemini
        return get_patch_provider("gemini")

    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(UserApiKey).where(
                UserApiKey.user_id == uid,
                UserApiKey.provider == provider_name,
            )
        )
        row = result.scalar_one_or_none()

        if row is not None:
            plaintext_key = decrypt_key(row.encrypted_key)
            # Update last_used_at
            from datetime import datetime, timezone

            row.last_used_at = datetime.now(timezone.utc)
            await session.commit()
            return get_patch_provider(provider_name, api_key=plaintext_key)

    # No BYOK key — fall back to hosted Gemini (Phase 7.8 requirement)
    return get_patch_provider("gemini")
