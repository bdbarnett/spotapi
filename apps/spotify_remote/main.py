# multimer types: queued, sync
# pyscript skip: gallery
import os
import sys


def _parent(path):
    path = path.replace("\\", "/").rstrip("/")
    return path.rsplit("/", 1)[0] if "/" in path else "."


# Run from anywhere: the spotify_remote package lives in apps/, and the spotapi
# package at the repo root, two levels above this file.
# Only from a source tree: frozen into firmware, or installed on a board, the
# packages are already importable, and the entries this would add ("/", "//.")
# made every later import search the root three times (~185 ms each on an
# ESP32-S3).
_APPS_DIR = _parent(_parent(__file__))
if not _APPS_DIR.startswith("/") and ":" not in _APPS_DIR:
    _APPS_DIR = os.getcwd().replace("\\", "/") + "/" + _APPS_DIR
if _APPS_DIR.rstrip("/").endswith("/apps"):
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

# After a slow LVGL pass display_driver keeps the tick back, to leave the
# thread to application code running outside LVGL. All of this app runs in
# LVGL timers, so that hold only idles the thread and lengthens each stall
# (lvgl-bindings#19); older display_drivers have no such knob.
_loop = getattr(display_driver, "event_loop", None)
_loop = _loop.current_instance() if _loop is not None else None
if _loop is not None and hasattr(_loop, "max_yield_ms"):
    _loop.max_yield_ms = 0

# ---------------------------------------------------------------------------
# Display and input drivers (you provide these on hardware).
#
# Initialize display and touch *before* SpotifyUI is constructed, because
# ui.py calls lv.screen_active(). See README.md for Linux vs MCU entry points.
# ---------------------------------------------------------------------------

from spotify_remote.spotify_ctrl import (  # NOQA
    _http_status,
    SpotifyController,
    friendly_error,
    is_transient_error,
    needs_authorization,
)
from spotify_remote.ui import SpotifyUI  # NOQA
from spotify_remote import config as remote_config  # NOQA
from spotify_remote import local_speaker  # NOQA


# After a rate-limited poll (HTTP 429), this many 5 s polls are skipped (30 s).
# Polling on through a rate limit kept the app limited (LCD-7, 2026-09-25).
POLL_BACKOFF_POLLS = 6
_poll_skip = 0


def poll(ui, controller):
    """Refresh now-playing on the worker; the screen updates when it lands."""

    def done(state, error):
        global _poll_skip
        if error is not None:
            if _http_status(error) == 429:
                _poll_skip = POLL_BACKOFF_POLLS
            ui._status_is_success = False
            ui.set_status(friendly_error(error), kind="error")
            return
        ui.update_now_playing(state)
        ui.clear_success_status()

    # Keyed: a refresh already waiting is replaced, never queued twice.
    ui.worker.submit(controller.refresh_now_playing, done, key="poll")


# A remote and a speaker must not doze: MicroPython's STA default is modem
# sleep, which holds downstream data until the next beacon. On the LCD-7 that
# made a 325 KB library page take 55 s instead of 15, and earful's audio
# chunks crawl (2026-09-25).
if sys.platform == "esp32":
    try:
        import network

        _sta = network.WLAN(network.STA_IF)
        _sta.config(pm=_sta.PM_NONE)
    except (ImportError, AttributeError, OSError, ValueError):
        pass

controller = SpotifyController()
ui = SpotifyUI(controller, on_poll=lambda: poll(ui, controller))

# Optional: this process is also a Connect speaker (earful), listed in Devices.
_speaker_name = remote_config.LOCAL_SPEAKER
if len(getattr(sys, "argv", ())) > 1 and sys.argv[1]:
    _speaker_name = sys.argv[1]
speaker = (
    local_speaker.start(
        _speaker_name,
        output=remote_config.LOCAL_SPEAKER_OUTPUT,
        volume=getattr(remote_config, "LOCAL_SPEAKER_VOLUME", None),
    )
    if _speaker_name
    else None
)
if speaker is not None:
    ui.attach_local_speaker(speaker)

try:
    me = controller.me()
    ui.set_user(me.display_name)
    ui.hide_auth_overlay()
except Exception as error:
    message = friendly_error(error)
    if needs_authorization(error):
        ui.show_auth_error(message, mode="authorize")
    elif is_transient_error(error):
        ui.show_auth_error(message, mode="retry", retry_after=getattr(error, "retry_after", None))
    else:
        ui.set_status(message, kind="error")


def _poll_timer(_timer):
    global _poll_skip
    # Nothing to show while the sign-in / unavailable overlay is up; it
    # retries on its own (SpotifyUI.show_auth_error).
    if not ui._auth_ok:
        return
    if _poll_skip > 0:
        _poll_skip -= 1
        return
    if not ui.worker.pending("poll"):
        poll(ui, controller)


lv.timer_create(_poll_timer, 5000, None)

# The local speaker (earful) stamps what it tells Spotify with the wall
# clock; a clock hours off made the phone show it stopped at 0:00 while it
# played (LCD-7, 2026-09-25: a tool had set the RTC to local time). Boards
# sync once at Wi-Fi connect; sync again every hour, on the worker.
NTP_RESYNC_MS = 60 * 60 * 1000


def _ntp_sync():
    import ntptime

    ntptime.settime()


def _ntp_timer(_timer):
    ui.worker.submit(_ntp_sync, key="ntp")


if sys.platform == "esp32" and speaker is not None:
    lv.timer_create(_ntp_timer, NTP_RESYNC_MS, None)
if ui._auth_ok:
    poll(ui, controller)
