"""vCard (VCF) generation from contact data."""

import logging
from pathlib import Path

import vobject

from .models import Contact

logger = logging.getLogger(__name__)


class VCardGenerator:
    """Generate vCard files from Contact objects."""
    
    def generate(self, contact: Contact) -> str:
        """
        Generate vCard 3.0 string from contact.
        
        Args:
            contact: Contact object
            
        Returns:
            vCard content as string
        """
        vcard = vobject.vCard()
        
        # Name (N: Last;First)
        first_name, last_name = contact.full_name_parts
        vcard.add('n')
        vcard.n.value = vobject.vcard.Name(family=last_name, given=first_name)
        
        # Formatted Name (FN)
        vcard.add('fn')
        vcard.fn.value = contact.name
        
        # Email
        vcard.add('email')
        vcard.email.value = contact.email
        vcard.email.type_param = 'INTERNET'
        
        # Organization
        if contact.company:
            vcard.add('org')
            vcard.org.value = [contact.company]
        
        # Title
        if contact.title:
            vcard.add('title')
            vcard.title.value = contact.title
        
        # Phone numbers
        if contact.phone:
            tel = vcard.add('tel')
            tel.value = contact.phone
            tel.type_param = 'WORK'
        
        if contact.mobile:
            tel = vcard.add('tel')
            tel.value = contact.mobile
            tel.type_param = 'CELL'
        
        # Department (as NOTE)
        if contact.department:
            vcard.add('note')
            vcard.note.value = f"Department: {contact.department}"
        
        return vcard.serialize()
    
    def save(self, contact: Contact, output_dir: Path) -> Path:
        """
        Generate and save vCard file.
        
        Args:
            contact: Contact object
            output_dir: Output directory path
            
        Returns:
            Path to saved VCF file
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        
        vcf_content = self.generate(contact)
        vcf_path = output_dir / f"{contact.id}.vcf"
        
        vcf_path.write_text(vcf_content, encoding='utf-8')
        logger.debug(f"Saved vCard: {vcf_path}")
        
        return vcf_path
