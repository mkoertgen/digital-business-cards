"""LDAP / Active Directory contact synchronization."""

import logging
import os
import unicodedata
from typing import Optional

from ldap3 import Server, Connection, ALL, ALL_ATTRIBUTES, NTLM, SIMPLE, ANONYMOUS, Tls
from ldap3.core.exceptions import LDAPException
import ssl

from src.models import Contact

logger = logging.getLogger(__name__)

# LDAP attributes to fetch
# Note: 'department' and 'sAMAccountName' are AD-specific; 'ou' / 'o' are standard OpenLDAP fallbacks
LDAP_ATTRIBUTES = [
    "displayName",
    "mail",
    "title",
    "department",     # AD; may be absent in standard OpenLDAP
    "ou",             # OpenLDAP fallback for department
    "telephoneNumber",
    "mobile",
    "manager",
    "company",        # AD; may be absent in standard OpenLDAP
    "o",              # OpenLDAP fallback for company
    "userAccountControl",  # AD-only; absent → default active=True
    "sAMAccountName",      # AD-only; absent → ignored
    "distinguishedName",
]

# userAccountControl bit 1 (0x2) = account disabled
UAC_DISABLED = 0x2


class LdapContactSync:
    """Sync contacts from LDAP / Active Directory."""

    def __init__(
        self,
        url: Optional[str] = None,
        bind_dn: Optional[str] = None,
        bind_password: Optional[str] = None,
        base_dn: Optional[str] = None,
        auth: str = "simple",
    ):
        """
        Initialize LDAP sync client.

        Reads config from environment if not provided:
            LDAP_URL, LDAP_BIND_DN, LDAP_BIND_PASSWORD, LDAP_BASE_DN

        Args:
            url: LDAP URL, e.g. ldap://dc.example.com or ldaps://...
            bind_dn: Bind DN for authentication
            bind_password: Bind password
            base_dn: Search base DN, e.g. DC=example,DC=com
            auth: Authentication type: simple, ntlm, anonymous
        """
        self.url = url or os.environ["LDAP_URL"]
        self.bind_dn = bind_dn or os.environ.get("LDAP_BIND_DN", "")
        self.bind_password = bind_password or os.environ.get("LDAP_BIND_PASSWORD", "")
        self.base_dn = base_dn or os.environ["LDAP_BASE_DN"]
        self.auth = auth

    def _connect(self) -> Connection:
        use_ssl = self.url.lower().startswith("ldaps://")
        tls = Tls(validate=ssl.CERT_NONE) if use_ssl else None
        server = Server(self.url, get_info=ALL, use_ssl=use_ssl, tls=tls)

        if self.auth == "ntlm":
            conn = Connection(server, user=self.bind_dn, password=self.bind_password, authentication=NTLM)
        elif self.auth == "anonymous" or not self.bind_dn:
            conn = Connection(server, authentication=ANONYMOUS)
        else:
            conn = Connection(server, user=self.bind_dn, password=self.bind_password, authentication=SIMPLE)

        if not conn.bind():
            raise LDAPException(f"LDAP bind failed: {conn.result}")
        return conn

    def fetch_contacts(self, department: Optional[str] = None) -> list[Contact]:
        """
        Fetch contacts from LDAP.

        Args:
            department: Filter by department name

        Returns:
            List of Contact objects
        """
        logger.info(f"Connecting to LDAP: {self.url}")
        conn = self._connect()

        # Base filter: persons with email
        # The !(objectClass=computer) exclusion is AD-specific; tolerate absence in plain OpenLDAP
        base_filter = "(&(objectClass=person)(mail=*))"
        if department:
            dept_escaped = department.replace("(", "\\28").replace(")", "\\29")
            search_filter = f"(&{base_filter}(department={dept_escaped}))"
        else:
            search_filter = base_filter

        logger.info(f"Searching: base={self.base_dn}, filter={search_filter}")
        conn.search(
            search_base=self.base_dn,
            search_filter=search_filter,
            attributes=ALL_ATTRIBUTES,  # fetch everything; parse code handles missing attrs
        )

        entries = conn.entries
        logger.info(f"Found {len(entries)} entries in LDAP")

        # Build DN → contact map for manager resolution
        dn_map: dict[str, str] = {}  # DN → short ID
        for entry in entries:
            dn = entry.entry_dn
            name = self._str(entry, "displayName")
            if name:
                dn_map[dn] = self._generate_id(name)

        contacts = []
        for entry in entries:
            contact = self._parse_entry(entry, dn_map)
            if contact:
                contacts.append(contact)

        conn.unbind()
        logger.info(f"Parsed {len(contacts)} contacts from LDAP")
        return contacts

    def _parse_entry(self, entry, dn_map: dict[str, str]) -> Optional[Contact]:
        name = self._str(entry, "displayName")
        if not name:
            return None

        email = self._str(entry, "mail")
        if not email:
            logger.debug(f"Skipping {name} — no mail attribute")
            return None

        # Active: check userAccountControl bit (AD-specific); default active if not present
        uac = self._int(entry, "userAccountControl")
        active = not bool(uac & UAC_DISABLED) if uac is not None else True

        # Manager: resolve DN → short ID
        manager_dn = self._str(entry, "manager")
        manager_id = dn_map.get(manager_dn) if manager_dn else None

        # department: AD uses 'department', standard OpenLDAP uses 'ou'
        department = self._str(entry, "department") or self._str(entry, "ou")

        # company: AD uses 'company', standard OpenLDAP uses 'o'
        company = self._str(entry, "company") or self._str(entry, "o") or ""

        return Contact(
            id=self._generate_id(name),
            name=name,
            email=email,
            title=self._str(entry, "title"),
            department=department,
            phone=self._str(entry, "telephoneNumber"),
            mobile=self._str(entry, "mobile"),
            manager=manager_id,
            company=company,
            active=active,
        )

    @staticmethod
    def _str(entry, attr: str) -> Optional[str]:
        try:
            val = entry[attr].value
            return str(val).strip() if val else None
        except Exception:
            return None

    @staticmethod
    def _int(entry, attr: str) -> Optional[int]:
        try:
            val = entry[attr].value
            return int(val) if val is not None else None
        except Exception:
            return None

    @staticmethod
    def _generate_id(name: str) -> str:
        """Generate short ID from display name (e.g. 'Clara Heinz' → 'CHe')."""
        name_ascii = unicodedata.normalize("NFKD", name).encode("ASCII", "ignore").decode("ASCII")
        parts = name_ascii.strip().split()
        if len(parts) >= 2:
            first = parts[0][0].upper()
            last = parts[-1]
            return first + last[0].upper() + last[1:2].lower()
        return name_ascii[:3].capitalize()
