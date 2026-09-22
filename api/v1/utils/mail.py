#!/usr/bin/python
"""Minimal transactional email sender (Resend API) for password-reset codes.
No SDK dependency - just a plain HTTPS POST via the stdlib."""

import json
import logging
import urllib.error
import urllib.request

from config import settings

logger = logging.getLogger(__name__)


def send_reset_token_email(to_email: str, reset_token: str) -> bool:
    """Emails the reset token instead of returning it in an API response.
    Returns False (and logs) if mail isn't configured or the send fails -
    callers should not fail the request just because delivery failed."""
    if not settings.mail_api_key or not settings.mail_from_address:
        logger.warning("mail not configured, cannot deliver reset token by email")
        return False

    payload = json.dumps(
        {
            "from": settings.mail_from_address,
            "to": [to_email],
            "subject": "Wego password reset",
            "text": (
                f"Your password reset code is: {reset_token}\n\n"
                "If you didn't request this, you can ignore this email."
            ),
        }
    ).encode("utf-8")

    req = urllib.request.Request(
        "https://api.resend.com/emails",
        data=payload,
        headers={
            "Authorization": f"Bearer {settings.mail_api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            return 200 <= resp.status < 300
    except urllib.error.URLError:
        logger.exception("failed to send reset token email")
        return False
