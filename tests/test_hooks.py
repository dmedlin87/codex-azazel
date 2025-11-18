"""
Tests for the hooks system

This module tests the core hooks functionality, including registration,
triggering, priority ordering, and abort behavior.
"""

from __future__ import annotations

import pytest

from bce.hooks import (
    HookContext,
    HookPoint,
    HookRegistry,
    hook,
    create_abort_hook,
    create_transform_hook,
)


class TestHookRegistry:
    """Test HookRegistry functionality"""

    def setup_method(self):
        """Clear hooks before each test"""
        HookRegistry.clear_all()
        HookRegistry.enable()

    def teardown_method(self):
        """Clear hooks after each test"""
        HookRegistry.clear_all()

    def test_register_and_trigger_hook(self):
        """Test basic hook registration and triggering"""
        called = []

        def my_handler(ctx: HookContext) -> HookContext:
            called.append(ctx.hook_point)
            return ctx

        HookRegistry.register(HookPoint.BEFORE_CHARACTER_LOAD, my_handler)
        HookRegistry.trigger(HookPoint.BEFORE_CHARACTER_LOAD, data={"char_id": "test"})

        assert called == [HookPoint.BEFORE_CHARACTER_LOAD]

    def test_hook_can_modify_data(self):
        """Test that hooks can modify context data"""

        def modifier(ctx: HookContext) -> HookContext:
            ctx.data["modified"] = True
            return ctx

        HookRegistry.register(HookPoint.BEFORE_CHARACTER_LOAD, modifier)
        ctx = HookRegistry.trigger(
            HookPoint.BEFORE_CHARACTER_LOAD, data={"char_id": "test"}
        )

        assert ctx.data["modified"] is True

    def test_hook_priority_ordering(self):
        """Test that hooks execute in priority order"""
        execution_order = []

        def handler_priority_100(ctx: HookContext) -> HookContext:
            execution_order.append(100)
            return ctx

        def handler_priority_50(ctx: HookContext) -> HookContext:
            execution_order.append(50)
            return ctx

        def handler_priority_150(ctx: HookContext) -> HookContext:
            execution_order.append(150)
            return ctx

        # Register in random order
        HookRegistry.register(HookPoint.BEFORE_CHARACTER_LOAD, handler_priority_100, priority=100)
        HookRegistry.register(HookPoint.BEFORE_CHARACTER_LOAD, handler_priority_50, priority=50)
        HookRegistry.register(HookPoint.BEFORE_CHARACTER_LOAD, handler_priority_150, priority=150)

        HookRegistry.trigger(HookPoint.BEFORE_CHARACTER_LOAD)

        # Should execute in priority order (lowest first)
        assert execution_order == [50, 100, 150]

    def test_hook_abort(self):
        """Test that setting abort stops execution"""
        execution_order = []

        def handler_50(ctx: HookContext) -> HookContext:
            execution_order.append(50)
            return ctx

        def handler_100_aborts(ctx: HookContext) -> HookContext:
            execution_order.append(100)
            ctx.abort = True
            return ctx

        def handler_150(ctx: HookContext) -> HookContext:
            execution_order.append(150)
            return ctx

        HookRegistry.register(HookPoint.BEFORE_CHARACTER_LOAD, handler_50, priority=50)
        HookRegistry.register(HookPoint.BEFORE_CHARACTER_LOAD, handler_100_aborts, priority=100)
        HookRegistry.register(HookPoint.BEFORE_CHARACTER_LOAD, handler_150, priority=150)

        ctx = HookRegistry.trigger(HookPoint.BEFORE_CHARACTER_LOAD)

        # Execution should stop after handler_100
        assert execution_order == [50, 100]
        assert ctx.abort is True

    def test_unregister_hook(self):
        """Test unregistering a hook"""
        called = []

        def handler(ctx: HookContext) -> HookContext:
            called.append(True)
            return ctx

        HookRegistry.register(HookPoint.BEFORE_CHARACTER_LOAD, handler)
        HookRegistry.trigger(HookPoint.BEFORE_CHARACTER_LOAD)
        assert len(called) == 1

        HookRegistry.unregister(HookPoint.BEFORE_CHARACTER_LOAD, handler)
        HookRegistry.trigger(HookPoint.BEFORE_CHARACTER_LOAD)
        assert len(called) == 1  # Not called again

    def test_disabled_hooks(self):
        """Test that disabling hooks prevents execution"""
        called = []

        def handler(ctx: HookContext) -> HookContext:
            called.append(True)
            return ctx

        HookRegistry.register(HookPoint.BEFORE_CHARACTER_LOAD, handler)
        HookRegistry.disable()
        HookRegistry.trigger(HookPoint.BEFORE_CHARACTER_LOAD)

        assert len(called) == 0

        HookRegistry.enable()
        HookRegistry.trigger(HookPoint.BEFORE_CHARACTER_LOAD)
        assert len(called) == 1

    def test_hook_error_handling(self):
        """Test that hook errors don't crash the system"""

        def failing_handler(ctx: HookContext) -> HookContext:
            raise ValueError("Intentional error")

        def successful_handler(ctx: HookContext) -> HookContext:
            ctx.data["success"] = True
            return ctx

        HookRegistry.register(HookPoint.BEFORE_CHARACTER_LOAD, failing_handler, priority=50)
        HookRegistry.register(HookPoint.BEFORE_CHARACTER_LOAD, successful_handler, priority=100)

        # Should not raise, successful handler should still run
        ctx = HookRegistry.trigger(HookPoint.BEFORE_CHARACTER_LOAD, data={})
        assert ctx.data["success"] is True

    def test_list_handlers(self):
        """Test listing registered handlers"""

        def handler1(ctx): return ctx
        def handler2(ctx): return ctx

        HookRegistry.register(HookPoint.BEFORE_CHARACTER_LOAD, handler1)
        HookRegistry.register(HookPoint.BEFORE_CHARACTER_LOAD, handler2)
        HookRegistry.register(HookPoint.BEFORE_CHARACTER_SAVE, handler1)

        handlers = HookRegistry.list_handlers()
        assert handlers[HookPoint.BEFORE_CHARACTER_LOAD.value] == 2
        assert handlers[HookPoint.BEFORE_CHARACTER_SAVE.value] == 1


