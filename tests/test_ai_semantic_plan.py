"""
Tests the schema-aware semantic query compiler.

Covers plan inference for different intents so the UI can rely on stable
fields (scope, clauses, target_type) without rerunning the full search stack.
"""

from bce.ai.semantic_search import compile_semantic_query


def test_compile_semantic_query_relationship_intent():
    plan = compile_semantic_query("Relationship between Peter and Paul")

    assert "relationships" in plan.scope
    assert plan.target_type == "character"
    assert any("relationships" == clause.field for clause in plan.clauses)
    assert plan.hints and "keyword_seeded" in plan.hints


def test_compile_semantic_query_event_intent():
    plan = compile_semantic_query("When did the resurrection appear in different accounts?")

    assert "accounts" in plan.scope
    assert plan.target_type == "event"
    fields = {clause.field for clause in plan.clauses}
    assert "accounts" in fields
    assert plan.normalized.startswith("when did the resurrection")
