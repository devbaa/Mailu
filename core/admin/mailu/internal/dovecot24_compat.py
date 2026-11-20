"""Dovecot 2.4 compatibility fields for Mailu 2024.06's legacy Maildir.

The persistent mailbox layout remains /mail/<email> with uid/gid 8 (mail).
These helpers are intentionally opt-in until the full 2.4 service migration
passes integration tests; do not use the sharded layout from master here.
"""

LEGACY_MAIL_UID = 8
LEGACY_MAIL_GID = 8


def userdb_fields(email, quota_bytes):
    """Return 2.4 Lua userdb fields without changing existing mailbox paths."""
    if not isinstance(email, str) or not email or "/" in email or "\x00" in email:
        raise ValueError("Invalid mailbox address")
    if isinstance(quota_bytes, bool) or not isinstance(quota_bytes, int) or quota_bytes < 0:
        raise ValueError("Invalid quota")
    return {
        "uid": LEGACY_MAIL_UID,
        "gid": LEGACY_MAIL_GID,
        "home": f"/mail/{email}",
        "quota_storage_size": str(quota_bytes),
    }
