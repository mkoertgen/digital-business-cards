"""Organization chart renderers - Strategy pattern."""

import json
from abc import ABC, abstractmethod

from src.orgchart_graph import OrgGraph


class OrgChartRenderer(ABC):
    """Base class for organization chart renderers."""
    
    @abstractmethod
    def render(self, graph: OrgGraph, department: str | None = None, root_id: str | None = None) -> str:
        """
        Render organization chart.
        
        Args:
            graph: Organization graph
            department: Filter by department
            root_id: Start from specific contact
            
        Returns:
            Rendered diagram as string
        """
        pass




class D3JsonRenderer(OrgChartRenderer):
    """D3.js hierarchical JSON renderer for d3-org-chart library."""
    
    def render(self, graph: OrgGraph, department: str | None = None, root_id: str | None = None) -> str:
        """
        Render as D3 hierarchical JSON (flat array with parentId).
        Compatible with d3-org-chart library: https://github.com/bumbeishvili/org-chart
        
        Format:
        [
          {"id": "MAd", "name": "Matthias Adrian", "title": "Geschäftsführer", 
           "department": "Geschäftsführung", "email": "...", "parentId": null},
          {"id": "MKo", "name": "Marcel Körtgen", "title": "Head of Technology",
           "department": "Architecture & Development", "email": "...", "parentId": "MAd"}
        ]
        """
        # Filter nodes
        nodes = list(graph.nodes.values())
        if department:
            nodes = [n for n in nodes if n.department == department]
        
        # Check for multiple roots
        roots = [n for n in nodes if not n.contact.manager]
        needs_virtual_root = len(roots) > 1

        # Derive company name from contacts
        company_name = next((n.contact.company for n in nodes if n.contact.company), "Organization")

        # Build flat array with parentId references
        data = []
        
        # Add virtual root if needed
        if needs_virtual_root:
            data.append({
                "id": "VIRTUAL_ROOT",
                "name": company_name,
                "title": "Organization",
                "department": "",
                "email": "",
                "parentId": None
            })
        
        for node in nodes:
            # Determine parent
            if needs_virtual_root and not node.contact.manager:
                parent_id = "VIRTUAL_ROOT"
            else:
                parent_id = node.contact.manager if node.contact.manager else None
            
            item = {
                "id": node.contact.id,
                "name": node.contact.name,
                "title": node.contact.title or "",
                "department": node.department,
                "email": node.contact.email,
                "parentId": parent_id
            }
            
            # Add optional fields if present
            if node.contact.phone:
                item["phone"] = node.contact.phone
            if node.contact.mobile:
                item["mobile"] = node.contact.mobile
            
            data.append(item)
        
        return json.dumps(data, indent=2, ensure_ascii=False)


