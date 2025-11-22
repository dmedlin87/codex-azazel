import pytest
from bce import dossiers, api
from bce.plugins import PluginManager
from bce.hooks import HookRegistry, HookPoint
from bce.config import BceConfig, set_default_config, get_default_config
from bce.export import dossier_to_markdown

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
    
    # Copy plugin code
    import shutil
    from pathlib import Path
    repo_root = Path.cwd()
    src_plugin = repo_root / "plugins" / "graph_viz.py"
    dst_plugin = plugin_dir / "graph_viz.py"
    
    if not src_plugin.exists():
        pytest.skip("graph_viz.py not found")
        
    shutil.copy(src_plugin, dst_plugin)
    
    yield plugin_dir
    
    PluginManager.unload_all()
    PluginManager._plugin_dirs = []

def test_graph_viz_plugin(plugin_env):
    """Test that graph_viz plugin injects mermaid blocks."""
    
    # Load plugin
    PluginManager.load_plugin("graph_viz")
    
    # Build dossier for Jesus (has relationships and conflicts)
    dossier = dossiers.build_character_dossier("jesus")
    
    # Render markdown
    md_output = dossier_to_markdown(dossier)
    
    # Check for Mermaid blocks
    assert "```mermaid" in md_output
    assert "## Relationship Graph" in md_output
    assert "graph LR" in md_output
    
    # Check for Conflict Graph
    assert "## Conflict Visualization" in md_output
    assert "graph TD" in md_output
    
    # Check content specific to Jesus
    assert "jesus" in md_output.lower() or "center" in md_output
    assert "peter" in md_output.lower() # Should be in relationship graph
