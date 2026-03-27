# Org Chart: Alternatives Considered

## Context

`digital-business-cards` includes an org chart renderer (`dbc orgchart`) that generates interactive HTML, Mermaid, and PlantUML output from synced contact data (Entra or LDAP).

Two established SharePoint alternatives were evaluated:

- [`react-organization-chart`](https://github.com/pnp/sp-dev-fx-webparts/tree/main/samples/react-organization-chart) — PnP SPFx web part (classic)
- [`react-modern-organization-chart`](https://github.com/pnp/sp-dev-fx-webparts/blob/main/samples/react-modern-organization-chart/README.md) — PnP SPFx web part with presence status

## Comparison

| Criterion                                       | `digital-business-cards` | PnP react-organization-chart        | PnP react-modern-organization-chart |
| ----------------------------------------------- | ------------------------ | ----------------------------------- | ----------------------------------- |
| LDAP / AD on-prem                               | ✅                       | ✗                                   | ✗                                   |
| Requires SharePoint                             | ✗                        | ✅ (required)                       | ✅ (Online only)                    |
| Static export (HTML / SVG / Mermaid / PlantUML) | ✅                       | ✗                                   | ✗                                   |
| QR codes + vCards                               | ✅                       | ✗                                   | ✗                                   |
| Interactive tree navigation in browser          | ✅ (d3-org-chart)        | ✅                                  | ✅                                  |
| Live presence status (online/away/offline)      | ✗                        | ✗                                   | ✅ (Graph `presence.Read.All`)      |
| Build complexity                                | Low (uv / Python)        | High (SPFx, Node, Gulp, AppCatalog) | High                                |
| SharePoint Online only                          | ✗                        | ✗                                   | ✅                                  |
| Self-hosted / portable                          | ✅                       | ✗                                   | ✗                                   |

## Decision

The PnP web parts are a good fit when SharePoint Online is already the platform and no custom deployment is desired.
For this project the PnP alternatives were **not adopted** because:

1. **Hard SharePoint dependency** — the web parts cannot run outside a SharePoint Online or 2019 tenant. This project targets environments without SharePoint (LDAP on-prem, standalone deployments).
2. **No LDAP support** — both PnP samples source exclusively from Microsoft Graph. The LDAP/AD sync path is a primary use case here.
3. **No export** — neither web part produces portable artefacts (HTML file, Mermaid diagram, PlantUML). The static export is used for documentation, presentations, and offline distribution.
4. **Build overhead** — SPFx requires Node.js, Gulp, and AppCatalog deployment; this project intentionally keeps the toolchain to Python + uv.

## Potential Complement

The presence status feature of `react-modern-organization-chart` (Graph `/presence/getPresencesByUserId`) could be added to the D3-HTML renderer without adopting SPFx. This is tracked as a potential enhancement, not a current requirement.
