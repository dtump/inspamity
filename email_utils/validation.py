from typing import Any


def validate_ai_response(result: dict[str, Any]) -> dict[str, Any]:
    """Ensure AI response has required fields with correct types.

    Returns a normalized dict with is_spam, confidence, and reason.
    Missing or invalid fields are replaced with safe defaults.
    """
    is_spam = result.get("is_spam", "no")
    if is_spam not in ("yes", "no"):
        is_spam = "no"

    confidence = result.get("confidence", 0)
    try:
        confidence = int(confidence)
    except (TypeError, ValueError):
        confidence = 0
    confidence = max(0, min(100, confidence))

    reason = result.get("reason", "No reason provided")
    if not isinstance(reason, str):
        reason = str(reason)

    return {"is_spam": is_spam, "confidence": confidence, "reason": reason}
