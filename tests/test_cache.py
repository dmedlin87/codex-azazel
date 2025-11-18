from __future__ import annotations

from typing import List

import pytest

from bce.cache import CacheRegistry
from bce.exceptions import CacheError


class TestCacheRegistryRegisterAndUnregister:
    def test_register_non_callable_raises_cache_error(self) -> None:
        with pytest.raises(CacheError) as exc:
            CacheRegistry.register(123)  # type: ignore[arg-type]

        msg = str(exc.value)
        assert "Invalidator must be callable" in msg

    def test_register_is_idempotent_and_does_not_duplicate_invalidators(self) -> None:
        calls: List[int] = []

        def invalidator() -> None:
            calls.append(1)

        baseline = CacheRegistry.count()

        CacheRegistry.register(invalidator)
        CacheRegistry.register(invalidator)

        # Count should increase by at most 1 relative to the baseline.
        assert CacheRegistry.count() <= baseline + 1

        CacheRegistry.invalidate_all()
        assert calls.count(1) >= 1

        # Clean up our invalidator so we don't affect other tests.
        CacheRegistry.unregister(invalidator)

    def test_unregister_non_registered_raises_cache_error(self) -> None:
        def invalidator() -> None:
            return None

        with pytest.raises(CacheError) as exc:
            CacheRegistry.unregister(invalidator)

        msg = str(exc.value)
        assert "was not registered" in msg


class TestCacheRegistryInvalidateAllBehavior:
    def test_invalidate_all_calls_invalidators_in_order(self) -> None:
        calls: List[str] = []

        def first() -> None:
            calls.append("first")

        def second() -> None:
            calls.append("second")

        CacheRegistry.register(first)
        CacheRegistry.register(second)

        try:
            CacheRegistry.invalidate_all()
        finally:
            CacheRegistry.unregister(first)
            CacheRegistry.unregister(second)

        assert calls[:2] == ["first", "second"]

    def test_invalidate_all_propagates_error_and_stops_subsequent_calls(self) -> None:
        calls: List[str] = []

        def ok() -> None:
            calls.append("ok")

        def boom() -> None:
            calls.append("boom")
            raise RuntimeError("failure")

        def never() -> None:
            calls.append("never")

        CacheRegistry.register(ok)
        CacheRegistry.register(boom)
        CacheRegistry.register(never)

        try:
            with pytest.raises(RuntimeError) as exc:
                CacheRegistry.invalidate_all()

            assert "failure" in str(exc.value)
            # The failing invalidator should have been called, but the later one should not.
            assert calls[:2] == ["ok", "boom"]
            assert "never" not in calls
        finally:
            # Ensure our invalidators are removed for other tests.
            for fn in (ok, boom, never):
                try:
                    CacheRegistry.unregister(fn)
                except CacheError:
                    # If it was never registered or already removed, ignore.
                    pass
