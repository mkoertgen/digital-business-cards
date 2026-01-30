"""Contact storage and CSV management."""

import logging
from pathlib import Path

import pandas as pd

from .models import Contact

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
        
        # Convert to DataFrame
        df = pd.DataFrame([c.model_dump() for c in contacts])
        
        # Sort by ID
        df = df.sort_values('id')
        
        # Save
        df.to_csv(self.csv_path, index=False, encoding='utf-8')
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
        
        df = pd.read_csv(self.csv_path)
        
        # Convert to Contact objects
        contacts = []
        for _, row in df.iterrows():
            try:
                contact = Contact(**row.to_dict())
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
