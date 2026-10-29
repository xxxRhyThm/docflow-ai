"""Optional LLM extraction hook. DISABLED by default in v1.

Design only: this module contains no API key, no network call and no
model invocation. If a future version wires a provider here, it must:
1. read the key from an environment variable only (never hard-coded),
2. label its output extraction_method="llm" (never "rule"),
3. keep rule extraction as the default fallback.

Any code that labels rule output as LLM output would be a defect.
"""

from __future__ import annotations


def llm_extraction_available() -> bool:
    """v1 answer: the LLM path is not wired up, by design."""
    return False


def describe_llm_interface() -> dict:
    return {
        "enabled": False,
        "default_method": "rule",
        "note": (
            "LLM extraction is an optional future extension. "
            "It requires an environment-variable API key and must "
            "label its results as extraction_method='llm'."
        ),
    }
