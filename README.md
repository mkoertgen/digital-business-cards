# Digital Business Cards

Generate QR codes for digital business cards from Azure AD/Entra contacts.

![](_docs/org-chart.png)

> See [\_docs/examples.md](_docs/examples.md) for screenshots, a demo recording, and diagram examples (Mermaid/PlantUML).

## Features

- 🔄 Sync contacts from Azure AD/Entra (reuses `az login` credentials)
- 📇 Generate vCard (VCF) files with contact details
- 📱 Create QR codes containing vCard data
- 📊 Generate interactive org charts (HTML, Mermaid, PlantUML)
- 🎯 Batch generation or individual cards
- 🖼️ Export as PNG or SVG

## Quick Start

```bash
# Install uv: https://docs.astral.sh/uv/getting-started/installation/

az login                 # First-time Azure login
uv run dbc sync          # Sync contacts from Azure AD
uv run dbc generate-all  # Generate all QR codes + vCards
uv run dbc generate MKo  # Single card
uv run dbc orgchart -o org.html  # Interactive org chart
```

## Commands

### Sync

```bash
uv run dbc sync
uv run dbc sync --department "Engineering"
uv run dbc sync --interactive   # browser auth
uv run dbc sync --dry-run
```

### Generate QR Codes

```bash
uv run dbc generate-all
uv run dbc generate-all --output ./cards --format svg --size 512
uv run dbc generate MKo
```

### List Contacts

```bash
uv run dbc list
uv run dbc list --verbose
```

### Organization Chart

```bash
uv run dbc orgchart                              # interactive HTML (default)
uv run dbc orgchart -o org.html                  # save to file
uv run dbc orgchart --format mermaid -o org.md   # Mermaid
uv run dbc orgchart --format puml -o org.puml    # PlantUML
uv run dbc orgchart --department "Engineering"
uv run dbc orgchart --root MKo
```

## Output

```
data/
├── contacts.csv        # Synced from Azure AD
└── output/
    ├── MKo.vcf         # vCard files
    └── MKo.png         # QR codes
```

## Requirements

- Python 3.11+
- Azure CLI (`az login`)
- Azure AD read permissions

## License

MIT License - see [LICENSE](LICENSE)