class TestHookDecorator:
    """Test the @hook decorator"""

    def setup_method(self):
        """Clear hooks before each test"""
        HookRegistry.clear_all()
        HookRegistry.enable()

    def teardown_method(self):
        """Clear hooks after each test"""
        HookRegistry.clear_all()

    def test_hook_decorator(self):
        """Test @hook decorator registration"""
        called = []

        @hook(HookPoint.BEFORE_CHARACTER_LOAD)
        def my_handler(ctx: HookContext) -> HookContext:
            called.append(True)
            return ctx

        HookRegistry.trigger(HookPoint.BEFORE_CHARACTER_LOAD)
        assert len(called) == 1

    def test_hook_decorator_with_priority(self):
        """Test @hook decorator with custom priority"""
        execution_order = []

        @hook(HookPoint.BEFORE_CHARACTER_LOAD, priority=100)
        def handler_100(ctx: HookContext) -> HookContext:
            execution_order.append(100)
            return ctx

        @hook(HookPoint.BEFORE_CHARACTER_LOAD, priority=50)
        def handler_50(ctx: HookContext) -> HookContext:
            execution_order.append(50)
            return ctx

        HookRegistry.trigger(HookPoint.BEFORE_CHARACTER_LOAD)
        assert execution_order == [50, 100]


class TestConvenienceFunctions:
    """Test convenience helper functions"""

    def setup_method(self):
        """Clear hooks before each test"""
        HookRegistry.clear_all()
        HookRegistry.enable()

    def teardown_method(self):
        """Clear hooks after each test"""
        HookRegistry.clear_all()

    def test_create_abort_hook(self):
        """Test create_abort_hook helper"""
        # Create hook that aborts if data is None
        create_abort_hook(
            HookPoint.BEFORE_CHARACTER_LOAD,
            lambda data: data is None
        )

        ctx = HookRegistry.trigger(HookPoint.BEFORE_CHARACTER_LOAD, data=None)
        assert ctx.abort is True

        ctx = HookRegistry.trigger(HookPoint.BEFORE_CHARACTER_LOAD, data={"id": "test"})
        assert ctx.abort is False

    def test_create_transform_hook(self):
        """Test create_transform_hook helper"""
        # Create hook that uppercases strings
        create_transform_hook(
            HookPoint.BEFORE_CHARACTER_LOAD,
            lambda data: {"value": data["value"].upper()} if isinstance(data.get("value"), str) else data
        )

        ctx = HookRegistry.trigger(
            HookPoint.BEFORE_CHARACTER_LOAD,
            data={"value": "hello"}
        )
        assert ctx.data["value"] == "HELLO"


