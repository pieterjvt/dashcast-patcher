import logging
import os

_LOGGER = logging.getLogger(__name__)
DOMAIN = "dashcast_patcher"


def _apply_patches(app_id):
    try:
        import pychromecast
    except ImportError:
        _LOGGER.error("pychromecast not installed")
        return 0

    base = os.path.dirname(pychromecast.__file__)
    patches = {
        os.path.join(base, "config.py"): [
            (r'APP_DASHCAST = "[^"]*"', f'APP_DASHCAST = "{app_id}"'),
        ],
        os.path.join(base, "controllers", "dashcast.py"): [
            (r'APP_NAMESPACE = "[^"]*"', 'APP_NAMESPACE = "urn:x-cast:lol.pieter.dashcast"'),
        ],
    }

    import re
    patched = 0
    for path, replacements in patches.items():
        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
            new_content = content
            for pattern, replacement in replacements:
                new_content = re.sub(pattern, replacement, new_content)
            if new_content == content:
                _LOGGER.debug("Already up to date: %s", path)
                continue
            with open(path, "w", encoding="utf-8") as f:
                f.write(new_content)
            _LOGGER.info("Patched: %s", path)
            patched += 1
        except OSError as e:
            _LOGGER.error("Failed to patch %s: %s", path, e)

    return patched


async def async_setup_entry(hass, entry):
    from .const import RECEIVERS, CONF_RECEIVER, DEFAULT_RECEIVER

    receiver_key = entry.options.get(CONF_RECEIVER, entry.data.get(CONF_RECEIVER, DEFAULT_RECEIVER))
    app_id = RECEIVERS[receiver_key][0]

    _LOGGER.info("DashCast Patcher: applying receiver '%s' (app_id=%s)", receiver_key, app_id)
    patched = await hass.async_add_executor_job(_apply_patches, app_id)

    if patched:
        _LOGGER.warning("DashCast Patcher: %d file(s) patched", patched)

    entry.async_on_unload(entry.add_update_listener(async_reload_entry))
    return True


async def async_unload_entry(hass, entry):
    return True


async def async_reload_entry(hass, entry):
    await hass.config_entries.async_reload(entry.entry_id)