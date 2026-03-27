# Ideas & Potential Extensions

> Tracked as GitHub issues: <https://github.com/mkoertgen/digital-business-cards/issues?q=label%3Aenhancement>

## Avatar / Photo support

- **Gravatar**: resolve avatar by email hash (`https://gravatar.com/avatar/<md5>`) — zero infrastructure needed
- **Azure AD photo**: fetch via Graph `GET /users/{id}/photo/$value`; embed as base64 in vCard (`PHOTO` property) and QR card HTML
- **LDAP `jpegPhoto`**: standard attribute, already fetchable — just not yet parsed

## Server mode / live directory

- `dbc serve` — lightweight HTTP server (FastAPI or Flask) that syncs on request and renders cards/org-chart live without the CLI sync step
- Read-through cache with configurable TTL; sync triggered by first request or on a schedule
- Useful for intranet deployment: bookmark `/card/MKo` → always up-to-date vCard + QR

## Presence status

- Graph `/presence/getPresencesByUserId` (requires `Presence.Read.All`) for Entra contacts
- Overlay traffic-light badge on org chart node — without adopting SPFx (see [orgchart-alternatives.md](orgchart-alternatives.md))

## vCard enhancements

- `LOGO` / `ORG` fields, social links (`X-SOCIALPROFILE`)
- vCard 4.0 output (currently 3.0)
- NFC tag payload (NDEF/URI) alongside QR

## Export targets

- PDF batch export (one card per page) via `WeasyPrint` or `pikepdf`
- Badge-print layout (e.g. 85×55 mm) for lanyards
- Confluence/SharePoint page export from org chart HTML

## Multi-source merge

- Sync from multiple sources (e.g. Entra + LDAP) and merge by email, deduplicate
- Conflict resolution strategy (source priority, last-write-wins)

## CI integration

- GitHub Actions / ADO pipeline: `dbc sync --dry-run` as a validation step
- Publish generated cards / org chart as pipeline artifact or GitHub Pages
