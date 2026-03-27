"""CLI for digital business card generation."""

import logging
from pathlib import Path

import click
from dotenv import load_dotenv

from src.azure_sync import AzureContactSync
from src.ldap_sync import LdapContactSync
from src.models import Contact, QRConfig
from src.orgchart import OrgChartGenerator
from src.qr_generator import QRCodeGenerator
from src.storage import ContactStorage
from src.vcard import VCardGenerator

logger = logging.getLogger(__name__)


@click.group()
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose logging')
def cli(verbose: bool) -> None:
    """Digital Business Cards - Generate QR codes from Azure AD contacts."""
    log_level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='%(message)s'
    )


@cli.command()
@click.option('--source', '-s', type=click.Choice(['entra', 'ldap']), default='entra',
              help='Directory source to sync from (default: entra)')
@click.option('--department', '-d', default=None,
              help='Filter by department (e.g., "Engineering")')
@click.option('--interactive', is_flag=True,
              help='Use browser authentication (Entra only, vs. az login cache)')
@click.option('--dry-run', is_flag=True,
              help='Preview without saving')
@click.option('--env-file', 'env_file', default=None, metavar='FILE',
              help='Dotenv file to load (default: .env.<source>, then .env)')
def sync(source: str, department: str | None, interactive: bool, dry_run: bool, env_file: str | None) -> None:
    """
    Sync contacts from a directory service.

    Sources:
      entra  - Azure AD / Entra ID via Microsoft Graph (default)
      ldap   - LDAP / Active Directory (configure via LDAP_* env vars)

    Examples:
      dbc sync                          # Entra via az login
      dbc sync --source ldap            # LDAP via LDAP_URL / LDAP_BIND_DN env
      dbc sync --source entra --interactive
      dbc sync --department "Engineering"
    """
    # Load env file: explicit > .env.<source> > .env
    _env_path = Path(env_file) if env_file else Path(f".env.{source}")
    if not _env_path.exists() and not env_file:
        _env_path = Path(".env")
    if _env_path.exists():
        load_dotenv(_env_path)
        logger.debug(f"Loaded env from {_env_path}")
    elif env_file:
        raise click.UsageError(f"Env file not found: {env_file}")

    try:
        if source == 'ldap':
            click.echo("🔍 Connecting to LDAP...")
            syncer = LdapContactSync()
            contacts = syncer.fetch_contacts(department=department)
        else:
            click.echo("🔍 Connecting to Azure AD / Entra...")
            syncer = AzureContactSync(interactive=interactive)
            contacts = syncer.fetch_contacts(department=department)
        
        if not contacts:
            click.secho("⚠️  No contacts found", fg="yellow")
            return
        
        click.secho(f"✅ Found {len(contacts)} contacts", fg="green")
        
        # Preview
        if dry_run:
            click.secho("\n📋 Would save:", fg="cyan", bold=True)
            for contact in contacts:
                dept = f" | {contact.department}" if contact.department else ""
                click.echo(f"  {contact.id:10} | {contact.name:30} | {contact.email:40}{dept}")
            click.secho("\nℹ️  Use without --dry-run to save", fg="blue")
            return
        
        # Save
        storage = ContactStorage()
        storage.save(contacts)
        
        click.secho(f"\n✅ Synced {len(contacts)} contacts to data/contacts.csv", fg="green", bold=True)
        click.echo("\n📌 Next: dbc generate-all")
        
    except Exception as e:
        click.secho(f"❌ Error: {e}", fg="red")
        raise click.Abort()


@cli.command()
@click.option('--output', '-o', default='data/output',
              help='Output directory for QR codes and VCF files')
@click.option('--format', '-f', type=click.Choice(['png', 'svg']), default='png',
              help='QR code format')
@click.option('--size', '-s', type=int, default=256,
              help='QR code size in pixels')
@click.option('--contacts', '-c', default=None, type=click.Path(exists=True),
              help='Custom contacts CSV (default: data/contacts.csv)')
