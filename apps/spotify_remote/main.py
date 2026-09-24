# multimer types: queued, sync
# pyscript skip: gallery
import gc
import os
import sys


def _parent(path):
    path = path.replace("\\", "/").rstrip("/")
    return path.rsplit("/", 1)[0] if "/" in path else "."


# Run from anywhere: the spotify_remote package lives in apps/, and the spotapi
# package at the repo root, two levels above this file.
_APPS_DIR = _parent(_parent(__file__))
if not _APPS_DIR.startswith("/") and ":" not in _APPS_DIR:
    _APPS_DIR = os.getcwd().replace("\\", "/") + "/" + _APPS_DIR
for _path in (_parent(_APPS_DIR), _APPS_DIR):
    if _path not in sys.path:
        sys.path.insert(0, _path)

from displaydev import env_set  # NOQA

# This desktop UI owns its logical display geometry. Set these before
# display_driver imports board_config and constructs the display.
env_set("PYDEVICES_WIDTH", "800")
env_set("PYDEVICES_HEIGHT", "480")
env_set("PYDEVICES_SCALE", "1")

import display_driver  # NOQA
import lvgl as lv  # NOQA

# ---------------------------------------------------------------------------
# Display and input drivers (you provide these on hardware).
#
# Initialize display and touch *before* SpotifyUI is constructed, because
# ui.py calls lv.screen_active(). See README.md for Linux vs MCU entry points.
# ---------------------------------------------------------------------------

from spotify_remote.spotify_ctrl import (  # NOQA
    SpotifyController,
    friendly_error,
    is_transient_error,
    needs_authorization,
)
from spotify_remote.ui import SpotifyUI  # NOQA


def _schedule_poll(ui, controller):
    lv.async_call(lambda _data: poll(ui, controller), None)


def poll(ui, controller):
    try:
        ui.update_now_playing(controller.refresh_now_playing())
        ui.clear_success_status()
    except Exception as error:
        ui._status_is_success = False
        ui.set_status(friendly_error(error), kind="error")
    finally:
        gc.collect()


controller = SpotifyController()
ui = SpotifyUI(controller, on_poll=lambda: poll(ui, controller))

try:
    me = controller.me()
    ui.set_user(me.display_name)
    ui.hide_auth_overlay()
except Exception as error:
    message = friendly_error(error)
    if needs_authorization(error):
        ui.show_auth_error(message, mode="authorize")
    elif is_transient_error(error):
        ui.show_auth_error(message, mode="retry")
    else:
        ui.set_status(message, kind="error")


def _poll_timer(_timer):
    _schedule_poll(ui, controller)


lv.timer_create(_poll_timer, 5000, None)
if ui._auth_ok:
    poll(ui, controller)
