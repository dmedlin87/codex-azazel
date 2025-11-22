from __future__ import annotations

import importlib.util
import logging
from pathlib import Path
from typing import List, Optional, Type

from .config import get_default_config

logger = logging.getLogger(__name__)

class Plugin:
    """Base class for BCE plugins.
    
    Plugins are the primary mechanism for extending BCE functionality without
    modifying core code. They can register hooks, add new CLI commands,
    or extend data models.
    """

    name: str = "unnamed_plugin"
    version: str = "0.0.0"
    description: str = ""

    def activate(self) -> None:
        """Called when plugin is loaded.
        
        Use this method to register hooks, CLI commands, etc.
        """
        pass

    def deactivate(self) -> None:
        """Called when plugin is unloaded.
        
        Use this method to unregister hooks and cleanup resources.
        """
        pass


class PluginManager:
    """Manages plugin discovery, loading, and lifecycle."""

    _loaded_plugins: List[Plugin] = []
    _plugin_dirs: List[Path] = []

    @classmethod
    def add_plugin_directory(cls, path: Path) -> None:
        """Add a directory to search for plugins.
        
        Parameters:
            path: Directory containing plugin python files
        """
        if path not in cls._plugin_dirs:
            cls._plugin_dirs.append(path)

    @classmethod
    def discover_plugins(cls) -> List[str]:
        """Find all available plugins in registered directories.
        
        Returns:
            List of plugin names (filenames without extension)
        """
        plugins = set()
        for plugin_dir in cls._plugin_dirs:
            if not plugin_dir.exists():
                continue
            for file in plugin_dir.glob("*.py"):
                if file.stem != "__init__":
                    plugins.add(file.stem)
        return sorted(list(plugins))

    @classmethod
    def load_plugin(cls, plugin_name: str) -> Plugin:
        """Load and activate a plugin by name.
        
        Parameters:
            plugin_name: Name of the plugin module to load
            
        Returns:
            The activated Plugin instance
            
        Raises:
            ValueError: If plugin is not found
            ImportError: If plugin cannot be imported
            AttributeError: If module does not define a Plugin class
        """
        # Check if already loaded
        for p in cls._loaded_plugins:
            if p.name == plugin_name:
                return p

        # Search for plugin file
        for plugin_dir in cls._plugin_dirs:
            plugin_file = plugin_dir / f"{plugin_name}.py"
            if plugin_file.exists():
                try:
                    spec = importlib.util.spec_from_file_location(
                        plugin_name, plugin_file
                    )
                    if spec is None or spec.loader is None:
                        raise ImportError(f"Could not create module spec for {plugin_file}")
                        
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)

                    # Look for Plugin class
                    if not hasattr(module, "Plugin"):
                        raise AttributeError(f"Plugin module {plugin_name} must define a 'Plugin' class")
                        
                    plugin_cls = getattr(module, "Plugin")
                    if not issubclass(plugin_cls, Plugin):
                         raise TypeError(f"Plugin class in {plugin_name} must inherit from bce.plugins.Plugin")

                    plugin = plugin_cls()
                    
                    # Allow plugin to override name if it wasn't set in class definition
                    if plugin.name == "unnamed_plugin":
                        plugin.name = plugin_name
                        
                    plugin.activate()
                    cls._loaded_plugins.append(plugin)
                    logger.info(f"Loaded plugin: {plugin.name} v{plugin.version}")
                    return plugin
                    
                except Exception as e:
                    logger.error(f"Failed to load plugin {plugin_name}: {e}")
                    raise

        raise ValueError(f"Plugin {plugin_name} not found in search paths: {cls._plugin_dirs}")

    @classmethod
    def unload_plugin(cls, plugin_name: str) -> None:
        """Deactivate and unload a plugin.
        
        Parameters:
            plugin_name: Name of plugin to unload
        """
        for plugin in cls._loaded_plugins:
            if plugin.name == plugin_name:
                try:
                    plugin.deactivate()
                    cls._loaded_plugins.remove(plugin)
                    logger.info(f"Unloaded plugin: {plugin_name}")
                    return
                except Exception as e:
                    logger.error(f"Error deactivating plugin {plugin_name}: {e}")
                    raise
                    
        logger.warning(f"Plugin {plugin_name} not found among loaded plugins")

    @classmethod
    def unload_all(cls) -> None:
        """Unload all plugins."""
        # Create a copy of the list to avoid modification during iteration
        for plugin in list(cls._loaded_plugins):
            cls.unload_plugin(plugin.name)

    @classmethod
    def list_loaded_plugins(cls) -> List[Plugin]:
        """Get list of currently loaded plugins."""
        return list(cls._loaded_plugins)

    @classmethod
    def get_plugin(cls, plugin_name: str) -> Optional[Plugin]:
        """Get a loaded plugin instance by name."""
        for plugin in cls._loaded_plugins:
            if plugin.name == plugin_name:
                return plugin
        return None

    @classmethod
    def initialize(cls) -> None:
        """Initialize plugin system using configuration."""
        config = get_default_config()
        
        # Add default plugin directory: ~/.bce/plugins
        user_plugins = Path.home() / ".bce" / "plugins"
        cls.add_plugin_directory(user_plugins)
        
        # Add project-local plugins: ./plugins
        local_plugins = Path.cwd() / "plugins"
        cls.add_plugin_directory(local_plugins)
        
        # Auto-load plugins defined in config
        if config.ai_plugins:
            for plugin_name in config.ai_plugins:
                try:
                    cls.load_plugin(plugin_name)
                except Exception as e:
                    logger.warning(f"Failed to auto-load plugin {plugin_name}: {e}")
