import pytest
import json
from bce import storage, models
from bce.plugins import PluginManager
from bce.hooks import HookRegistry
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
def changelog_env(tmp_path):
    """Environment with storage and plugin dir."""
    data_root = tmp_path / "data"
    (data_root / "characters").mkdir(parents=True)
    (data_root / "events").mkdir(parents=True)
    
    plugin_dir = tmp_path / "plugins"
    plugin_dir.mkdir()
    
    # Configure BCE to use this data root
    config = BceConfig(data_root=data_root, enable_hooks=True)
    set_default_config(config)
    
    # Initialize plugin system
    PluginManager.unload_all()
    PluginManager._plugin_dirs = []
    PluginManager.add_plugin_directory(plugin_dir)
    
    # Copy plugin code
    import shutil
    from pathlib import Path
    repo_root = Path.cwd()
    src_plugin = repo_root / "plugins" / "changelog.py"
    dst_plugin = plugin_dir / "changelog.py"
    
    if src_plugin.exists():
        shutil.copy(src_plugin, dst_plugin)
    else:
        pytest.skip("plugins/changelog.py not found")
        
    # Load plugin
    PluginManager.load_plugin("changelog")
    
    yield data_root
    
    PluginManager.unload_all()
    PluginManager._plugin_dirs = []

def test_changelog_creation(changelog_env):
    """Test tracking creation of a new character."""
    sm = storage.StorageManager()
    
    char = models.Character(
        id="test_char",
        canonical_name="Test Character",
        aliases=[],
        roles=[]
    )
    
    # Save should trigger hook -> create record
    sm.save_character(char)
    
    log_file = changelog_env / "changelog.json"
    assert log_file.exists()
    
    with log_file.open() as f:
        logs = json.load(f)
        
    assert len(logs) == 1
    assert logs[0]["change_type"] == "create"
    assert logs[0]["entity_id"] == "test_char"

def test_changelog_update(changelog_env):
    """Test tracking updates to a character."""
    sm = storage.StorageManager()
    
    # 1. Create
    char = models.Character(
        id="update_char",
        canonical_name="Original Name",
        aliases=["Alias 1"],
        roles=[]
    )
    sm.save_character(char)
    
    # 2. Update
    char.canonical_name = "New Name"
    char.aliases.append("Alias 2")
    sm.save_character(char)
    
    log_file = changelog_env / "changelog.json"
    with log_file.open() as f:
        logs = json.load(f)
        
    # Should have Create + Update
    assert len(logs) == 2
    
    update_record = logs[1]
    assert update_record["change_type"] == "update"
    assert update_record["entity_id"] == "update_char"
    
    changes = update_record["field_changes"]
    assert "canonical_name" in changes
    assert changes["canonical_name"]["old"] == "Original Name"
    assert changes["canonical_name"]["new"] == "New Name"
    
    assert "aliases" in changes
    # Note: The plugin converts sets to lists for comparison, order might vary
    # but we check if it was captured
    assert sorted(changes["aliases"]["old"]) == ["Alias 1"]
    assert sorted(changes["aliases"]["new"]) == ["Alias 1", "Alias 2"]
