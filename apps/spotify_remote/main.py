import os
import sys

# Run from the spotapi repo root so spotapi and config files resolve.
sys.path.insert(0, os.getcwd())

import lvgl as lv  # NOQA
import task_handler  # NOQA

# ---------------------------------------------------------------------------
# Display and input drivers (you provide these on hardware).
#
# Initialize display and touch *before* SpotifyUI is constructed, because
# ui.py calls lv.screen_active(). See README.md for Linux vs MCU entry points.
# ---------------------------------------------------------------------------

th = task_handler.TaskHandler(duration=5)

from spotify_ctrl import SpotifyController  # NOQA
from ui import SpotifyUI  # NOQA


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

while True:
    th.async_refresh()