def generate_all(output: str, format: str, size: int, contacts: str | None) -> None:
    """
    Generate QR codes for all contacts.
    
    Creates both VCF files and QR code images for each contact.
    
    Examples:
      dbc generate-all
      dbc generate-all --output ./cards
      dbc generate-all --format svg --size 512
      dbc generate-all --contacts data/contacts.mock.csv --output data/output-mock
    """
    output_dir = Path(output)
    
    try:
        # Load contacts
        csv_path = Path(contacts) if contacts else Path("data/contacts.csv")
        storage = ContactStorage(csv_path=csv_path)
        contacts_list = storage.load()
        contacts = contacts_list
        
        if not contacts:
            click.secho("❌ No contacts found. Run 'dbc sync' first.", fg="red")
            raise click.Abort()
        
        # Filter active contacts
        active_contacts = [c for c in contacts if c.active]
        click.echo(f"📇 Generating cards for {len(active_contacts)} active contacts...")
        
        # Initialize generators
        vcard_gen = VCardGenerator()
        qr_config = QRConfig(size=size, format=format)
        qr_gen = QRCodeGenerator(qr_config)
        
        # Generate cards
        success_count = 0
        for contact in active_contacts:
            try:
                # Generate VCF
                vcf_path = vcard_gen.save(contact, output_dir)
                
                # Generate QR code
                vcard_content = vcard_gen.generate(contact)
                qr_path = qr_gen.generate_from_contact(contact, vcard_content, output_dir)
                
                click.echo(f"  ✓ {contact.id:10} | {contact.name:30} → {qr_path.name}")
                success_count += 1
                
            except Exception as e:
                click.secho(f"  ✗ {contact.id:10} | {contact.name:30} - Error: {e}", fg="red")
        
        click.secho(f"\n✅ Generated {success_count}/{len(active_contacts)} business cards", fg="green", bold=True)
        click.echo(f"📂 Output: {output_dir.absolute()}")
        
    except Exception as e:
        click.secho(f"❌ Error: {e}", fg="red")
        raise click.Abort()


@cli.command()
@click.argument('contact_id')
@click.option('--output', '-o', default='data/output',
              help='Output directory for QR code and VCF file')
@click.option('--format', '-f', type=click.Choice(['png', 'svg']), default='png',
              help='QR code format')
@click.option('--size', '-s', type=int, default=256,
              help='QR code size in pixels')
def generate(contact_id: str, output: str, format: str, size: int) -> None:
    """
    Generate QR code for a specific contact.
    
    Examples:
      dbc generate MKo
      dbc generate MKo --format svg
      dbc generate MKo --output ./my-card
    """
    output_dir = Path(output)
    
    try:
        # Load contact
        storage = ContactStorage()
        contact = storage.get(contact_id)
        
        if not contact:
            click.secho(f"❌ Contact '{contact_id}' not found", fg="red")
            click.echo("💡 Run 'dbc list' to see all contacts")
            raise click.Abort()
        
        if not contact.active:
            click.secho(f"⚠️  Contact '{contact_id}' is inactive", fg="yellow")
        
        # Generate
        click.echo(f"📇 Generating card for {contact.name}...")
        
        vcard_gen = VCardGenerator()
        qr_config = QRConfig(size=size, format=format)
        qr_gen = QRCodeGenerator(qr_config)
        
        # Generate VCF
        vcf_path = vcard_gen.save(contact, output_dir)
        
        # Generate QR code
        vcard_content = vcard_gen.generate(contact)
        qr_path = qr_gen.generate_from_contact(contact, vcard_content, output_dir)
        
        click.secho(f"\n✅ Generated business card", fg="green", bold=True)
        click.echo(f"   VCF: {vcf_path}")
        click.echo(f"   QR:  {qr_path}")
        
    except Exception as e:
        click.secho(f"❌ Error: {e}", fg="red")
        raise click.Abort()


