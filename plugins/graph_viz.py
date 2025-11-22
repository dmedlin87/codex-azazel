from typing import Dict, List, Any, Optional
from bce.hooks import HookPoint, hook, HookRegistry
from bce.plugins import Plugin

class Plugin(Plugin):
    name = "graph_viz"
    version = "0.1.0"
    description = "Generates Mermaid diagrams for conflict and relationship visualization"

    def activate(self):
        
        @hook(HookPoint.DOSSIER_EXPORT_MARKDOWN)
        def append_mermaid_graphs(ctx):
            """Append visualization graphs to the markdown export"""
            lines = ctx.data
            dossier = ctx.metadata.get("dossier", {})
            
            # Generate Relationship Graph
            rel_graph = self._generate_relationship_graph(dossier)
            if rel_graph:
                lines.append("")
                lines.append("## Relationship Graph")
                lines.append("```mermaid")
                lines.append(rel_graph)
                lines.append("```")
                
            # Generate Conflict Graph
            conflict_graph = self._generate_conflict_graph(dossier)
            if conflict_graph:
                lines.append("")
                lines.append("## Conflict Visualization")
                lines.append("```mermaid")
                lines.append(conflict_graph)
                lines.append("```")
                
            ctx.data = lines
            return ctx

        self.viz_hook = append_mermaid_graphs

    def deactivate(self):
        if hasattr(self, "viz_hook"):
            HookRegistry.unregister(HookPoint.DOSSIER_EXPORT_MARKDOWN, self.viz_hook)

    def _generate_relationship_graph(self, dossier: Dict[str, Any]) -> Optional[str]:
        """Generate a Mermaid flowchart for relationships."""
        relationships = dossier.get("relationships", [])
        if not relationships:
            return None
            
        char_id = dossier.get("id", "center")
        canonical_name = dossier.get("canonical_name", char_id)
        
        # Sanitize ID for mermaid
        def sanitize(s):
            return str(s).replace(" ", "_").replace("-", "_").replace("'", "")
            
        center_node = sanitize(char_id)
        
        lines = ["graph LR"]
        lines.append(f"    {center_node}[{canonical_name}]")
        lines.append(f"    style {center_node} fill:#f9f,stroke:#333,stroke-width:4px")
        
        for rel in relationships:
            target_id = rel.get("character_id") or rel.get("target_id")
            if not target_id:
                continue
                
            target_name = rel.get("target_name", target_id)
            rel_type = rel.get("type", "related")
            
            t_node = sanitize(target_id)
            lines.append(f"    {center_node} -- {rel_type} --> {t_node}({target_name})")
            
        return "\n".join(lines)

    def _generate_conflict_graph(self, dossier: Dict[str, Any]) -> Optional[str]:
        """Generate a Mermaid graph for trait conflicts."""
        conflicts = dossier.get("trait_conflict_summaries", {})
        if not conflicts:
            return None
            
        lines = ["graph TD"]
        
        # Limit to top 5 most severe conflicts to avoid clutter
        sorted_conflicts = sorted(
            conflicts.items(), 
            key=lambda x: {"critical": 3, "high": 2, "medium": 1, "low": 0}.get(x[1].get("severity"), 0),
            reverse=True
        )[:5]
        
        for trait, meta in sorted_conflicts:
            trait_id = f"T_{trait.replace(' ', '_')}"
            severity = meta.get("severity", "low")
            
            # Style based on severity
            color = "#fff"
            if severity == "critical": color = "#ff9999" # Red
            elif severity == "high": color = "#ffcc99"   # Orange
            elif severity == "medium": color = "#ffff99" # Yellow
            
            lines.append(f"    {trait_id}[{trait.upper()}]")
            lines.append(f"    style {trait_id} fill:{color},stroke:#333")
            
            # Add source nodes
            sources = meta.get("sources", {})
            for src, val in sources.items():
                src_id = f"{trait_id}_{src.replace(' ', '_')}"
                # Truncate value for display
                display_val = (val[:20] + '...') if len(val) > 20 else val
                display_val = display_val.replace('"', "'")
                
                lines.append(f"    {trait_id} --- {src_id}({src}: {display_val})")
                
        return "\n".join(lines)
