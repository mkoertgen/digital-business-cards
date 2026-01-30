# Digital Business Cards

Generate QR codes for digital business cards from Azure AD/Entra contacts.

## Features

- 🔄 Sync contacts from Azure AD/Entra (reuses `az login` credentials)
- 📇 Generate vCard (VCF) files with contact details
- 📱 Create QR codes containing vCard data
- 🎯 Batch generation or individual cards
- 🖼️ Export as PNG or SVG

## Quick Start

```bash
# Install dependencies
pip install -e .

# First-time Azure login
az login

# Sync contacts from Azure AD
python dbc.py sync

# Generate all QR codes
python dbc.py generate-all

# Generate single card
python dbc.py generate MKo
```

## Commands

### Sync from Azure AD

```bash
# Basic sync (uses az login cache)
python dbc.py sync

# Filter by department
python dbc.py sync --department "Engineering"

# Interactive browser auth (first-time)
python dbc.py sync --interactive

# Preview without saving
python dbc.py sync --dry-run
```

### Generate QR Codes

```bash
# All active contacts
python dbc.py generate-all

# Specific contact by ID
python dbc.py generate MKo

# Custom output directory
python dbc.py generate-all --output ./cards

# SVG format (default: PNG)
python dbc.py generate-all --format svg

# Larger QR code
python dbc.py generate-all --size 512
```

### List Contacts

```bash
python dbc.py list
python dbc.py list --verbose
```

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
