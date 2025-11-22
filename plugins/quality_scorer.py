from dataclasses import dataclass
from typing import List, Dict, Any
from bce import api
from bce.plugins import Plugin
from bce.hooks import HookRegistry, HookPoint, hook

@dataclass
class QualityScore:
    overall: float  # 0.0-1.0
    dimensions: Dict[str, float]
    recommendations: List[str]
    warnings: List[str]

class QualityScorer:
    """Calculate data quality scores"""

    @staticmethod
    def score_character(char_id: str, dossier: Dict[str, Any] = None) -> QualityScore:
        """Score a character's data quality"""
        char = api.get_character(char_id)

        scores = {}
        recommendations = []
        warnings = []

        # Completeness dimension
        scores["completeness"] = QualityScorer._score_completeness(char)
        if scores["completeness"] < 0.7:
            recommendations.append("Add more source profiles or traits")

        # Consistency dimension
        # Use dossier if available, otherwise we'd have to calculate it
        if dossier and "trait_conflict_summaries" in dossier:
            scores["consistency"] = QualityScorer._score_consistency_from_dossier(dossier)
        else:
            # Fallback if no dossier provided (though usually it is)
            scores["consistency"] = 1.0 # Optimistic fallback
            
        if scores["consistency"] < 0.8:
            warnings.append("Significant data inconsistencies detected across sources")
        if scores["consistency"] < 0.5:
             warnings.append("Critical contradictions found in core identity fields")

        # Reference quality dimension
        scores["reference_quality"] = QualityScorer._score_references(char)
        if scores["reference_quality"] < 0.9:
            recommendations.append("Add more specific scripture references")

        # Tag coverage dimension
        scores["tag_coverage"] = QualityScorer._score_tags(char)
        if scores["tag_coverage"] < 0.6:
            recommendations.append("Add relevant thematic tags")

        # Relationship dimension
        scores["relationship_coverage"] = QualityScorer._score_relationships(char)
        
        # Source diversity dimension
        scores["source_diversity"] = QualityScorer._score_source_diversity(char)
        if scores["source_diversity"] < 0.5:
            recommendations.append("Add profiles from more diverse sources")

        overall = sum(scores.values()) / len(scores) if scores else 0.0

        return QualityScore(
            overall=overall,
            dimensions=scores,
            recommendations=recommendations,
            warnings=warnings
        )

    @staticmethod
    def _score_completeness(char) -> float:
        """0.0-1.0 based on field completeness"""
        score = 0.0
        max_score = 0.0

        # Has name?
        max_score += 10
        if char.canonical_name:
            score += 10

        # Has aliases?
        max_score += 10
        if char.aliases:
            score += min(len(char.aliases) * 5, 10)

        # Has roles?
        max_score += 15
        if char.roles:
            score += min(len(char.roles) * 5, 15)

        # Has tags?
        max_score += 15
        if char.tags:
            score += min(len(char.tags) * 3, 15)

        # Has source profiles?
        max_score += 30
        if char.source_profiles:
            score += min(len(char.source_profiles) * 10, 30)

        # Source profiles have traits?
        max_score += 20
        total_traits = sum(len(sp.traits) for sp in char.source_profiles)
        score += min(total_traits * 2, 20)

        return score / max_score if max_score > 0 else 0.0

    @staticmethod
    def _score_consistency_from_dossier(dossier: Dict[str, Any]) -> float:
        """Calculate consistency based on conflict severity in dossier."""
        conflicts = dossier.get("trait_conflict_summaries", {})
        if not conflicts:
            return 1.0
            
        score = 1.0
        penalty_map = {
            "low": 0.05,
            "medium": 0.1,
            "high": 0.2,
            "critical": 0.3
        }
        
        for conflict_info in conflicts.values():
            severity = conflict_info.get("severity", "low")
            penalty = penalty_map.get(severity, 0.05)
            score -= penalty
            
        return max(0.0, score)

    @staticmethod
    def _score_references(char) -> float:
        """Quality of scripture references"""
        total_refs = sum(len(sp.references) for sp in char.source_profiles)
        if total_refs == 0:
            return 0.0

        # Simple heuristic: assume refs are OK if they exist
        # Cap at 1.0 for > 10 refs
        return min(total_refs / 10.0, 1.0)

    @staticmethod
    def _score_tags(char) -> float:
        """Tag coverage quality"""
        if not char.tags:
            return 0.0
        return min(len(char.tags) / 5.0, 1.0)

    @staticmethod
    def _score_relationships(char) -> float:
        """Relationship coverage"""
        if not hasattr(char, "relationships") or not char.relationships:
            return 0.0
        return min(len(char.relationships) / 3.0, 1.0)

    @staticmethod
    def _score_source_diversity(char) -> float:
        """Diversity of sources"""
        if not char.source_profiles:
            return 0.0

        unique_sources = len(set(sp.source_id for sp in char.source_profiles))
        # Score higher for more diverse sources (gospels, Paul, Acts, etc.)
        return min(unique_sources / 4.0, 1.0)


class Plugin(Plugin):
    name = "quality_scorer"
    version = "1.0.0"
    description = "Automated data quality scoring and enrichment"

    def activate(self):
        """Register hooks when plugin loads"""
        
        @hook(HookPoint.DOSSIER_ENRICH)
        def inject_quality_score(ctx):
            """Add quality score to dossier"""
            dossier = ctx.data
            # Dossier builder passes char_id in metadata or we can infer from context
            # But wait, dossier hook usually passes 'character' in metadata or args
            # Looking at PROPOSED_FEATURES, it says: 
            # ctx = HookRegistry.trigger(HookPoint.DOSSIER_ENRICH, data=dossier, character=character)
            
            # However, we need to check how dossier builder calls this hook.
            # It is not yet implemented in dossier builder.
            # But assuming it will be implemented or we are using this to test the plugin.
            
            # For now, let's handle the case where we have char_id
            # Note: CharacterDossier is flat, containing 'id', 'canonical_name' etc.
            char_id = dossier.get("id")
            if char_id:
                try:
                    # Pass the dossier so we can analyze conflicts
                    score = QualityScorer.score_character(char_id, dossier=dossier)
                    
                    # Add to dossier
                    dossier["quality_score"] = {
                        "overall": score.overall,
                        "dimensions": score.dimensions,
                        "recommendations": score.recommendations,
                        "warnings": score.warnings
                    }
                    
                    ctx.data = dossier
                except Exception as e:
                    # Don't fail build if scoring fails
                    import logging
                    logging.warning(f"Quality scoring failed for {char_id}: {e}")
            
            return ctx

        self.enrich_hook = inject_quality_score
        
    def deactivate(self):
        """Unregister hooks"""
        if hasattr(self, "enrich_hook"):
            HookRegistry.unregister(HookPoint.DOSSIER_ENRICH, self.enrich_hook)
