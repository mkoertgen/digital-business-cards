# digital-business-cards

> CLI tool to sync contacts from Entra ID / LDAP and generate vCards, QR codes, Markdown cards, and org charts.

## Stack

- **Language**: Python ≥ 3.11
- **Package Manager**: uv
- **CLI Framework**: Click
- **Directory sources**: Azure AD via Microsoft Graph (`azure-identity`), LDAP (`ldap3`)
- **Output**: vCard 3.0 (`vobject`), QR codes (`segno`), Markdown cards, org chart HTML/JSON
- **Config**: python-dotenv (`.env.ldap`, `.env.entra`, or `.env`)

## Terminal Environment

**Windows PowerShell 5.1** — use `;` not `&&`

## Commands

```powershell
uv sync                                   # Install dependencies
uv run dbc --help                         # CLI help
uv run dbc sync --source ldap             # Sync from LDAP
uv run dbc sync --source entra            # Sync from Entra ID
uv run dbc generate-all                   # Generate cards for all contacts
uv run dbc generate MKo                   # Generate card for one contact
uv run dbc orgchart                       # Generate org chart
uv run pytest                             # Run tests
```

## Structure

| Path                   | Purpose                                          |
| ---------------------- | ------------------------------------------------ |
| `src/models.py`        | Shared data models (`Contact`, `QRConfig`)       |
| `src/storage.py`       | CSV contact persistence                          |
| `src/cli.py`           | Click CLI entry point                            |
| `src/sync/azure.py`    | Entra ID / Microsoft Graph sync                  |
| `src/sync/ldap.py`     | LDAP / Active Directory sync                     |
| `src/cards/vcard.py`   | vCard 3.0 generator                              |
| `src/cards/qr.py`      | QR code generator (segno)                        |
| `src/cards/avatar.py`  | Avatar resolver (Gravatar, LDAP jpegPhoto)       |
| `src/cards/md_card.py` | Markdown card renderer (Pandoc-compatible)       |
| `src/chart/`           | Org chart generation (graph, renderers)          |
| `data/contacts.csv`    | Synced contacts (gitignored in sensitive setups) |
| `data/output/`         | Generated cards (VCF, QR PNG, MD)                |

## Working Rules

### Code Principles (DRY · KISS · SOLID)

- **DRY**: Extract shared logic into helpers; no copy-paste across commands.
- **KISS**: Prefer stdlib + existing deps over new dependencies. No magic, no overengineering.
- **SOLID / Single Responsibility**: One module, one concern. `sync/` = fetch; `cards/` = render; `chart/` = visualize.

### Git

- **Conventional Commits**: `feat:`, `fix:`, `chore:`, `refactor:`, `docs:`, `ci:`, `test:`
- `git pull --rebase` always (never merge commits on `main`)
- Feature work on short-lived branches (`feat/<name>`), squash-merge to `main`

### Always include

- `.editorconfig` — LF, indent 2, UTF-8
- `.gitattributes` — `* text=auto eol=lf`, binary files flagged

### CI

- CI jobs are 1-liners reproducible locally (no logic in YAML)
- `uv run` for all Python invocations in CI

### Data & Sensitivity

- Contact data in `data/` is **not committed** unless it is mock/test data
- `.env.*` files are **always gitignored**; use `.env.example` for documentation
- This is a **public** repo — no real email addresses, credentials, or company-internal data in source

## Cross-repo

Working rules (git, editorconfig, gitattributes, code principles) are intentionally kept in sync
across `mkoertgen/*` repos. Candidate for a shared global skill — see
[ADR-0001](https://github.com/mkoertgen/...) in `colenio-infra`.
