import pytest
from bce.conflicts_enhanced import EnhancedConflictDetector, ConflictCategory, ConflictSeverity, EnhancedConflict

def test_classify_category():
    """Test category classification rules."""
    assert EnhancedConflictDetector.classify_category("birth_date") == ConflictCategory.CHRONOLOGICAL
    assert EnhancedConflictDetector.classify_category("birth_place") == ConflictCategory.GEOGRAPHICAL
    assert EnhancedConflictDetector.classify_category("resurrection_appearance") == ConflictCategory.THEOLOGICAL
    assert EnhancedConflictDetector.classify_category("number_of_angels") == ConflictCategory.NUMERICAL
    assert EnhancedConflictDetector.classify_category("unknown_field") == ConflictCategory.OTHER

def test_assess_severity():
    """Test severity assessment rules."""
    # Critical fields
    assert EnhancedConflictDetector.assess_severity("resurrection_body", 2, 2) == ConflictSeverity.CRITICAL
    
    # High severity fields
    assert EnhancedConflictDetector.assess_severity("birthplace", 2, 2) == ConflictSeverity.HIGH
    
    # Structural high chaos (many sources, many variants)
    assert EnhancedConflictDetector.assess_severity("color_of_robe", 4, 3) == ConflictSeverity.HIGH
    
    # Structural medium (binary disagreement)
    assert EnhancedConflictDetector.assess_severity("time_of_day", 3, 2) == ConflictSeverity.MEDIUM
    
    # Low
    assert EnhancedConflictDetector.assess_severity("minor_detail", 2, 2) == ConflictSeverity.LOW

def test_analyze_conflict():
    """Test full analysis."""
    values = {
        "mark": "at the tomb",
        "luke": "at the tomb",
        "john": "in the garden"
    }
    
    conflict = EnhancedConflictDetector.analyze_conflict("location", values, "event")
    
    assert isinstance(conflict, EnhancedConflict)
    assert conflict.field == "location"
    assert conflict.category == ConflictCategory.GEOGRAPHICAL
    assert conflict.severity == ConflictSeverity.MEDIUM # 3 sources, 2 distinct values
    assert conflict.distinct_values == ["at the tomb", "in the garden"]
    assert "Disagreement in geographical domain" in conflict.rationale
