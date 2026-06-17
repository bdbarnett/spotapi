import gc
import os
import sys

# Run from the spotapi repo root so spotapi and config files resolve.
sys.path.insert(0, os.getcwd())

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


def _run_event_loop():
    try:
        import lv_utils

        loop = lv_utils.event_loop.current_instance()
    except ImportError:
        loop = None
    if loop is not None:
        loop.run()
        return
    while True:
        th.async_refresh()


_run_event_loop()
