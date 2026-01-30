"""QR code generation from vCard data."""

import logging
from pathlib import Path

import segno

from src.models import Contact, QRConfig

logger = logging.getLogger(__name__)


class QRCodeGenerator:
    """Generate QR codes containing vCard data."""
    
    def __init__(self, config: QRConfig = QRConfig()):
        """
        Initialize QR code generator.
        
        Args:
            config: QR generation configuration
        """
        self.config = config
    
    def generate(self, vcard_content: str, output_path: Path) -> Path:
        """
        Generate QR code from vCard content.
        
        Args:
            vcard_content: vCard string content
            output_path: Output file path (with extension)
            
        Returns:
            Path to generated QR code file
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Create QR code using segno (better SVG support than qrcode)
        qr = segno.make(
            vcard_content,
            error=self.config.error_correction,
            boost_error=False
        )
        
        # Save based on format
        if self.config.format.lower() == 'svg':
            qr.save(
                output_path,
                scale=self.config.size // 37,  # Adjust scale for desired size
                border=self.config.border,
                xmldecl=False,
                svgns=False,
                nl=False
            )
        else:  # PNG (default)
            qr.save(
                output_path,
                scale=self.config.size // 37,
                border=self.config.border
            )
        
        logger.debug(f"Saved QR code: {output_path}")
        return output_path
    
    def generate_from_contact(
        self, 
        contact: Contact, 
        vcard_content: str, 
        output_dir: Path
    ) -> tuple[Path, Path]:
        """
        Generate both PNG and VCF QR codes for a contact.
        
        Args:
            contact: Contact object
            vcard_content: vCard string content
            output_dir: Output directory
            
        Returns:
            Tuple of (png_path, svg_path) - svg_path may be None if format is PNG
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate primary format
        ext = self.config.format.lower()
        primary_path = output_dir / f"{contact.id}.{ext}"
        self.generate(vcard_content, primary_path)
        
        return primary_path
