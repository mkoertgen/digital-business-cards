"""CLI for digital business card generation."""

import logging
from pathlib import Path

import click

from .azure_sync import AzureContactSync
from .models import Contact, QRConfig
from .qr_generator import QRCodeGenerator
from .storage import ContactStorage
from .vcard import VCardGenerator

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
@click.option('--department', '-d', default=None,
              help='Filter by department (e.g., "Engineering")')
@click.option('--interactive', is_flag=True,
              help='Use browser authentication (vs. az login cache)')
@click.option('--dry-run', is_flag=True,
              help='Preview without saving')
def sync(department: str | None, interactive: bool, dry_run: bool) -> None:
    """
    Sync contacts from Azure AD/Entra.
    
    By default, uses cached Azure CLI tokens (from `az login`).
    If no cached tokens exist and --interactive is set, opens browser.
    
    Examples:
      dbc sync                    # Use az login cache
      dbc sync --interactive       # Open browser if needed
      dbc sync --department "Engineering"  # Filter by dept
    """
    try:
        # Sync from Azure
        click.echo("🔍 Connecting to Azure AD...")
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
def generate_all(output: str, format: str, size: int) -> None:
    """
    Generate QR codes for all contacts.
    
    Creates both VCF files and QR code images for each contact.
    
    Examples:
      dbc generate-all
      dbc generate-all --output ./cards
      dbc generate-all --format svg --size 512
    """
    output_dir = Path(output)
    
    try:
        # Load contacts
        storage = ContactStorage()
        contacts = storage.load()
        
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


if __name__ == '__main__':
    cli()
