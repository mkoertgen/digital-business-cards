"""Azure AD/Entra contact synchronization."""

import logging
import unicodedata
from typing import Optional

from azure.identity import AzureCliCredential, InteractiveBrowserCredential
import requests

from src.models import Contact

logger = logging.getLogger(__name__)


class AzureContactSync:
    """Sync contacts from Azure AD via Microsoft Graph API."""
    
    GRAPH_URL = "https://graph.microsoft.com/v1.0/users"
    SCOPES = ["https://graph.microsoft.com/.default"]
    
    def __init__(self, interactive: bool = False):
        """
        Initialize Azure sync client.
        
        Args:
            interactive: Use browser authentication (vs. az login cache)
        """
        self.credential = self._get_credential(interactive)
    
    def _get_credential(self, interactive: bool):
        """Get Azure credential (CLI or interactive browser)."""
        if interactive:
            logger.info("Using interactive browser authentication")
            return InteractiveBrowserCredential()
        else:
            logger.info("Using Azure CLI credentials (az login)")
            try:
                return AzureCliCredential()
            except Exception as e:
                logger.error(f"Azure CLI auth failed: {e}")
                logger.info("Run 'az login' or use --interactive flag")
                raise
    
    def fetch_contacts(self, department: Optional[str] = None) -> list[Contact]:
        """
        Fetch contacts from Azure AD.
        
        Args:
            department: Filter by department name
            
        Returns:
            List of Contact objects
        """
        logger.info("Fetching contacts from Microsoft Graph...")
        
        # Get access token
        token = self.credential.get_token(*self.SCOPES)
        
        # Query Graph API
        headers = {
            "Authorization": f"Bearer {token.token}",
            "Content-Type": "application/json"
        }
        params = {
            "$filter": "accountEnabled eq true",
            "$select": "id,displayName,mail,userPrincipalName,jobTitle,department,mobilePhone,businessPhones,manager",
            "$expand": "manager($select=id,displayName)",
            "$top": "999"
        }
        
        response = requests.get(self.GRAPH_URL, headers=headers, params=params)
        response.raise_for_status()
        
        users = response.json().get('value', [])
        logger.info(f"Found {len(users)} active users in Azure AD")
        
        # Filter by department
        if department:
            users = [u for u in users if u.get('department') == department]
            logger.info(f"Filtered to {len(users)} users in department '{department}'")
        
        # Filter out service accounts / booking pages (no real users)
        users = [u for u in users if u.get('jobTitle')]
        logger.info(f"Filtered to {len(users)} users with jobTitle (real employees)")
        
        # Convert to Contact models
        contacts = []
        for user in users:
            contact = self._parse_user(user)
            if contact:
                contacts.append(contact)
        
        return contacts
    
    def _parse_user(self, user: dict) -> Optional[Contact]:
        """Convert Azure AD user to Contact model."""
        name = user.get('displayName', '')
        if not name:
            logger.warning(f"Skipping user {user.get('id')} - no displayName")
            return None
        
        # Generate short ID from name (e.g., "Marcel Körtgen" → "MKo")
        contact_id = self._generate_id(name)
        
        # Get email (prefer mail over UPN)
        email = user.get('mail') or user.get('userPrincipalName', '')
        if not email:
            logger.warning(f"Skipping user {name} - no email")
            return None
        
        # Phone numbers
        business_phones = user.get('businessPhones', [])
        phone = business_phones[0] if business_phones else None
        mobile = user.get('mobilePhone')
        
        # Manager
        manager_id = None
        if manager_data := user.get('manager'):
            manager_name = manager_data.get('displayName', '')
            if manager_name:
                manager_id = self._generate_id(manager_name)
        
        return Contact(
            id=contact_id,
            name=name,
            email=email,
            title=user.get('jobTitle'),
            department=user.get('department'),
            phone=phone,
            mobile=mobile,
            manager=manager_id,
            active=True
        )
    
    def _generate_id(self, name: str) -> str:
        """
        Generate short ID from display name.
        
        Heuristic: First letter of first name + first 2 letters of last name
        Example: "Marcel Körtgen" → "MKo"
        
        Args:
            name: Full display name
            
        Returns:
            Short ID (e.g., "MKo")
        """
        # Normalize Unicode (ä→a, ö→o, ü→u)
        name_normalized = unicodedata.normalize('NFKD', name).encode('ASCII', 'ignore').decode('ASCII')
        parts = name_normalized.strip().split()
        
        if len(parts) >= 2:
            first_initial = parts[0][0].upper()
            last_name = parts[-1]
            last_initial = last_name[0].upper()
            last_second = last_name[1].lower() if len(last_name) > 1 else ''
            return first_initial + last_initial + last_second
        else:
            # Fallback: first 3 chars
            return name_normalized[:3].upper()
