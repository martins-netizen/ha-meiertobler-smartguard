"""Shared imports for the current and minimum Home Assistant test packages."""

from importlib.util import find_spec

if find_spec("pytest_homeassistant") is not None:
    from pytest_homeassistant.common import (
        MockConfigEntry,
        async_fire_time_changed,
        mock_restore_cache,
    )
    from pytest_homeassistant.test_util.aiohttp import AiohttpClientMocker
else:
    from pytest_homeassistant_custom_component.common import (
        MockConfigEntry,
        async_fire_time_changed,
        mock_restore_cache,
    )
    from pytest_homeassistant_custom_component.test_util.aiohttp import (
        AiohttpClientMocker,
    )

__all__ = [
    "AiohttpClientMocker",
    "MockConfigEntry",
    "async_fire_time_changed",
    "mock_restore_cache",
]