@cli.command()
@click.option('--verbose', '-v', is_flag=True, help='Show detailed information')
def list(verbose: bool) -> None:
    """
    List all contacts.
    
    Examples:
      dbc list
      dbc list --verbose
    """
    try:
        storage = ContactStorage()
        contacts = storage.load()
        
        if not contacts:
            click.secho("❌ No contacts found. Run 'dbc sync' first.", fg="red")
            raise click.Abort()
        
        active_contacts = [c for c in contacts if c.active]
        inactive_contacts = [c for c in contacts if not c.active]
        
        click.secho(f"📇 {len(contacts)} contacts ({len(active_contacts)} active)", fg="cyan", bold=True)
        
        for contact in active_contacts:
            if verbose:
                dept = f" | {contact.department}" if contact.department else ""
                title = f" | {contact.title}" if contact.title else ""
                click.echo(f"  {contact.id:10} | {contact.name:30} | {contact.email:40}{title}{dept}")
            else:
                click.echo(f"  {contact.id:10} | {contact.name:30} | {contact.email}")
        
        if inactive_contacts:
            click.secho(f"\n⚠️  {len(inactive_contacts)} inactive contacts", fg="yellow")
            if verbose:
                for contact in inactive_contacts:
                    click.echo(f"  {contact.id:10} | {contact.name:30} [INACTIVE]")
        
    except Exception as e:
        click.secho(f"❌ Error: {e}", fg="red")
        raise click.Abort()


@cli.command()
@click.option('--format', '-f', type=click.Choice(['d3-html', 'd3', 'mermaid', 'puml']), default='d3-html',
              help='Diagram format (default: d3-html for interactive)')
@click.option('--department', '-d', default=None,
              help='Filter by department')
@click.option('--root', '-r', default=None,
              help='Start from specific contact ID')
@click.option('--output', '-o', default=None, type=click.Path(),
              help='Output file (.html/.json)')
@click.option('--contacts', '-c', default=None, type=click.Path(exists=True),
              help='Custom contacts CSV (default: data/contacts.csv)')
def orgchart(format: str, department: str | None, root: str | None, output: str | None, contacts: str | None) -> None:
    """
    Generate organization chart from contact hierarchy.
    
    Reads manager relationships from synced contacts and generates a diagram.
    
    Formats:
      d3-html  - Interactive web visualization with recording (.html) - RECOMMENDED
      d3       - JSON data for d3-org-chart library (.json)
    
    Examples:
      dbc orgchart                                        # Interactive HTML to stdout
      dbc orgchart --format d3-html -o org.html           # Interactive HTML to file
      dbc orgchart --format d3 -o org.json                # D3 JSON data
      dbc orgchart --department "Engineering"             # Filter by dept
      dbc orgchart --contacts data/contacts.mock.csv      # Use custom CSV
    """
    try:
        csv_path = Path(contacts) if contacts else Path("data/contacts.csv")
        storage = ContactStorage(csv_path=csv_path)
        contacts = storage.load()
        
        if not contacts:
            click.secho("⚠️  No contacts found. Run 'dbc sync' first.", fg="yellow")
            return
        
        # Filter by department
        if department:
            contacts_filtered = [c for c in contacts if c.department == department]
            if not contacts_filtered:
                click.secho(f"⚠️  No contacts in department '{department}'", fg="yellow")
                return
            click.secho(f"📊 Generating {format} diagram for {len(contacts_filtered)} contacts in '{department}'", fg="cyan")
        else:
            click.secho(f"📊 Generating {format} diagram for {len(contacts)} contacts", fg="cyan")
        
        # Auto-detect extension if not provided
        ext_map = {
            'd3': '.json',
            'd3-html': '.html',
            'mermaid': '.md',
            'puml': '.puml',
        }
        if output:
            known_exts = ('.json', '.html', '.md', '.puml')
            if not any(output.endswith(e) for e in known_exts):
                output = output + ext_map.get(format, '.html')
        
        # Generate diagram
        generator = OrgChartGenerator(storage)
        output_path = Path(output) if output else None
        
        diagram = generator.export(
            format=format,
            output_file=output_path,
            department=department,
            root_id=root
        )
        
        # Output
        if output:
            click.secho(f"✅ Exported to {output}", fg="green", bold=True)
        else:
            click.echo("\n" + diagram + "\n")
        
    except Exception as e:
        click.secho(f"❌ Error: {e}", fg="red")
        raise click.Abort()


if __name__ == '__main__':
    cli()
