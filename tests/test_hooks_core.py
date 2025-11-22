import pytest
from bce.hooks import HookRegistry, HookPoint, HookContext, hook
from bce.config import get_default_config, BceConfig, set_default_config

@pytest.fixture(autouse=True)
def enable_hooks_fixture():
    """Enable hooks for all tests in this module."""
    # Save original config
    old_config = get_default_config()
    
    # Create new config with hooks enabled (inheriting other defaults)
    # Note: We create a fresh config to ensure clean state
    new_config = BceConfig(enable_hooks=True)
    set_default_config(new_config)
    
    yield
    
    # Restore original config
    set_default_config(old_config)

def test_hook_registration_and_execution():
    """Test basic hook registration and execution."""
    HookRegistry.clear_all()
    
    execution_order = []
    
    def handler1(ctx):
        execution_order.append("handler1")
        return ctx
        
    def handler2(ctx):
        execution_order.append("handler2")
        return ctx
        
    HookRegistry.register(HookPoint.BEFORE_QUERY, handler1, priority=100)
    HookRegistry.register(HookPoint.BEFORE_QUERY, handler2, priority=10)  # Should run first
    
    ctx = HookRegistry.trigger(HookPoint.BEFORE_QUERY, data="test")
    
    assert execution_order == ["handler2", "handler1"]
    assert ctx.data == "test"

def test_hook_abort():
    """Test that a hook can abort execution."""
    HookRegistry.clear_all()
    
    executed = []
    
    def aborting_handler(ctx):
        executed.append("aborting")
        ctx.abort = True
        return ctx
        
    def skipped_handler(ctx):
        executed.append("skipped")
        return ctx
        
    HookRegistry.register(HookPoint.BEFORE_QUERY, aborting_handler, priority=10)
    HookRegistry.register(HookPoint.BEFORE_QUERY, skipped_handler, priority=100)
    
    ctx = HookRegistry.trigger(HookPoint.BEFORE_QUERY)
    
    assert executed == ["aborting"]
    assert ctx.abort is True

def test_hook_decorator():
    """Test the decorator syntax."""
    HookRegistry.clear_all()
    
    @hook(HookPoint.AFTER_QUERY, priority=50)
    def decorated_handler(ctx):
        ctx.data = "modified"
        return ctx
        
    ctx = HookRegistry.trigger(HookPoint.AFTER_QUERY, data="original")
    assert ctx.data == "modified"

def test_hook_context_helpers():
    """Test context helper methods."""
    HookRegistry.clear_all()
    
    def enriching_handler(ctx):
        ctx.record("test note")
        ctx.add_artifact("key", "value")
        return ctx
        
    HookRegistry.register(HookPoint.BEFORE_EXPORT, enriching_handler)
    ctx = HookRegistry.trigger(HookPoint.BEFORE_EXPORT)
    
    assert "test note" in ctx.notes
    assert ctx.artifacts["key"] == "value"

def test_legacy_handler_compat():
    """Test compatibility with handlers returning data instead of context."""
    HookRegistry.clear_all()
    
    def legacy_handler(ctx):
        return "new_data"
        
    HookRegistry.register(HookPoint.BEFORE_QUERY, legacy_handler)
    ctx = HookRegistry.trigger(HookPoint.BEFORE_QUERY, data="old_data")
    
    assert ctx.data == "new_data"