class TestHookContext:
    """Test HookContext object"""

    def test_hook_context_creation(self):
        """Test creating a HookContext"""
        ctx = HookContext(
            hook_point=HookPoint.BEFORE_CHARACTER_LOAD,
            data={"char_id": "test"},
            metadata={"source": "test"}
        )

        assert ctx.hook_point == HookPoint.BEFORE_CHARACTER_LOAD
        assert ctx.data == {"char_id": "test"}
        assert ctx.metadata == {"source": "test"}
        assert ctx.abort is False

    def test_hook_context_repr(self):
        """Test HookContext string representation"""
        ctx = HookContext(
            hook_point=HookPoint.BEFORE_CHARACTER_LOAD,
            data={"char_id": "test"}
        )

        repr_str = repr(ctx)
        assert "HookContext" in repr_str
        assert "BEFORE_CHARACTER_LOAD" in repr_str
        assert "dict" in repr_str  # data type


class TestHookIntegration:
    """Integration tests with actual BCE operations"""

    def setup_method(self):
        """Clear hooks before each test"""
        HookRegistry.clear_all()
        HookRegistry.enable()

    def teardown_method(self):
        """Clear hooks after each test"""
        HookRegistry.clear_all()

    def test_character_load_hooks_triggered(self):
        """Test that character load triggers appropriate hooks"""
        from bce import storage

        before_called = []
        after_called = []

        @hook(HookPoint.BEFORE_CHARACTER_LOAD)
        def before_load(ctx: HookContext) -> HookContext:
            before_called.append(ctx.data.get("char_id"))
            return ctx

        @hook(HookPoint.AFTER_CHARACTER_LOAD)
        def after_load(ctx: HookContext) -> HookContext:
            after_called.append(ctx.data.id)
            return ctx

        # Load a character
        char = storage.load_character("jesus")

        assert before_called == ["jesus"]
        assert after_called == ["jesus"]
        assert char.id == "jesus"

    def test_character_save_hooks_triggered(self):
        """Test that character save triggers appropriate hooks"""
        from bce import storage
        import tempfile
        from pathlib import Path
        from bce.config import BceConfig

        before_called = []
        after_called = []

        @hook(HookPoint.BEFORE_CHARACTER_SAVE)
        def before_save(ctx: HookContext) -> HookContext:
            before_called.append(ctx.data.id)
            return ctx

        @hook(HookPoint.AFTER_CHARACTER_SAVE)
        def after_save(ctx: HookContext) -> HookContext:
            after_called.append(ctx.data.id)
            return ctx

        # Load and save a character to temp location
        with tempfile.TemporaryDirectory() as tmpdir:
            config = BceConfig(data_root=Path(tmpdir) / "data")
            storage_manager = storage.StorageManager(config)
            storage_manager.char_dir.mkdir(parents=True, exist_ok=True)

            # Load original character
            original_char = storage.load_character("jesus")

            # Save to temp location
            storage_manager.save_character(original_char)

        assert before_called == ["jesus"]
        assert after_called == ["jesus"]

    def test_dossier_enrichment_hook(self):
        """Test dossier enrichment hook"""
        from bce import dossiers

        @hook(HookPoint.DOSSIER_ENRICH)
        def add_custom_field(ctx: HookContext) -> HookContext:
            ctx.data["custom_field"] = "test_value"
            return ctx

        dossier = dossiers.build_character_dossier("jesus")
        assert "custom_field" in dossier
        assert dossier["custom_field"] == "test_value"