class D3HtmlRenderer(OrgChartRenderer):
    """D3.js org chart HTML renderer with embedded visualization."""
    
    def render(self, graph: OrgGraph, department: str | None = None, root_id: str | None = None) -> str:
        """
        Render as standalone HTML with d3-org-chart visualization.
        Uses d3-org-chart library via CDN.
        """
        # Get JSON data
        json_renderer = D3JsonRenderer()
        json_data = json_renderer.render(graph, department, root_id)
        
        # Derive company name from JSON data for title
        raw_nodes = list(graph.nodes.values())
        company_name = next((n.contact.company for n in raw_nodes if n.contact.company), "Organization")

        html = f'''<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Organigramm - {company_name}</title>
    <script src="https://d3js.org/d3.v7.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/d3-flextree@2.1.2/build/d3-flextree.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/d3-org-chart@3"></script>
    <style>
        body {{
            margin: 0;
            padding: 20px;
            font-family: Arial, sans-serif;
            background: #f5f5f5;
        }}
        h1 {{
            text-align: center;
            color: #1976D2;
        }}
        #chart {{
            width: 100%;
            height: 800px;
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }}
        .node-card {{
            background: #E3F2FD;
            border: 2px solid #1976D2;
            border-radius: 8px;
            padding: 12px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .node-name {{
            font-weight: bold;
            font-size: 14px;
            color: #1976D2;
            margin-bottom: 4px;
        }}
        .node-title {{
            font-size: 12px;
            color: #666;
            margin-bottom: 4px;
        }}
        .node-dept {{
            font-size: 11px;
            color: #999;
            font-style: italic;
        }}
        .record-btn {{
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 12px 24px;
            background: #dc3545;
            color: white;
            border: none;
            border-radius: 24px;
            font-size: 14px;
            font-weight: bold;
            cursor: pointer;
            box-shadow: 0 2px 8px rgba(0,0,0,0.2);
            z-index: 1000;
            transition: all 0.3s;
        }}
        .record-btn:hover {{
            background: #c82333;
            box-shadow: 0 4px 12px rgba(0,0,0,0.3);
        }}
        .record-btn.recording {{
            background: #28a745;
            animation: pulse 1.5s infinite;
        }}
        @keyframes pulse {{
            0%, 100% {{ opacity: 1; }}
            50% {{ opacity: 0.7; }}
        }}
    </style>
</head>
<body>
    <button id="recordBtn" class="record-btn" title="Screen Recording starten/stoppen">🎥 Record</button>
    <h1>Organigramm</h1>
    <div id="chart"></div>
    
    <script>
        // Screen Recording functionality
        let mediaRecorder;
        let recordedChunks = [];
        const recordBtn = document.getElementById('recordBtn');

        recordBtn.addEventListener('click', async () => {{
            if (!mediaRecorder || mediaRecorder.state === 'inactive') {{
                try {{
                    const stream = await navigator.mediaDevices.getDisplayMedia({{
                        video: {{ mediaSource: 'screen' }},
                        audio: false
                    }});
                    
                    recordedChunks = [];
                    mediaRecorder = new MediaRecorder(stream, {{ mimeType: 'video/webm' }});
                    
                    mediaRecorder.ondataavailable = (event) => {{
                        if (event.data.size > 0) {{
                            recordedChunks.push(event.data);
                        }}
                    }};
                    
                    mediaRecorder.onstop = () => {{
                        const blob = new Blob(recordedChunks, {{ type: 'video/webm' }});
                        const url = URL.createObjectURL(blob);
                        const a = document.createElement('a');
                        a.href = url;
                        a.download = `orgchart-${{new Date().toISOString().slice(0,10)}}.webm`;
                        a.click();
                        URL.revokeObjectURL(url);
                        
                        stream.getTracks().forEach(track => track.stop());
                        recordBtn.classList.remove('recording');
                        recordBtn.textContent = '🎥 Record';
                    }};
                    
                    mediaRecorder.start();
                    recordBtn.classList.add('recording');
                    recordBtn.textContent = '⏹️ Stop Recording';
                }} catch (err) {{
                    console.error('Recording failed:', err);
                    alert('Screen Recording nicht möglich. Browser-Berechtigung erforderlich.');
                }}
            }} else {{
                mediaRecorder.stop();
            }}
        }});

        const data = {json_data};
        
        // Department color scheme
        const deptColors = {{
            'Geschäftsführung': {{ bg: '#FFE0B2', border: '#FF6F00', text: '#E65100' }},
            'Architecture & Development': {{ bg: '#E3F2FD', border: '#1976D2', text: '#0D47A1' }},
            'Legal & Compliance': {{ bg: '#F3E5F5', border: '#7B1FA2', text: '#4A148C' }},
            '': {{ bg: '#ECEFF1', border: '#546E7A', text: '#263238' }}  // Virtual root
        }};
        
        const chart = new d3.OrgChart()
            .container('#chart')
            .data(data)
            .nodeWidth(d => 180)
            .nodeHeight(d => 80)
            .childrenMargin(d => 50)
            .compactMarginBetween(d => 30)
            .compactMarginPair(d => 50)
            .nodeContent(function(d) {{
                const colors = deptColors[d.data.department] || deptColors[''];
                return `
                    <div class="node-card" style="background: ${{colors.bg}}; border-color: ${{colors.border}};">
                        <div class="node-name" style="color: ${{colors.text}};">${{d.data.name}}</div>
                        <div class="node-title">${{d.data.title}}</div>
                        <div class="node-dept">${{d.data.department}}</div>
                    </div>
                `;
            }})
            .render();
    </script>
</body>
</html>'''
        return html


class MermaidRenderer(OrgChartRenderer):
    """Mermaid graph TD renderer."""

    def render(self, graph: OrgGraph, department: str | None = None, root_id: str | None = None) -> str:
        nodes = list(graph.nodes.values())
        if department:
            nodes = [n for n in nodes if n.department == department]

        node_ids = {n.contact.id for n in nodes}
        lines = ["# Org Chart", "", "```mermaid", "graph TD"]

        for node in nodes:
            label = f"{node.contact.name}\\n{node.contact.title or ''}"
            lines.append(f"    {node.contact.id}[\"{label}\"]")
            if node.contact.manager and node.contact.manager in node_ids:
                lines.append(f"    {node.contact.manager} --> {node.contact.id}")

        lines += ["```", ""]
        return "\n".join(lines)


class PlantUMLRenderer(OrgChartRenderer):
    """PlantUML org chart renderer with department packages."""

    def render(self, graph: OrgGraph, department: str | None = None, root_id: str | None = None) -> str:
        nodes = list(graph.nodes.values())
        if department:
            nodes = [n for n in nodes if n.department == department]

        node_ids = {n.contact.id for n in nodes}

        # Group by department
        by_dept: dict[str, list] = {}
        for node in nodes:
            by_dept.setdefault(node.department, []).append(node)

        lines = [
            "@startuml",
            "skinparam backgroundColor white",
            "skinparam shadowing false",
            "skinparam linetype ortho",
            "skinparam nodesep 60",
            "skinparam ranksep 80",
            "top to bottom direction",
            "",
            "skinparam rectangle {",
            "  BackgroundColor #E3F2FD",
            "  BorderColor #1976D2",
            "  FontStyle bold",
            "  FontSize 11",
            "}",
            "skinparam package {",
            "  BackgroundColor #F5F5F5",
            "  BorderColor #757575",
            "  FontStyle bold",
            "  FontSize 13",
            "}",
            "",
        ]

        pkg_alias = {}
        for i, (dept, members) in enumerate(by_dept.items()):
            alias = f"PKG{i}"
            pkg_alias[dept] = alias
            lines.append(f'package "{dept}" as {alias} {{')
            for node in members:
                title = node.contact.title or ""
                lines.append(f'  rectangle "**{node.contact.name}**\\n{title}" as {node.contact.id}')
            lines.append("}")
            lines.append("")

        # Relationships
        for node in nodes:
            if node.contact.manager and node.contact.manager in node_ids:
                lines.append(f"{node.contact.manager} --> {node.contact.id}")

        lines += ["", "@enduml", ""]
        return "\n".join(lines)
