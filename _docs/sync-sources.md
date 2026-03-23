# Sync Sources

How to populate `data/contacts.csv` from different directory services.

## Overview

| Source                  | Status     | Command                   | Notes                                |
| ----------------------- | ---------- | ------------------------- | ------------------------------------ |
| Entra ID / Azure AD     | ✅ Ready   | `dbc sync --source entra` | Via Microsoft Graph API + `az login` |
| LDAP / Active Directory | ✅ Ready   | `dbc sync --source ldap`  | Generic LDAP, works with on-prem AD  |
| Entra Connect (hybrid)  | 🔧 Config  | —                         | Cloud sync of on-prem AD             |
| Keycloak                | 💡 Planned | —                         | Via Keycloak REST API                |
| CSV (manual)            | ✅ Always  | —                         | Edit `data/contacts.csv` directly    |

---

## Entra ID / Azure AD

Uses the Microsoft Graph API with `az login` credentials.

```bash
az login
dbc sync --source entra
dbc sync --source entra --department "Engineering"
dbc sync --source entra --interactive   # browser popup instead of CLI cache
```

**Required fields in Entra/AD:**

| Entra field                  | Contact field | Notes                                   |
| ---------------------------- | ------------- | --------------------------------------- |
| `displayName`                | `name`        | Required                                |
| `mail` / `userPrincipalName` | `email`       | Required                                |
| `jobTitle`                   | `title`       | Filters out service accounts if missing |
| `department`                 | `department`  |                                         |
| `businessPhones[0]`          | `phone`       |                                         |
| `mobilePhone`                | `mobile`      |                                         |
| `manager.displayName`        | `manager`     | Resolved to short ID                    |

---

## Entra Connect (Hybrid — on-prem AD synced to Entra)

If your org uses Entra Connect to sync on-prem AD to Entra ID, the `entra` source works
**if** the relevant fields are included in the sync scope.

**Commonly missing fields** (disabled by default in Entra Connect):

| AD attribute             | Enable in                         | Notes                              |
| ------------------------ | --------------------------------- | ---------------------------------- |
| `mobile` / `mobilePhone` | Entra Connect attribute filtering | Opt-in per attribute               |
| `telephoneNumber`        | Entra Connect attribute filtering |                                    |
| `department`             | Usually synced by default         | Verify in Entra Connect wizard     |
| `manager`                | Usually synced by default         | Requires manager to also be synced |

**To enable missing attributes in Entra Connect:**

1. Open **Microsoft Entra Connect** on the sync server
2. → **Customize synchronization options**
3. → **Optional features** → enable **Directory extension attribute sync** if needed
4. → **Attribute filtering** → select the object type (User) → enable missing attributes
5. Run a full sync: `Start-ADSyncSyncCycle -PolicyType Initial`

If Entra Connect is not an option, use `--source ldap` to read directly from on-prem AD.

---

## LDAP / Active Directory (on-prem)

Reads directly via LDAP/LDAPS — no cloud dependency.
Works with Microsoft AD, OpenLDAP, and any RFC 4511-compliant directory.

```bash
# Configure in .env (copy from .env.example)
LDAP_URL=ldap://dc.example.com
LDAP_BIND_DN=CN=svc-dbc,OU=ServiceAccounts,DC=example,DC=com
LDAP_BIND_PASSWORD=secret
LDAP_BASE_DN=DC=example,DC=com

dbc sync --source ldap
dbc sync --source ldap --department "Engineering"
```

**LDAP → Contact field mapping:**

| LDAP attribute            | Contact field               |
| ------------------------- | --------------------------- |
| `displayName`             | `name`                      |
| `mail`                    | `email`                     |
| `title`                   | `title`                     |
| `department`              | `department`                |
| `telephoneNumber`         | `phone`                     |
| `mobile`                  | `mobile`                    |
| `manager` (DN → resolved) | `manager`                   |
| `company`                 | `company`                   |
| `userAccountControl`      | `active` (bit 2 = disabled) |

**For LDAPS (TLS, port 636):**

```env
LDAP_URL=ldaps://dc.example.com
```

**Service account minimum permissions:** Read access to the user OU — no write permissions needed.

---

## Keycloak (planned)

Keycloak exposes users via its REST Admin API. Would map naturally to the Contact model.
No implementation yet — contributions welcome.

```bash
# Future
dbc sync --source keycloak --url https://keycloak.example.com --realm my-realm
```

---

## Testing with a local LDAP server

A Docker Compose setup with OpenLDAP pre-loaded with mock contacts is provided:

```bash
docker compose -f docker-compose.ldap.yml up -d
dbc sync --source ldap   # uses LDAP_URL=ldap://localhost from .env.ldap.example
docker compose -f docker-compose.ldap.yml down
```

See [docker-compose.ldap.yml](../docker-compose.ldap.yml) and [.env.ldap.example](../.env.ldap.example).
