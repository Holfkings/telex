"""
Change extractor — uses Gemini to parse a changelog and extract structured
breaking changes from a package version bump.
"""

import json
import logging
import re

logger = logging.getLogger(__name__)

# Change types that are always considered semantically risky regardless of confidence.
_ALWAYS_SEMANTIC: frozenset[str] = frozenset({"behavior_change"})

# Change types that are only risky when the model itself is uncertain (confidence < threshold).
_UNCERTAIN_SEMANTIC: frozenset[str] = frozenset({"signature_change", "deprecated"})

_CONFIDENCE_THRESHOLD = 0.75


def classify_risk(change_type: str, confidence: float) -> bool:
    """
    Derive a boolean semantic-risk flag from the Gemini classifier output.

    Returns True if:
    - change_type is "behavior_change" (always risky — passing tests don't
      guarantee old behavior is preserved), OR
    - change_type is "signature_change" or "deprecated" AND confidence < 0.75
      (the model itself is not sure it is purely mechanical).

    Returns False for "removed", "renamed", or high-confidence mechanical changes.

    This is a pure function with no I/O — unit-test friendly.
    """
    if change_type in _ALWAYS_SEMANTIC:
        return True
    if change_type in _UNCERTAIN_SEMANTIC and confidence < _CONFIDENCE_THRESHOLD:
        return True
    return False


EXTRACT_PROMPT = """You are analyzing a package changelog to extract breaking API changes.

PACKAGE: {package_name}
OLD VERSION: {old_version}
NEW VERSION: {new_version}

CHANGELOG:
{changelog}

Extract every breaking API change. For each one, return a JSON object with these fields:
- change_type: one of "signature_change" | "removed" | "renamed" | "deprecated" | "behavior_change"
- symbol_old: the exact old function/method/class name (e.g. "createCompletion")
- symbol_new: the new name if renamed, otherwise null
- description: one sentence describing the change
- confidence: a float 0.0-1.0 indicating how confident you are this is a real breaking change

Return a JSON array of these objects. If there are no breaking changes, return [].
Do not include any other text or explanation outside the JSON array."""


async def extract_breaking_changes(
    package_name: str,
    old_version: str,
    new_version: str,
    changelog: str,
) -> list[dict]:
    """
    Feed changelog text to Gemini and get back structured detected_changes rows.
    """

    from google import genai  # type: ignore[import]
    from google.genai import types as genai_types  # type: ignore[import]

    from config import settings

    client = genai.Client(
        api_key=settings.gemini_api_key,
        http_options=genai_types.HttpOptions(timeout=30000),
    )

    prompt = EXTRACT_PROMPT.format(
        package_name=package_name,
        old_version=old_version,
        new_version=new_version,
        changelog=changelog[:8000],  # guard against huge changelogs
    )

    # Transport and parse errors propagate — let the worker retry.
    response = await client.aio.models.generate_content(
        model="gemini-2.0-flash",
        contents=prompt,
    )
    raw = response.text
    if raw is None:
        raise ValueError(
            "extract_breaking_changes: model returned no text (content may have been blocked)"
        )
    raw = raw.strip()

    # Strip markdown fences if present
    fenced = re.search(r"```(?:json)?\s*\n(.*?)```", raw, re.DOTALL)
    if fenced:
        raw = fenced.group(1).strip()

    changes = json.loads(raw)
    if not isinstance(changes, list):
        raise ValueError(f"extract_breaking_changes: expected list, got {type(changes)}")

    return changes
