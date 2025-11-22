from datetime import datetime
from pathlib import Path
from typing import Any, Dict

from bce import storage
from bce.changelog import ChangeLog, ChangeRecord
from bce.hooks import HookRegistry, HookPoint, hook
from bce.plugins import Plugin
from bce.config import get_default_config

class Plugin(Plugin):
    name = "changelog"
    version = "1.0.0"
    description = "Tracks changes to characters and events"

    def activate(self):
        # Initialize changelog in the data root
        config = get_default_config()
        log_path = config.data_root / "changelog.json"
        self.changelog = ChangeLog(log_path)

        # Register hooks
        HookRegistry.register(HookPoint.BEFORE_CHARACTER_SAVE, self.track_character_change)
        HookRegistry.register(HookPoint.BEFORE_EVENT_SAVE, self.track_event_change)

    def deactivate(self):
        HookRegistry.unregister(HookPoint.BEFORE_CHARACTER_SAVE, self.track_character_change)
        HookRegistry.unregister(HookPoint.BEFORE_EVENT_SAVE, self.track_event_change)

    def track_character_change(self, ctx):
        new_char = ctx.data
        char_id = new_char.id
        
        change_type = "update"
        field_changes = {}
        
        try:
            # Try to load existing version
            old_char = storage.load_character(char_id)
            
            # Compare fields
            # 1. Canonical Name
            if old_char.canonical_name != new_char.canonical_name:
                field_changes["canonical_name"] = {
                    "old": old_char.canonical_name,
                    "new": new_char.canonical_name
                }
            
            # 2. Aliases (set comparison)
            if set(old_char.aliases) != set(new_char.aliases):
                field_changes["aliases"] = {
                    "old": list(old_char.aliases),
                    "new": list(new_char.aliases)
                }
                
            # 3. Roles
            if set(old_char.roles) != set(new_char.roles):
                field_changes["roles"] = {
                    "old": list(old_char.roles),
                    "new": list(new_char.roles)
                }
            
            # 4. Tags
            if set(old_char.tags) != set(new_char.tags):
                field_changes["tags"] = {
                    "old": list(old_char.tags),
                    "new": list(new_char.tags)
                }
                
            # Note: Deep comparison of source profiles is complex, skipping for MVP
            if len(old_char.source_profiles) != len(new_char.source_profiles):
                field_changes["source_profiles_count"] = {
                    "old": len(old_char.source_profiles),
                    "new": len(new_char.source_profiles)
                }

        except Exception:
            # Character doesn't exist yet, or failed to load
            change_type = "create"
            field_changes = {"all": "new character"}

        if field_changes or change_type == "create":
            record = ChangeRecord(
                timestamp=datetime.now().isoformat(),
                entity_type="character",
                entity_id=char_id,
                change_type=change_type,
                field_changes=field_changes,
                author="system_user" # Placeholder for auth system
            )
            self.changelog.record_change(record)

        return ctx

    def track_event_change(self, ctx):
        new_event = ctx.data
        event_id = new_event.id
        
        change_type = "update"
        field_changes = {}
        
        try:
            old_event = storage.load_event(event_id)
            
            if old_event.label != new_event.label:
                field_changes["label"] = {
                    "old": old_event.label,
                    "new": new_event.label
                }
                
            if set(old_event.participants) != set(new_event.participants):
                field_changes["participants"] = {
                    "old": list(old_event.participants),
                    "new": list(new_event.participants)
                }

        except Exception:
            change_type = "create"
            field_changes = {"all": "new event"}

        if field_changes or change_type == "create":
            record = ChangeRecord(
                timestamp=datetime.now().isoformat(),
                entity_type="event",
                entity_id=event_id,
                change_type=change_type,
                field_changes=field_changes,
                author="system_user"
            )
            self.changelog.record_change(record)

        return ctx
