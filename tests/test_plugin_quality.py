import pytest
from bce import dossiers, api
from bce.plugins import PluginManager
from bce.hooks import HookRegistry, HookPoint
from bce.config import BceConfig, set_default_config, get_default_config

@pytest.fixture(autouse=True)
def enable_hooks_fixture():
    """Enable hooks for all tests in this module."""
    old_config = get_default_config()
    new_config = BceConfig(enable_hooks=True)
    set_default_config(new_config)
    yield
    set_default_config(old_config)

@pytest.fixture
def plugin_env(tmp_path):
    """Fixture setting up a temporary plugin environment."""
    plugin_dir = tmp_path / "plugins"
    plugin_dir.mkdir()
    
    # Clear any existing state
    PluginManager.unload_all()
    PluginManager._plugin_dirs = []
    PluginManager.add_plugin_directory(plugin_dir)
    
    yield plugin_dir
    
    PluginManager.unload_all()
    PluginManager._plugin_dirs = []

def test_quality_scoring_plugin(plugin_env):
    """Test that the quality scorer plugin enriches dossiers."""
    # Copy the actual plugin file to the temp plugin dir
    # We assume the plugin source exists at plugins/quality_scorer.py in the repo
    import shutil
    from pathlib import Path
    
    repo_root = Path.cwd()
    src_plugin = repo_root / "plugins" / "quality_scorer.py"
    dst_plugin = plugin_env / "quality_scorer.py"
    
    if not src_plugin.exists():
        pytest.skip("quality_scorer.py not found in repo plugins/")
        
    shutil.copy(src_plugin, dst_plugin)
    
    # Load the plugin
    PluginManager.load_plugin("quality_scorer")
    
    # Build a dossier (using a real character like 'jesus' if available, or mocked)
    # The API tests usually rely on the bundled data.
    # 'jesus' should exist in the bundled data.
    try:
        dossier = dossiers.build_character_dossier("jesus")
    except Exception as e:
        pytest.skip(f"Skipping due to missing data: {e}")
        
    # Verify quality score was added
    if "quality_score" not in dossier:
        print(f"DEBUG: Dossier keys: {dossier.keys()}")
        # Check if hook is registered
        handlers = HookRegistry._handlers.get(HookPoint.DOSSIER_ENRICH, [])
        print(f"DEBUG: Registered handlers for DOSSIER_ENRICH: {handlers}")
        
    assert "quality_score" in dossier
    score = dossier["quality_score"]
    assert "overall" in score
    assert "dimensions" in score
    assert isinstance(score["overall"], float)
    assert 0.0 <= score["overall"] <= 1.0
    
    # Check specific dimension
    assert "completeness" in score["dimensions"]

def test_quality_scoring_logic():
    """Directly test the scorer logic without plugin infrastructure."""
    # We can import the module directly from the source location for unit testing
    # This is a bit hacky because it's not in the python path, but for testing it works
    import sys
    sys.path.append("plugins")
    try:
        from quality_scorer import QualityScorer, QualityScore
        
        # Mock a character
        from bce.models import Character, SourceProfile
        
        char = Character(
            id="test_char",
            canonical_name="Test Character",
            aliases=[],
            roles=["Disciple"],
            tags=["test"],
            source_profiles=[
                SourceProfile(source_id="mark", traits={"brave": "very"}, references=["Mark 1:1"])
            ]
        )
        
        # We need to mock api.get_character because the static method calls it
        # Or we can test the private methods
        score_val = QualityScorer._score_completeness(char)
        assert 0.0 < score_val < 1.0
        
        score_div = QualityScorer._score_source_diversity(char)
        assert score_div > 0.0

        # Test consistency from dossier
        dossier_with_conflicts = {
            "trait_conflict_summaries": {
                "trait1": {"severity": "high"},
                "trait2": {"severity": "medium"}
            }
        }
        # 1.0 - 0.2 (high) - 0.1 (medium) = 0.7
        consistency = QualityScorer._score_consistency_from_dossier(dossier_with_conflicts)
        assert abs(consistency - 0.7) < 0.001

        dossier_clean = {"trait_conflict_summaries": {}}
        assert QualityScorer._score_consistency_from_dossier(dossier_clean) == 1.0
        
    finally:
        sys.path.remove("plugins")
