"""Avatar/photo resolution from multiple sources.

Resolution order per contact:
  1. Local file already present (e.g. from LDAP jpegPhoto saved during sync)
  2. Gravatar (email MD5 hash, 404 if not registered → silently skipped)
"""

import hashlib
import logging
from pathlib import Path
from typing import Optional

import httpx

from src.models import Contact

logger = logging.getLogger(__name__)

GRAVATAR_BASE = "https://gravatar.com/avatar"
GRAVATAR_SIZE = 256


class AvatarResolver:
    """Resolve and cache contact avatar images."""

    def __init__(self, avatar_dir: Path):
        self.avatar_dir = avatar_dir
        self.avatar_dir.mkdir(parents=True, exist_ok=True)

    def save(self, contact: Contact, data: bytes) -> Path:
        """Save raw JPEG bytes (e.g. from LDAP jpegPhoto) and return path."""
        path = self._path(contact)
        path.write_bytes(data)
        logger.debug(f"Saved avatar for {contact.id} ({len(data)} bytes)")
        return path

    def resolve(self, contact: Contact) -> Optional[Path]:
        """
        Return a local path to the avatar image, or None if unavailable.

        Tries local file first, then Gravatar.
        """
        path = self._path(contact)
        if path.exists():
            return path
        return self._fetch_gravatar(contact)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _path(self, contact: Contact) -> Path:
        return self.avatar_dir / f"{contact.id}.jpg"

    def _fetch_gravatar(self, contact: Contact) -> Optional[Path]:
        digest = hashlib.md5(contact.email.strip().lower().encode()).hexdigest()
        url = f"{GRAVATAR_BASE}/{digest}?s={GRAVATAR_SIZE}&d=404"
        try:
            response = httpx.get(url, follow_redirects=True, timeout=5.0)
            if response.status_code == 200:
                path = self._path(contact)
                path.write_bytes(response.content)
                logger.debug(f"Gravatar resolved for {contact.id}")
                return path
            logger.debug(f"No Gravatar for {contact.id} (HTTP {response.status_code})")
        except Exception as e:
            logger.debug(f"Gravatar request failed for {contact.id}: {e}")
        return None
