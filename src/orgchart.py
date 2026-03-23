"""Organization chart generator from Azure AD hierarchy."""

import logging
from pathlib import Path
from typing import Optional

from src.orgchart_graph import OrgGraph
from src.orgchart_renderers import D3JsonRenderer, D3HtmlRenderer, MermaidRenderer, PlantUMLRenderer
from src.storage import ContactStorage

logger = logging.getLogger(__name__)


class OrgChartGenerator:
    """Generate organization charts from contact hierarchy."""
    
    def __init__(self, storage: ContactStorage):
        """
        Initialize org chart generator.
        
        Args:
            storage: Contact storage instance
        """
        self.storage = storage
        self.renderers = {
            'd3': D3JsonRenderer(),
            'd3-html': D3HtmlRenderer(),
            'mermaid': MermaidRenderer(),
            'puml': PlantUMLRenderer(),
        }
    
    def export(
        self,
        format: str = "d3-html",
        output_file: Optional[Path] = None,
        department: Optional[str] = None,
        root_id: Optional[str] = None
    ) -> str:
        """
        Export org chart to file or return as string.
        
        Args:
            format: Output format (d3/d3-html)
            output_file: Output file path (optional)
            department: Filter by department
            root_id: Start from specific contact
            
        Returns:
            Generated diagram as string
        """
        format_lower = format.lower()
        
        contacts = self.storage.load()
        graph = OrgGraph.build_from_contacts(contacts)
        
        if format_lower in ["d3", "json"]:
            diagram = self.renderers['d3'].render(graph, department, root_id)
        elif format_lower in ["d3-html", "html"]:
            diagram = self.renderers['d3-html'].render(graph, department, root_id)
        elif format_lower in ["mermaid", "mmd"]:
            diagram = self.renderers['mermaid'].render(graph, department, root_id)
        elif format_lower in ["puml", "plantuml"]:
            diagram = self.renderers['puml'].render(graph, department, root_id)
        else:
            raise ValueError(f"Unsupported format: {format}. Use: d3, d3-html, mermaid, puml")
        
        if output_file:
            output_file.parent.mkdir(parents=True, exist_ok=True)
            output_file.write_text(diagram, encoding='utf-8')
            logger.info(f"Exported {format} diagram to {output_file}")
        
        return diagram
