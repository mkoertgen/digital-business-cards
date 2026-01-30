"""Contact storage and CSV management."""

import csv
import logging
from pathlib import Path

from src.models import Contact

logger = logging.getLogger(__name__)


class ContactStorage:
    """Manage contact storage in CSV format."""
    
    def __init__(self, csv_path: Path = Path("data/contacts.csv")):
        """
        Initialize contact storage.
        
        Args:
            csv_path: Path to contacts CSV file
        """
        self.csv_path = csv_path
    
    def save(self, contacts: list[Contact]) -> None:
        """
        Save contacts to CSV.
        
        Args:
            contacts: List of Contact objects
        """
        if not contacts:
            logger.warning("No contacts to save")
            return
        
        self.csv_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Get field names from first contact
        fieldnames = list(contacts[0].model_dump().keys())
        
        # Sort contacts by ID
        contacts_sorted = sorted(contacts, key=lambda c: c.id)
        
        # Write CSV
        with open(self.csv_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for contact in contacts_sorted:
                # Convert None to empty string for CSV
                row = {k: (v if v is not None else '') for k, v in contact.model_dump().items()}
                writer.writerow(row)
        
        logger.info(f"Saved {len(contacts)} contacts to {self.csv_path}")
    
    def load(self) -> list[Contact]:
        """
        Load contacts from CSV.
        
        Returns:
            List of Contact objects
        """
        if not self.csv_path.exists():
            logger.warning(f"CSV not found: {self.csv_path}")
            return []
        
        contacts = []
        with open(self.csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    # Convert empty strings to None for Optional fields
                    cleaned_row = {k: (None if v == '' else v) for k, v in row.items()}
                    contact = Contact(**cleaned_row)
                    contacts.append(contact)
                except Exception as e:
                    logger.warning(f"Failed to parse contact {row.get('id')}: {e}")
        
        logger.info(f"Loaded {len(contacts)} contacts from {self.csv_path}")
        return contacts
    
    def get(self, contact_id: str) -> Contact | None:
        """
        Get single contact by ID.
        
        Args:
            contact_id: Contact ID
            
        Returns:
            Contact object or None if not found
        """
        contacts = self.load()
        for contact in contacts:
            if contact.id == contact_id:
                return contact
        return None
