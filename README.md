# Digital Business Cards

Generate QR codes for digital business cards from Azure AD/Entra contacts.

## Features

- 🔄 Sync contacts from Azure AD/Entra (reuses `az login` credentials)
- 📇 Generate vCard (VCF) files with contact details
- 📱 Create QR codes containing vCard data
- 📊 Generate organization charts (Mermaid/PlantUML)
- 🎯 Batch generation or individual cards
- 🖼️ Export as PNG or SVG

## Quick Start

```bash
# Install uv (recommended)
# See: https://docs.astral.sh/uv/getting-started/installation/

# First-time Azure login
az login

# Sync contacts from Azure AD
uv run dbc sync

# Generate all QR codes
uv run dbc generate-all

# Generate single card
uv run dbc generate MKo
```

> **Recommended**: Use `uv` for automatic dependency management and virtual environment handling.
> Alternatively, you can use `pip install -e .` and run `dbc` directly.

## Commands

### Sync from Azure AD

```bash
# Basic sync (uses az login cache)
uv run dbc sync

# Filter by department
uv run dbc sync --department "Engineering"

# Interactive browser auth (first-time)
uv run dbc sync --interactive

# Preview without saving
uv run dbc sync --dry-run
```

### Generate QR Codes

```bash
# All active contacts
uv run dbc generate-all

# Specific contact by ID
uv run dbc generate MKo

# Custom output directory
uv run dbc generate-all --output ./cards

# SVG format (default: PNG)
uv run dbc generate-all --format svg

# Larger QR code
uv run dbc generate-all --size 512
```

### List Contacts

```bash
uv run dbc list
uv run dbc list --verbose
```

### Organization Chart

```bash
# Generate PlantUML diagram (stdout, default)
uv run dbc orgchart

# Export to file
uv run dbc orgchart --output org.puml

# Mermaid format
uv run dbc orgchart --format mermaid --output org.md

# Filter by department
uv run dbc orgchart --department "Engineering"

# Start from specific person
uv run dbc orgchart --root MKo
```

**PlantUML features:**

- Orthogonal (rectangular) arrows for clean layouts
- Department containers for visual grouping
- Better bin-packing of organizational units
- `.puml` files can be rendered with PlantUML tools/plugins

## Output Structure

```
data/
├── contacts.csv          # Synced from Azure AD
└── output/
    ├── MKo.vcf          # vCard files
    ├── MKo.png          # QR codes (PNG)
    └── MKo.svg          # QR codes (SVG)
```

## Requirements

- Python 3.11+
- Azure CLI (`az login` for authentication)
- Azure AD read permissions

## License

MIT License - see [LICENSE](LICENSE)
