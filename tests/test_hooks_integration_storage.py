import pytest
from pathlib import Path
from bce import storage, models
from bce.hooks import HookRegistry, HookPoint, HookContext
from bce.config import BceConfig, set_default_config
from bce.exceptions import StorageError

@pytest.fixture
def hook_storage(tmp_path):
    """Fixture providing a storage manager with hooks enabled and a temp data root."""
    # Create data dirs
    data_root = tmp_path / "data"
    (data_root / "characters").mkdir(parents=True)
    (data_root / "events").mkdir(parents=True)
    
    # Create a dummy character
    jesus = models.Character(
        id="jesus", 
        canonical_name="Jesus", 
        aliases=["Christ"],
        roles=["Teacher"]
    )
    
    # Set GLOBAL config to enable hooks, because HookRegistry looks at global config
    config = BceConfig(data_root=data_root, enable_hooks=True)
    set_default_config(config)
    
    sm = storage.StorageManager(config)
    # We temporarily disable hooks for this initial save to avoid interference
    # if we were using the global registry (which we are).
    # But since we clear the registry in tests, it should be fine.
    sm.save_character(jesus)
    
    yield sm
    
    # Teardown: Reset global config
    from bce.config import reset_default_config
    reset_default_config()

def test_character_load_hooks(hook_storage):
    """Test that load hooks are triggered."""
    HookRegistry.clear_all()
    
    events = []
    
    def before_load(ctx):
        events.append("before")
        assert ctx.data["char_id"] == "jesus"
        return ctx
        
    def after_load(ctx):
        events.append("after")
        assert isinstance(ctx.data, models.Character)
        assert ctx.data.id == "jesus"
        return ctx
        
    HookRegistry.register(HookPoint.BEFORE_CHARACTER_LOAD, before_load)
    HookRegistry.register(HookPoint.AFTER_CHARACTER_LOAD, after_load)
    
    char = hook_storage.load_character("jesus")
    
    assert events == ["before", "after"]
    assert char.id == "jesus"

def test_character_save_hooks(hook_storage):
    """Test that save hooks are triggered."""
    HookRegistry.clear_all()
    
    events = []
    
    def before_save(ctx):
        events.append("before")
        assert isinstance(ctx.data, models.Character)
        return ctx
        
    def after_save(ctx):
        events.append("after")
        return ctx
        
    HookRegistry.register(HookPoint.BEFORE_CHARACTER_SAVE, before_save)
    HookRegistry.register(HookPoint.AFTER_CHARACTER_SAVE, after_save)
    
    char = hook_storage.load_character("jesus")
    char.canonical_name = "Jesus of Nazareth"
    hook_storage.save_character(char)
    
    assert events == ["before", "after"]
    
    # Verify it was actually saved
    # Temporarily clear hooks to check persistence without triggering them again
    HookRegistry.clear_all()
    loaded = hook_storage.load_character("jesus")
    assert loaded.canonical_name == "Jesus of Nazareth"

def test_load_hook_abort(hook_storage):
    """Test that a load hook can abort the operation."""
    HookRegistry.clear_all()
    
    def abort_load(ctx):
        ctx.abort = True
        return ctx
        
    HookRegistry.register(HookPoint.BEFORE_CHARACTER_LOAD, abort_load)
    
    with pytest.raises(StorageError, match="aborted by hook"):
        hook_storage.load_character("jesus")

def test_save_hook_abort(hook_storage):
    """Test that a save hook can abort the operation."""
    HookRegistry.clear_all()
    
    def abort_save(ctx):
        ctx.abort = True
        return ctx
        
    HookRegistry.register(HookPoint.BEFORE_CHARACTER_SAVE, abort_save)
    
    char = hook_storage.load_character("jesus")
    original_name = char.canonical_name
    char.canonical_name = "Changed Name"
    
    with pytest.raises(StorageError, match="aborted by hook"):
        hook_storage.save_character(char)
        
    # Verify it was NOT saved
    HookRegistry.clear_all()
    loaded = hook_storage.load_character("jesus")
    assert loaded.canonical_name == original_name

def test_hook_modify_data(hook_storage):
    """Test that a hook can modify data in flight."""
    HookRegistry.clear_all()
    
    def modify_char(ctx):
        char = ctx.data
        char.canonical_name = "Modified Name"
        return ctx
        
    HookRegistry.register(HookPoint.AFTER_CHARACTER_LOAD, modify_char)
    
    char = hook_storage.load_character("jesus")
    assert char.canonical_name == "Modified Name"
    
    # Verify it wasn't saved to disk (it's just modified in memory return)
    HookRegistry.clear_all()
    loaded_raw = hook_storage.load_character("jesus")
    assert loaded_raw.canonical_name == "Jesus"
