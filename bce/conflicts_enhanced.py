from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional, Any

class ConflictCategory(str, Enum):
    CHRONOLOGICAL = "chronological"
    GEOGRAPHICAL = "geographical"
    THEOLOGICAL = "theological"
    NARRATIVE = "narrative"
    NUMERICAL = "numerical"
    RELATIONAL = "relational"
    OTHER = "other"

class ConflictSeverity(str, Enum):
    LOW = "low"  # Minor details
    MEDIUM = "medium"  # Significant differences
    HIGH = "high"  # Fundamental contradictions
    CRITICAL = "critical"  # Irreconcilable differences

@dataclass
class EnhancedConflict:
    field: str
    entity_type: str  # "character" or "event"
    category: ConflictCategory
    severity: ConflictSeverity
    sources: Dict[str, str]
    distinct_values: List[str]
    notes: str
    rationale: Optional[str] = None
    implications: Optional[List[str]] = None

class EnhancedConflictDetector:
    """Advanced conflict detection with configurable rules."""

    # Keyword mapping for categories
    CATEGORY_KEYWORDS = {
        ConflictCategory.CHRONOLOGICAL: ["date", "year", "time", "when", "order", "timeline", "chronolog", "age", "duration"],
        ConflictCategory.GEOGRAPHICAL: ["place", "location", "city", "region", "where", "route", "travel", "map", "origin"],
        ConflictCategory.THEOLOGICAL: ["divinity", "nature", "salvation", "sin", "miracle", "prophecy", "resurrect", "messiah", "son of god", "christolog"],
        ConflictCategory.NUMERICAL: ["count", "number", "how many", "amount", "distance"],
        ConflictCategory.RELATIONAL: ["father", "mother", "son", "brother", "sister", "spouse", "disciple", "relationship", "kin"],
        ConflictCategory.NARRATIVE: ["event", "story", "happen", "detail", "summary", "description", "action"],
    }

    # Specific fields or traits that imply high/critical severity
    CRITICAL_FIELDS = {
        "resurrection", "divinity", "messianic_status", "death_cause", "empty_tomb"
    }
    
    HIGH_SEVERITY_FIELDS = {
        "birthplace", "parentage", "apostleship", "conversion", "trial_outcome"
    }

    @classmethod
    def classify_category(cls, field_name: str) -> ConflictCategory:
        """Determine conflict category based on field name keywords."""
        field_lower = field_name.lower()
        
        for category, keywords in cls.CATEGORY_KEYWORDS.items():
            for keyword in keywords:
                if keyword in field_lower:
                    return category
        
        return ConflictCategory.OTHER

    @classmethod
    def assess_severity(cls, field_name: str, num_sources: int, num_distinct: int) -> ConflictSeverity:
        """Assess severity based on field importance and degree of disagreement."""
        field_lower = field_name.lower()
        
        # Check predefined rules first
        if any(crit in field_lower for crit in cls.CRITICAL_FIELDS):
            return ConflictSeverity.CRITICAL
            
        if any(high in field_lower for high in cls.HIGH_SEVERITY_FIELDS):
            return ConflictSeverity.HIGH

        # Fallback to structural heuristics
        # If nearly every source says something different, that's high chaos
        if num_sources >= 4 and num_distinct >= 3:
            return ConflictSeverity.HIGH
            
        # If binary disagreement among many sources
        if num_sources >= 3 and num_distinct == 2:
            return ConflictSeverity.MEDIUM
            
        return ConflictSeverity.LOW

    @classmethod
    def analyze_conflict(
        cls, 
        field_name: str, 
        values_by_source: Dict[str, str],
        entity_type: str
    ) -> EnhancedConflict:
        """Analyze a single conflict to produce enriched metadata."""
        
        values = {v for v in values_by_source.values() if v}
        num_sources = len(values_by_source)
        num_distinct = len(values)
        
        category = cls.classify_category(field_name)
        severity = cls.assess_severity(field_name, num_sources, num_distinct)
        
        # Auto-generate rationale
        rationale = f"Disagreement in {category.value} domain regarding {field_name}."
        if severity == ConflictSeverity.CRITICAL:
            rationale += " This touches on core doctrinal or historical identity."
        
        return EnhancedConflict(
            field=field_name,
            entity_type=entity_type,
            category=category,
            severity=severity,
            sources=values_by_source,
            distinct_values=sorted(list(values)),
            notes=f"{num_distinct} variants across {num_sources} sources",
            rationale=rationale
        )
