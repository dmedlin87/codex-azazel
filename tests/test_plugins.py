import pytest
from pathlib import Path
from bce.plugins import Plugin, PluginManager
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

def test_plugin_discovery(plugin_env):
    """Test finding plugins in a directory."""
    # Create a dummy plugin file
    (plugin_env / "my_plugin.py").write_text("""
from bce.plugins import Plugin

class Plugin(Plugin):
    name = "my_plugin"
    version = "1.0"
    """)
    
    # Create a non-plugin file
    (plugin_env / "helper.txt").write_text("not a python file")
    (plugin_env / "__init__.py").write_text("")
    
    plugins = PluginManager.discover_plugins()
    assert "my_plugin" in plugins
    assert "__init__" not in plugins
    assert "helper" not in plugins

def test_plugin_lifecycle(plugin_env):
    """Test loading, activating, and unloading a plugin."""
    (plugin_env / "lifecycle_plugin.py").write_text("""
from bce.plugins import Plugin

class Plugin(Plugin):
    name = "lifecycle_plugin"
    
    def activate(self):
        self.active = True
        
    def deactivate(self):
        self.active = False
    """)
    
    # Load
    plugin = PluginManager.load_plugin("lifecycle_plugin")
    assert plugin.name == "lifecycle_plugin"
    assert plugin.active is True
    assert plugin in PluginManager.list_loaded_plugins()
    
    # Unload
    PluginManager.unload_plugin("lifecycle_plugin")
    assert plugin.active is False
    assert plugin not in PluginManager.list_loaded_plugins()

def test_plugin_hooks_integration(plugin_env):
    """Test that a plugin can register hooks."""
    (plugin_env / "hook_plugin.py").write_text("""
from bce.plugins import Plugin
from bce.hooks import HookRegistry, HookPoint

def hook_handler(ctx):
    ctx.data = "modified_by_plugin"
    return ctx

class Plugin(Plugin):
    name = "hook_plugin"
    
    def activate(self):
        HookRegistry.register(HookPoint.BEFORE_QUERY, hook_handler)
        
    def deactivate(self):
        HookRegistry.unregister(HookPoint.BEFORE_QUERY, hook_handler)
    """)
    
    # Clean slate
    HookRegistry.clear_all()
    
    # Load plugin
    PluginManager.load_plugin("hook_plugin")
    
    # Verify hook is active
    ctx = HookRegistry.trigger(HookPoint.BEFORE_QUERY, data="original")
    assert ctx.data == "modified_by_plugin"
    
    # Unload plugin
    PluginManager.unload_plugin("hook_plugin")
    
    # Verify hook is removed (or at least inactive logic handles it)
    # Note: HookRegistry.unregister needs to work correctly for this test to pass
    # But since we're testing integration, let's verify it.
    ctx = HookRegistry.trigger(HookPoint.BEFORE_QUERY, data="original")
    assert ctx.data == "original"

def test_invalid_plugins(plugin_env):
    """Test error handling for bad plugins."""
    # 1. Missing Plugin class
    (plugin_env / "bad_plugin.py").write_text("""
def not_a_plugin_class():
    pass
    """)
    
    with pytest.raises(AttributeError, match="must define a 'Plugin' class"):
        PluginManager.load_plugin("bad_plugin")
        
    # 2. Wrong inheritance
    (plugin_env / "wrong_inherit.py").write_text("""
class Plugin:
    pass
    """)
    
    with pytest.raises(TypeError, match="must inherit from"):
        PluginManager.load_plugin("wrong_inherit")
