"""Organization chart graph data structure."""

from dataclasses import dataclass, field
from typing import Optional

from src.models import Contact


@dataclass
class OrgNode:
    """Node in organization chart."""
    contact: Contact
    department: str  # Resolved department (with GF override)
    reports: list['OrgNode'] = field(default_factory=list)


@dataclass
class OrgGraph:
    """Organization chart graph structure."""
    nodes: dict[str, OrgNode]  # contact_id -> OrgNode
    hierarchy: dict[str, list[Contact]]  # manager_id -> reports
    departments: dict[str, list[Contact]]  # department -> contacts
    roots: list[OrgNode]  # Top-level nodes
    
    @classmethod
    def build_from_contacts(cls, contacts: list[Contact]) -> 'OrgGraph':
        """
        Build organization graph from contacts.
        
        Args:
            contacts: List of contacts
            
        Returns:
            OrgGraph instance
        """
        # Filter out contacts without title or department (service accounts, etc.)
        contacts = [c for c in contacts if c.title or c.department]
        
        # Build hierarchy map
        hierarchy = {}
        for contact in contacts:
            if contact.manager:
                if contact.manager not in hierarchy:
                    hierarchy[contact.manager] = []
                hierarchy[contact.manager].append(contact)
        
        # Resolve departments (with GF override)
        def resolve_dept(contact: Contact) -> str:
            if contact.title and "Geschäftsführer" in contact.title:
                return "Geschäftsführung"
            return contact.department or "Keine Abteilung"
        
        # Group by department
        departments = {}
        for contact in contacts:
            dept = resolve_dept(contact)
            if dept not in departments:
                departments[dept] = []
            departments[dept].append(contact)
        
        # Create nodes
        nodes = {}
        for contact in contacts:
            dept = resolve_dept(contact)
            nodes[contact.id] = OrgNode(contact=contact, department=dept)
        
        # Link reports
        for manager_id, reports in hierarchy.items():
            if manager_id in nodes:
                nodes[manager_id].reports = [nodes[r.id] for r in reports if r.id in nodes]
        
        # Find roots
        contact_ids = {c.id for c in contacts}
        roots = []
        for contact in contacts:
            if not contact.manager or contact.manager not in contact_ids:
                roots.append(nodes[contact.id])
        
        # If no roots (circular), pick managers
        if not roots:
            roots = [nodes[c.id] for c in contacts if c.id in hierarchy]
        
        return cls(
            nodes=nodes,
            hierarchy=hierarchy,
            departments=departments,
            roots=roots
        )
