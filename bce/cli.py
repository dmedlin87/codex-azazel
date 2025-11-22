from __future__ import annotations

import argparse
import sys
from typing import Iterable

from .dossiers import build_character_dossier, build_event_dossier
from .export import dossier_to_markdown
from .plugins import PluginManager


def main(argv: list[str] | None = None) -> int:
    # Initialize plugins first
    PluginManager.initialize()

    parser = argparse.ArgumentParser(description="Build and export BCE dossiers")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # Dossier commands (legacy behavior promoted to 'dossier' subcommand, 
    # but keeping top-level args for backward compat if possible, or just changing it)
    # To maintain backward compat with "bce character jesus", we need to be careful.
    # The current CLI is positional: "kind" then "dossier_id".
    # We can check if the first arg is "plugins" or "quality" etc.
    
    # Let's restructure to use subparsers properly but keep the simple case working if possible.
    # Actually, let's just add 'plugins' as a choice for 'kind' might be confusing.
    # Better to switch to full subparser architecture.
    
    # Subparser: dossier (default-ish)
    # But since we want to support "bce character jesus", we might need to parse manually or 
    # just add "plugins" as a top level command parallel to "character" and "event" if we change "kind" to be a subcommand.
    
    # Current: bce [kind] [id]
    # Proposed: bce [command] [args...]
    
    # Let's try to handle the legacy arguments by checking argv
    
    cmd_parser = argparse.ArgumentParser(add_help=False)
    cmd_parser.add_argument("cmd", nargs="?", choices=["plugins", "character", "event"])
    
    # We'll stick to the existing structure but extend it safely.
    # If we change "kind" to include "plugins", we break the "dossier_id" requirement.
    
    # Let's rewrite using subparsers for everything, which is cleaner.
    # Users will now run:
    #   bce character jesus
    #   bce event crucifixion
    #   bce plugins list
    
    # Character command
    char_parser = subparsers.add_parser("character", help="Build character dossier")
    char_parser.add_argument("dossier_id", help="ID of the character")
    char_parser.add_argument("-f", "--format", choices=["markdown"], default="markdown", help="Output format")

    # Event command
    event_parser = subparsers.add_parser("event", help="Build event dossier")
    event_parser.add_argument("dossier_id", help="ID of the event")
    event_parser.add_argument("-f", "--format", choices=["markdown"], default="markdown", help="Output format")

    # Plugins command
    plugins_parser = subparsers.add_parser("plugins", help="Manage plugins")
    plugin_subs = plugins_parser.add_subparsers(dest="plugin_cmd", help="Plugin action")
    
    # plugins list
    plugin_subs.add_parser("list", help="List loaded plugins")
    
    # plugins load <name>
    load_parser = plugin_subs.add_parser("load", help="Load a plugin")
    load_parser.add_argument("name", help="Plugin name")
    
    # plugins unload <name>
    unload_parser = plugin_subs.add_parser("unload", help="Unload a plugin")
    unload_parser.add_argument("name", help="Plugin name")

    args = parser.parse_args(argv)

    if args.command == "character":
        try:
            dossier = build_character_dossier(args.dossier_id)
            if args.format == "markdown":
                print(dossier_to_markdown(dossier))
            return 0
        except (KeyError, FileNotFoundError):
            print(f"Error: character '{args.dossier_id}' not found", file=sys.stderr)
            return 1

    elif args.command == "event":
        try:
            dossier = build_event_dossier(args.dossier_id)
            if args.format == "markdown":
                print(dossier_to_markdown(dossier))
            return 0
        except (KeyError, FileNotFoundError):
            print(f"Error: event '{args.dossier_id}' not found", file=sys.stderr)
            return 1

    elif args.command == "plugins":
        if args.plugin_cmd == "list":
            print("Loaded Plugins:")
            for plugin in PluginManager.list_loaded_plugins():
                print(f"  - {plugin.name} (v{plugin.version}): {plugin.description}")
            
            print("\nAvailable Plugins:")
            for name in PluginManager.discover_plugins():
                loaded = any(p.name == name for p in PluginManager.list_loaded_plugins())
                status = "[Loaded]" if loaded else "[Available]"
                print(f"  - {name} {status}")
            return 0
            
        elif args.plugin_cmd == "load":
            try:
                PluginManager.load_plugin(args.name)
                print(f"Plugin '{args.name}' loaded successfully.")
                return 0
            except Exception as e:
                print(f"Failed to load plugin '{args.name}': {e}", file=sys.stderr)
                return 1
                
        elif args.plugin_cmd == "unload":
            try:
                PluginManager.unload_plugin(args.name)
                print(f"Plugin '{args.name}' unloaded successfully.")
                return 0
            except Exception as e:
                print(f"Failed to unload plugin '{args.name}': {e}", file=sys.stderr)
                return 1
        else:
            plugins_parser.print_help()
            return 1

    else:
        parser.print_help()
        return 1

    return 0


if __name__ == "__main__":  # pragma: no cover - exercised via CLI, not import
    raise SystemExit(main())
