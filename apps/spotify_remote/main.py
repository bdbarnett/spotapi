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

from spotify_remote.spotify_ctrl import SpotifyController  # NOQA
from spotify_remote.ui import SpotifyUI  # NOQA


def poll(ui, controller):
    try:
        ui.update_now_playing(controller.refresh_now_playing())
        ui.set_status("")
    except Exception as error:
        ui.set_status(str(error))


controller = SpotifyController()
ui = SpotifyUI(controller, on_poll=lambda: poll(ui, controller))

try:
    me = controller.me()
    ui.set_user(me.display_name)
except Exception as error:
    ui.set_status("Auth: {}".format(error))


def _poll_timer(_timer):
    poll(ui, controller)


lv.timer_create(_poll_timer, 3000, None)
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
