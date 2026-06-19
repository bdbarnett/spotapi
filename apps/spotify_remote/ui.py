import gc
import time

import lvgl as lv

from spotify_remote import config as remote_config
from spotify_remote import image_view
from spotify_remote.spotify_ctrl import (
    friendly_error,
    is_no_active_device_error,
    is_transient_error,
    needs_authorization,
)

ACCENT = 0x1DB954
BG = 0x121212
PANEL = 0x1E1E1E
MUTED = 0xB3B3B3
TEXT = 0xFFFFFF
ART_PANEL = 0x0A0A0A
SURFACE = 0x282828
SURFACE_PRESSED = 0x3E3E3E
BORDER = 0x404040
BAR_TRACK = 0x535353
PAUSE_RED = 0xE91429
ACCENT_PRESSED = 0x169C46
PAUSE_PRESSED = 0xB81022
SUCCESS = 0x1ED760
ERROR = 0xF15E6C

ROW_HEIGHT = 44
ROW_GAP = 4
CHIP_W = 58
ROW_CHIP_W = 48
CHIP_H = 32
CHIP_GAP = 6
LIST_THUMB = 40
THUMB_GAP = 8

PANEL_HEADER_H = 48
HUB_ROW_H = 40
PANEL_BACK_W = 76
PANEL_BACK_H = 32
PANEL_TITLE_X = PANEL_BACK_W + 16
HUB_CHIP_X = PANEL_TITLE_X - 8
QUERY_ROW_H = 44
GENRE_ROW_H = 36

SEARCH_TYPES = (
    "track",
    "artist",
    "album",
    "playlist",
    "episode",
    "show",
    "audiobook",
)

LIBRARY_CATEGORIES = (
    "tracks",
    "artists",
    "albums",
    "playlists",
    "episodes",
    "shows",
    "audiobooks",
)


def _screen_size():
    display = lv.display_get_default()
    if display is not None:
        return display.get_horizontal_resolution(), display.get_vertical_resolution()
    scr = lv.screen_active()
    return scr.get_width(), scr.get_height()


def _hex(color):
    return lv.color_hex(color)


def _fmt_ms(ms):
    ms = int(ms or 0)
    total_seconds = ms // 1000
    minutes = total_seconds // 60
    seconds = total_seconds % 60
    return "{}:{:02d}".format(minutes, seconds)


def _label_case(value):
    value = str(value)
    if not value:
        return value
    return value[0].upper() + value[1:]


def _style_base(obj):
    obj.set_style_shadow_width(0, lv.PART.MAIN)
    obj.set_style_pad_all(0, lv.PART.MAIN)
    obj.set_style_border_width(0, lv.PART.MAIN)


def _style_slim_slider(slider):
    _style_base(slider)
    slider.set_style_radius(4, lv.PART.MAIN)
    slider.set_style_radius(4, lv.PART.INDICATOR)
    slider.set_style_radius(4, lv.PART.KNOB)
    slider.set_style_bg_color(_hex(BAR_TRACK), lv.PART.MAIN)
    slider.set_style_bg_color(_hex(ACCENT), lv.PART.INDICATOR)
    slider.set_style_bg_color(_hex(ACCENT), lv.PART.KNOB)
    slider.set_style_pad_all(1, lv.PART.KNOB)


def _style_transport_secondary(btn, size):
    _style_base(btn)
    btn.set_style_radius(size // 2, lv.PART.MAIN)
    btn.set_style_bg_color(_hex(SURFACE), lv.PART.MAIN)
    btn.set_style_bg_color(_hex(SURFACE_PRESSED), lv.PART.MAIN | lv.STATE.PRESSED)


def _style_transport_primary(btn, size, playing=False):
    _style_base(btn)
    btn.set_style_radius(size // 2, lv.PART.MAIN)
    color = PAUSE_RED if playing else ACCENT
    pressed = PAUSE_PRESSED if playing else ACCENT_PRESSED
    btn.set_style_bg_color(_hex(color), lv.PART.MAIN)
    btn.set_style_bg_color(_hex(pressed), lv.PART.MAIN | lv.STATE.PRESSED)


def _style_chip(btn, label, active=False, muted=False):
    _style_base(btn)
    btn.set_style_radius(10, lv.PART.MAIN)
    if active:
        btn.set_style_border_width(0, lv.PART.MAIN)
        btn.set_style_bg_color(_hex(ACCENT), lv.PART.MAIN)
        btn.set_style_bg_color(_hex(ACCENT_PRESSED), lv.PART.MAIN | lv.STATE.PRESSED)
        label.set_style_text_color(_hex(BG), lv.PART.MAIN)
    else:
        btn.set_style_bg_color(_hex(SURFACE), lv.PART.MAIN)
        btn.set_style_bg_color(_hex(SURFACE_PRESSED), lv.PART.MAIN | lv.STATE.PRESSED)
        btn.set_style_border_width(1, lv.PART.MAIN)
        btn.set_style_border_color(_hex(BORDER), lv.PART.MAIN)
        text_color = MUTED if muted else TEXT
        label.set_style_text_color(_hex(text_color), lv.PART.MAIN)


def _style_nav_button(btn, label, active=False):
    _style_chip(btn, label, active=active, muted=not active)


def _style_link_button(btn, label):
    _style_base(btn)
    btn.set_style_radius(6, lv.PART.MAIN)
    btn.set_style_bg_opa(lv.OPA.TRANSP, lv.PART.MAIN)
    btn.set_style_bg_color(_hex(SURFACE_PRESSED), lv.PART.MAIN | lv.STATE.PRESSED)
    if label is not None:
        label.set_style_text_color(_hex(TEXT), lv.PART.MAIN)


LIBRARY_TAB_TITLES = {
    "tracks": "Songs",
    "artists": "Artists",
    "albums": "Albums",
    "playlists": "Playlists",
    "episodes": "Episodes",
    "shows": "Shows",
    "audiobooks": "Audiobooks",
}

SEARCH_TYPE_LABELS = {
    "track": "Tracks",
    "artist": "Artists",
    "album": "Albums",
    "playlist": "Playlists",
    "episode": "Episodes",
    "show": "Shows",
    "audiobook": "Books",
}


def _genre_label(slug):
    words = slug.replace("-", " ").split(" ")
    titled = []
    for word in words:
        if not word:
            continue
        if len(word) == 1:
            titled.append(word.upper())
        else:
            titled.append(word[0].upper() + word[1:])
    return " ".join(titled)


def _enable_horizontal_scroll(obj):
    obj.add_flag(lv.obj.FLAG.SCROLLABLE)
    if hasattr(lv, "DIR"):
        obj.set_scroll_dir(lv.DIR.HOR)
    elif hasattr(lv, "DIRECTION"):
        obj.set_scroll_dir(lv.DIRECTION.HOR)
    obj.set_scrollbar_mode(lv.SCROLLBAR_MODE.AUTO)


def _style_back_button(btn, label):
    _style_base(btn)
    btn.set_style_radius(10, lv.PART.MAIN)
    btn.set_style_bg_color(_hex(SURFACE), lv.PART.MAIN)
    btn.set_style_bg_color(_hex(SURFACE_PRESSED), lv.PART.MAIN | lv.STATE.PRESSED)
    btn.set_style_border_width(1, lv.PART.MAIN)
    btn.set_style_border_color(_hex(BORDER), lv.PART.MAIN)
    label.set_style_text_color(_hex(TEXT), lv.PART.MAIN)


def _raise_back_button(btn):
    if btn is None:
        return
    if hasattr(btn, "move_foreground"):
        btn.move_foreground()
        return
    parent = btn.get_parent()
    if parent is None:
        return
    try:
        parent.move_child(btn, -1)
    except AttributeError:
        pass


def _volume_btn_symbol():
    for name in ("VOLUME_MAX", "AUDIO"):
        symbol = getattr(lv.SYMBOL, name, None)
        if symbol:
            return symbol
    return "Vol"


class SpotifyUI:
    def __init__(self, controller, on_poll):
        self.controller = controller
        self.on_poll = on_poll
        self._now_state = {}
        self._selected_artist = None
        self._browse_back_panel = "now"
        self._library_category = None
        self._playlist_track_uri = None
        self._return_stack = []
        self._status_is_success = False
        self._browse_album_id = None
        self._browse_playlist_id = None
        self._browse_playlist_owned = False
        self._library_offset = 0
        self._load_more_handler = None
        self._seek_dragging = False
        self._current_panel = "now"
        self._library_fetch_limit = remote_config.LIBRARY_LIST_LIMIT
        self._search_type = "track"
        self._search_query = None
        self._search_genre_preset = False
        self._search_type_buttons = {}
        self._search_fetch_limit = remote_config.SEARCH_RESULT_LIMIT
        self._search_genre_slugs = ()
        self._browse_offset = 0
        self._browse_fetch_limit = remote_config.BROWSE_LIST_LIMIT
        self._browse_artist_albums_offset = 0
        self._browse_artist_albums_entries = ()
        self._browse_context = None
        self._loading_panel = None
        self._seek_hold_until = 0
        self._volume_slider_busy = False
        self._volume_popup_visible = False
        self._volume_hide_timer = None
        self._last_volume = 50
        self._library_hub_buttons = {}
        self._auth_ok = True
        self._pending_after_device = None
        self._device_startup_checked = False
        self._device_prompt_dismissed = False
        scr = lv.screen_active()
        self.width, self.height = _screen_size()
        self._build(scr)

    def _build(self, parent):
        width = self.width
        height = self.height
        header_h = 56
        footer_h = 56
        margin = 16
        content_width = width - margin * 2
        content_height = height - header_h - footer_h - margin * 2
        panel_y = header_h + margin
        label_width = max(180, content_width - 96)
        art_size = min(content_height - 48, (content_width * 42) // 100, 420)
        art_x = 24
        details_gap = 32
        details_x = art_x + art_size + details_gap
        details_width = content_width - details_x - 24
        if details_width < 260:
            details_width = content_width - 48
            details_x = 24
        self._details_x = details_x
        self._details_width = details_width
        progress_width = details_width
        slider_track_h = 16
        transport_btn_size = min(56, max(48, (progress_width - 80) // 4))
        play_btn_size = min(72, transport_btn_size + 12)
        seek_btn_w = max(transport_btn_size, 52)
        transport_gap = 12
        transport_total_width = (
            transport_btn_size * 2 + seek_btn_w * 2 + play_btn_size + transport_gap * 4
        )
        transport_start = (progress_width - transport_total_width) // 2
        btn_row_height = max(transport_btn_size, play_btn_size) + 8
        aux_gap = 8
        aux_btn_w = min(88, max(48, (progress_width - aux_gap) // 2))
        aux_btn_h = 40
        action_space = CHIP_W * 2 + CHIP_GAP + 16

        parent.set_style_bg_color(_hex(BG), 0)

        header = lv.obj(parent)
        header.set_size(width, header_h)
        header.align(lv.ALIGN.TOP_MID, 0, 0)
        header.set_style_bg_color(_hex(PANEL), 0)
        header.set_style_border_width(0, 0)
        header.remove_flag(lv.obj.FLAG.SCROLLABLE)

        self.user_label = lv.label(header)
        self.user_label.set_text("Spotify")
        self.user_label.set_style_text_color(_hex(TEXT), 0)
        self.user_label.align(lv.ALIGN.LEFT_MID, 12, 0)

        device_btn_w = min(240, width // 3)
        search_btn_w = 72
        self.search_btn = lv.button(header)
        self.search_btn.set_size(search_btn_w, 40)
        self.search_btn.align(lv.ALIGN.RIGHT_MID, -device_btn_w - 20, 0)
        self.search_btn.set_style_bg_color(_hex(BG), 0)
        self.search_btn.set_style_border_width(1, 0)
        self.search_btn.set_style_border_color(_hex(MUTED), 0)
        self.search_btn.add_event_cb(self._show_search, lv.EVENT.CLICKED, None)
        lv.label(self.search_btn).set_text("Find")
        lv.label(self.search_btn).center()

        self.device_btn = lv.button(header)
        self.device_btn.set_size(device_btn_w, 40)
        self.device_btn.align(lv.ALIGN.RIGHT_MID, -12, 0)
        self.device_btn.set_style_bg_color(_hex(BG), 0)
        self.device_btn.set_style_border_width(1, 0)
        self.device_btn.set_style_border_color(_hex(MUTED), 0)
        self.device_btn.add_event_cb(self._show_devices, lv.EVENT.CLICKED, None)

        self.device_btn_label = lv.label(self.device_btn)
        self.device_btn_label.set_width(device_btn_w - 16)
        self.device_btn_label.set_long_mode(lv.label.LONG.DOT)
        self.device_btn_label.set_style_text_color(_hex(MUTED), 0)
        self.device_btn_label.set_text("Device")
        self.device_btn_label.center()

        nav_items = (
            ("now", "Now"),
            ("library", "Library"),
            ("queue", "Queue"),
            ("recent", "Recent"),
        )
        nav_gap = 10
        nav_h = 40
        nav_w = min(
            160,
            (width - margin * 2 - nav_gap * (len(nav_items) - 1)) // len(nav_items),
        )
        nav_total = nav_w * len(nav_items) + nav_gap * (len(nav_items) - 1)
        nav_x = (width - nav_total) // 2

        self._nav_tabs = {}
        for index, (tab_id, text) in enumerate(nav_items):
            btn, label = self._nav_button(
                parent, text, nav_x + (nav_w + nav_gap) * index, nav_w, nav_h
            )
            self._nav_tabs[tab_id] = (btn, label)
            if tab_id == "now":
                btn.add_event_cb(self._show_now, lv.EVENT.CLICKED, None)
            elif tab_id == "library":
                btn.add_event_cb(self._show_library_hub, lv.EVENT.CLICKED, None)
            elif tab_id == "queue":
                btn.add_event_cb(self._show_queue, lv.EVENT.CLICKED, None)
            elif tab_id == "recent":
                btn.add_event_cb(self._show_recent, lv.EVENT.CLICKED, None)

        self._active_tab = "now"
        self._set_active_tab("now")

        self.now_panel = lv.obj(parent)
        self.now_panel.set_size(content_width, content_height)
        self.now_panel.align(lv.ALIGN.TOP_MID, 0, panel_y)
        self.now_panel.set_style_bg_color(_hex(PANEL), 0)
        self.now_panel.set_style_border_width(0, 0)
        self.now_panel.remove_flag(lv.obj.FLAG.SCROLLABLE)

        self.cover_art = image_view.CoverArtView(self.now_panel, art_size, ART_PANEL, MUTED)
        self.cover_art.align(lv.ALIGN.LEFT_MID, art_x, 0)

        title_w = max(120, details_width - action_space)
        self.track_label = lv.label(self.now_panel)
        self.track_label.set_width(title_w)
        self.track_label.set_long_mode(lv.label.LONG.DOT)
        self.track_label.set_style_text_color(_hex(TEXT), 0)
        self.track_label.set_text("—")
        self.track_label.align(lv.ALIGN.TOP_LEFT, details_x, 28)

        track_action_x = details_x + title_w + CHIP_GAP
        self.playlist_add_btn, self.playlist_add_label = self._action_chip(
            self.now_panel,
            "+PL",
            track_action_x,
            24,
            CHIP_W + 16,
            CHIP_H,
            self._on_add_to_playlist,
        )
        self.like_btn, self.like_label = self._action_chip(
            self.now_panel,
            "Like",
            track_action_x + CHIP_W + 16 + CHIP_GAP,
            24,
            CHIP_W,
            CHIP_H,
            self._on_like_track,
        )

        artist_albums_w = CHIP_W + 8
        artist_follow_w = CHIP_W
        artist_chips_w = artist_albums_w + CHIP_GAP + artist_follow_w + 8
        artist_title_w = max(120, details_width - artist_chips_w)
        self.artist_btn = lv.button(self.now_panel)
        self.artist_btn.set_size(artist_title_w, CHIP_H)
        self.artist_btn.align(lv.ALIGN.TOP_LEFT, details_x, 64)
        _style_link_button(self.artist_btn, None)
        self.artist_btn.add_event_cb(self._on_artist_name_click, lv.EVENT.CLICKED, None)
        self.artist_label = lv.label(self.artist_btn)
        self.artist_label.set_width(artist_title_w - 8)
        self.artist_label.set_long_mode(lv.label.LONG.DOT)
        self.artist_label.set_text("")
        self.artist_label.align(lv.ALIGN.LEFT_MID, 4, 0)

        artist_chips_x = details_x + artist_title_w + CHIP_GAP
        self.artist_albums_btn, self.artist_albums_label = self._action_chip(
            self.now_panel,
            "Albums",
            artist_chips_x,
            64,
            artist_albums_w,
            CHIP_H,
            self._on_artist_albums,
        )
        self.artist_follow_btn, self.artist_follow_label = self._action_chip(
            self.now_panel,
            "Follow",
            artist_chips_x + artist_albums_w + CHIP_GAP,
            64,
            artist_follow_w,
            CHIP_H,
            self._on_follow_artist_now,
        )

        album_title_w = max(120, details_width - CHIP_W - CHIP_GAP)
        self.album_btn = lv.button(self.now_panel)
        self.album_btn.set_size(album_title_w, CHIP_H)
        self.album_btn.align(lv.ALIGN.TOP_LEFT, details_x, 104)
        _style_link_button(self.album_btn, None)
        self.album_btn.add_event_cb(self._on_album_name_click, lv.EVENT.CLICKED, None)
        self.album_label = lv.label(self.album_btn)
        self.album_label.set_width(album_title_w - 8)
        self.album_label.set_long_mode(lv.label.LONG.DOT)
        self.album_label.set_text("")
        self.album_label.align(lv.ALIGN.LEFT_MID, 4, 0)

        self.album_save_btn, self.album_save_label = self._action_chip(
            self.now_panel,
            "Save",
            details_x + album_title_w + CHIP_GAP,
            104,
            CHIP_W,
            CHIP_H,
            self._on_save_album,
        )

        self.playback_flags_label = lv.label(self.now_panel)
        self.playback_flags_label.set_width(details_width)
        self.playback_flags_label.set_long_mode(lv.label.LONG.DOT)
        self.playback_flags_label.set_text("")
        self.playback_flags_label.set_style_text_color(_hex(MUTED), 0)
        self.playback_flags_label.align(lv.ALIGN.TOP_LEFT, details_x, 148)

        self.progress = lv.slider(self.now_panel)
        self.progress.set_size(progress_width, slider_track_h)
        self.progress.align(lv.ALIGN.TOP_LEFT, details_x, 200)
        self.progress.set_range(0, 1000)
        self.progress.set_value(0, lv.ANIM.OFF)
        _style_slim_slider(self.progress)
        self.progress.add_event_cb(self._on_progress_slider, lv.EVENT.PRESSED, None)
        self.progress.add_event_cb(self._on_progress_slider, lv.EVENT.PRESSING, None)
        self.progress.add_event_cb(self._on_progress_slider, lv.EVENT.RELEASED, None)

        self.time_label = lv.label(self.now_panel)
        self.time_label.set_style_text_color(_hex(MUTED), 0)
        self.time_label.set_text("0:00 / 0:00")
        self.time_label.align(lv.ALIGN.TOP_LEFT, details_x, 218)

        btn_row = lv.obj(self.now_panel)
        btn_row.set_size(progress_width, btn_row_height)
        btn_row.align(lv.ALIGN.TOP_LEFT, details_x, 236)
        btn_row.set_style_bg_opa(lv.OPA.TRANSP, 0)
        btn_row.set_style_border_width(0, 0)
        btn_row.set_style_pad_all(0, 0)
        btn_row.remove_flag(lv.obj.FLAG.SCROLLABLE)

        transport_y = (btn_row_height - transport_btn_size) // 2
        play_y = (btn_row_height - play_btn_size) // 2
        tx = transport_start
        self.prev_btn = self._transport_button(
            btn_row, lv.SYMBOL.PREV, tx, transport_y, transport_btn_size
        )
        tx += transport_btn_size + transport_gap
        self.seek_back_btn, self.seek_back_label = self._transport_seek_button(
            btn_row, "-15s", tx, transport_y, seek_btn_w, transport_btn_size
        )
        tx += seek_btn_w + transport_gap
        self.play_btn = lv.button(btn_row)
        self.play_btn.set_size(play_btn_size, play_btn_size)
        self.play_btn.align(lv.ALIGN.TOP_LEFT, tx, play_y)
        _style_transport_primary(self.play_btn, play_btn_size, playing=False)
        self.play_label = lv.label(self.play_btn)
        self.play_label.set_text(lv.SYMBOL.PLAY)
        self.play_label.set_style_text_color(_hex(TEXT), 0)
        self.play_label.center()
        tx += play_btn_size + transport_gap
        self.seek_fwd_btn, self.seek_fwd_label = self._transport_seek_button(
            btn_row, "+15s", tx, transport_y, seek_btn_w, transport_btn_size
        )
        tx += seek_btn_w + transport_gap
        self.next_btn = self._transport_button(
            btn_row, lv.SYMBOL.NEXT, tx, transport_y, transport_btn_size
        )

        self.prev_btn.add_event_cb(self._on_prev, lv.EVENT.CLICKED, None)
        self.seek_back_btn.add_event_cb(self._on_seek_back, lv.EVENT.CLICKED, None)
        self.play_btn.add_event_cb(self._on_play_pause, lv.EVENT.CLICKED, None)
        self.seek_fwd_btn.add_event_cb(self._on_seek_fwd, lv.EVENT.CLICKED, None)
        self.next_btn.add_event_cb(self._on_next, lv.EVENT.CLICKED, None)

        aux_row = lv.obj(self.now_panel)
        aux_row.set_size(progress_width, aux_btn_h + 12)
        aux_row.align(lv.ALIGN.TOP_LEFT, details_x, 314)
        aux_row.set_style_bg_opa(lv.OPA.TRANSP, 0)
        aux_row.set_style_border_width(0, 0)
        aux_row.set_style_pad_all(0, 0)
        aux_row.remove_flag(lv.obj.FLAG.SCROLLABLE)

        aux_start = (progress_width - (aux_btn_w * 2 + aux_gap)) // 2
        self.shuffle_btn, self.shuffle_label = self._row_button(
            aux_row, lv.SYMBOL.SHUFFLE, aux_start, aux_btn_w, aux_btn_h
        )
        self.repeat_btn, self.repeat_label = self._row_button(
            aux_row, lv.SYMBOL.LOOP, aux_start + aux_btn_w + aux_gap, aux_btn_w, aux_btn_h
        )

        self.shuffle_btn.add_event_cb(self._on_shuffle, lv.EVENT.CLICKED, None)
        self.repeat_btn.add_event_cb(self._on_repeat, lv.EVENT.CLICKED, None)

        self.status_label = lv.label(self.now_panel)
        self.status_label.set_width(label_width)
        self.status_label.set_long_mode(lv.label.LONG.DOT)
        self.status_label.set_text("")
        self.status_label.set_style_text_color(_hex(MUTED), 0)
        self.status_label.align(lv.ALIGN.BOTTOM_MID, 0, -8)

        vol_btn_size = 44
        vol_pad = 8
        vol_slider_w = 20
        vol_slider_h = min(160, content_height - 80)
        popup_w = vol_slider_w + vol_pad * 2
        popup_h = vol_slider_h + vol_pad * 2

        self.volume_btn = lv.button(self.now_panel)
        self.volume_btn.set_size(vol_btn_size, vol_btn_size)
        self.volume_btn.align(lv.ALIGN.BOTTOM_RIGHT, -12, -8)
        _style_transport_secondary(self.volume_btn, vol_btn_size)
        self.volume_btn_label = lv.label(self.volume_btn)
        self.volume_btn_label.set_text(_volume_btn_symbol())
        self.volume_btn_label.set_style_text_color(_hex(TEXT), 0)
        self.volume_btn_label.center()
        self.volume_btn.add_event_cb(self._on_volume_btn, lv.EVENT.CLICKED, None)

        self.volume_popup = lv.obj(self.now_panel)
        self.volume_popup.set_size(popup_w, popup_h)
        self.volume_popup.set_style_bg_color(_hex(PANEL), 0)
        self.volume_popup.set_style_radius(8, 0)
        self.volume_popup.set_style_border_width(1, 0)
        self.volume_popup.set_style_border_color(_hex(BORDER), 0)
        self.volume_popup.set_style_pad_all(vol_pad, 0)
        self.volume_popup.remove_flag(lv.obj.FLAG.CLICKABLE)
        self.volume_popup.add_flag(lv.obj.FLAG.HIDDEN)

        self.volume_slider = lv.slider(self.volume_popup)
        self.volume_slider.set_size(vol_slider_w, vol_slider_h)
        self.volume_slider.align(lv.ALIGN.CENTER, 0, 0)
        self.volume_slider.set_range(0, 100)
        self.volume_slider.set_value(50, lv.ANIM.OFF)
        if hasattr(self.volume_slider, "set_orientation") and hasattr(lv, "SLIDER_ORIENTATION"):
            self.volume_slider.set_orientation(lv.SLIDER_ORIENTATION.VERTICAL)
        _style_slim_slider(self.volume_slider)
        self.volume_slider.add_event_cb(self._on_volume_slider, lv.EVENT.RELEASED, None)
        self.volume_slider.add_event_cb(self._on_volume_slider_activity, lv.EVENT.PRESSED, None)
        self.volume_slider.add_event_cb(self._on_volume_slider_activity, lv.EVENT.PRESSING, None)
        self.volume_slider.add_event_cb(self._on_volume_slider_activity, lv.EVENT.RELEASED, None)
        self.volume_popup.align_to(self.volume_btn, lv.ALIGN.OUT_TOP_MID, 0, -6)

        self._list_w = content_width - 16
        self._hub_y = PANEL_HEADER_H
        self._scroll_y = PANEL_HEADER_H + HUB_ROW_H + 4
        self._list_y = PANEL_HEADER_H + 4
        self._scroll_h = content_height - self._scroll_y - 8
        self._scroll_h_no_hub = content_height - self._list_y - 8
        self._device_list_h = content_height - PANEL_HEADER_H - 8
        self._search_query_y = PANEL_HEADER_H
        self._search_type_y = PANEL_HEADER_H + QUERY_ROW_H + 4
        self._search_genre_y = self._search_type_y + HUB_ROW_H + 4
        self._search_scroll_y = self._search_genre_y + GENRE_ROW_H + 4
        self._search_scroll_h = content_height - self._search_scroll_y - 8

        (
            self.library_panel,
            self.library_title,
            self.library_scroll,
            self.library_hub,
            self.library_back_btn,
        ) = self._build_list_panel(parent, content_width, content_height, panel_y, with_hub=True)
        self.library_panel.add_flag(lv.obj.FLAG.HIDDEN)
        self.library_back_btn.add_event_cb(self._nav_back, lv.EVENT.CLICKED, None)
        _enable_horizontal_scroll(self.library_hub)
        self._build_library_hub()

        (
            self.queue_panel,
            self.queue_title,
            self.queue_scroll,
            _queue_hub,
            self.queue_back_btn,
        ) = self._build_list_panel(parent, content_width, content_height, panel_y)
        self.queue_panel.add_flag(lv.obj.FLAG.HIDDEN)
        self.queue_title.set_text("Queue")
        self.queue_back_btn.add_event_cb(self._nav_back, lv.EVENT.CLICKED, None)
        self.queue_note = lv.label(self.queue_panel)
        self.queue_note.set_width(content_width - PANEL_TITLE_X - 16)
        self.queue_note.set_long_mode(lv.label.LONG.WRAP)
        self.queue_note.set_text("Tap Now on a track to play it. Remove from queue is not supported by Spotify.")
        self.queue_note.set_style_text_color(_hex(MUTED), 0)
        self.queue_note.align(lv.ALIGN.TOP_LEFT, PANEL_TITLE_X, 36)
        self.queue_scroll.align(lv.ALIGN.TOP_MID, 0, PANEL_HEADER_H + 28)
        queue_scroll_h = content_height - PANEL_HEADER_H - 36
        self.queue_scroll.set_size(self._list_w, queue_scroll_h)

        (
            self.recent_panel,
            self.recent_title,
            self.recent_scroll,
            _recent_hub,
            self.recent_back_btn,
        ) = self._build_list_panel(parent, content_width, content_height, panel_y)
        self.recent_panel.add_flag(lv.obj.FLAG.HIDDEN)
        self.recent_title.set_text("Recently Played")
        self.recent_back_btn.add_event_cb(self._nav_back, lv.EVENT.CLICKED, None)

        (
            self.search_panel,
            self.search_title,
            self.search_scroll,
            self.search_type_hub,
            self.search_back_btn,
        ) = self._build_list_panel(parent, content_width, content_height, panel_y, with_hub=True)
        self.search_panel.add_flag(lv.obj.FLAG.HIDDEN)
        self.search_title.set_text("Find")
        self.search_back_btn.add_event_cb(self._nav_back, lv.EVENT.CLICKED, None)

        self.search_query_row = lv.obj(self.search_panel)
        self.search_query_row.set_size(content_width - 16, QUERY_ROW_H)
        self.search_query_row.align(lv.ALIGN.TOP_MID, 0, self._search_query_y)
        self.search_query_row.set_style_bg_opa(lv.OPA.TRANSP, 0)
        self.search_query_row.set_style_border_width(0, 0)
        self.search_query_row.remove_flag(lv.obj.FLAG.SCROLLABLE)

        query_w = content_width - 16 - 80 - CHIP_GAP
        self.search_textarea = lv.textarea(self.search_query_row)
        self.search_textarea.set_size(max(120, query_w), CHIP_H + 8)
        self.search_textarea.align(lv.ALIGN.LEFT_MID, HUB_CHIP_X - 8, 0)
        self.search_textarea.set_one_line(True)
        self.search_textarea.set_placeholder_text("Search...")
        self.search_search_btn, _ = self._action_chip(
            self.search_query_row,
            "Search",
            HUB_CHIP_X + max(120, query_w) + CHIP_GAP,
            (QUERY_ROW_H - CHIP_H) // 2,
            72,
            CHIP_H,
            self._on_search_submit,
        )
        self.search_search_btn.remove_flag(lv.obj.FLAG.HIDDEN)

        self.search_type_hub.align(lv.ALIGN.TOP_MID, 0, self._search_type_y)
        _enable_horizontal_scroll(self.search_type_hub)

        self.search_genre_dropdown = lv.dropdown(self.search_panel)
        self.search_genre_dropdown.set_size(content_width - 32, GENRE_ROW_H)
        self.search_genre_dropdown.align(lv.ALIGN.TOP_LEFT, 16, self._search_genre_y)
        _style_base(self.search_genre_dropdown)
        self.search_genre_dropdown.set_style_bg_color(_hex(SURFACE), lv.PART.MAIN)
        self.search_genre_dropdown.set_style_border_width(1, lv.PART.MAIN)
        self.search_genre_dropdown.set_style_border_color(_hex(BORDER), lv.PART.MAIN)
        self.search_genre_dropdown.add_event_cb(
            self._on_genre_dropdown_selected, lv.EVENT.VALUE_CHANGED, None
        )

        self.search_genre_note = lv.label(self.search_panel)
        self.search_genre_note.set_width(content_width - 32)
        self.search_genre_note.set_long_mode(lv.label.LONG.DOT)
        self.search_genre_note.set_style_text_color(_hex(MUTED), 0)
        self.search_genre_note.set_text("")
        self.search_genre_note.align(lv.ALIGN.TOP_LEFT, 16, self._search_genre_y + GENRE_ROW_H - 4)
        self.search_genre_note.add_flag(lv.obj.FLAG.HIDDEN)

        self.search_scroll.align(lv.ALIGN.TOP_MID, 0, self._search_scroll_y)
        self.search_scroll.set_size(self._list_w, self._search_scroll_h)
        _raise_back_button(self.search_back_btn)
        self._build_search_hub()
        _raise_back_button(self.search_back_btn)

        self.browse_panel, self.browse_title, self.browse_scroll, self.browse_hub, self.browse_back_btn = (
            self._build_list_panel(parent, content_width, content_height, panel_y, with_hub=True)
        )
        self.browse_panel.add_flag(lv.obj.FLAG.HIDDEN)
        self.browse_back_btn.add_event_cb(self._browse_back, lv.EVENT.CLICKED, None)

        (
            self.playlist_picker_panel,
            self.playlist_picker_title,
            self.playlist_picker_scroll,
            self.playlist_picker_hub,
            self.playlist_picker_back_btn,
        ) = self._build_list_panel(parent, content_width, content_height, panel_y, with_hub=True)
        self.playlist_picker_panel.add_flag(lv.obj.FLAG.HIDDEN)
        self.playlist_picker_back_btn.add_event_cb(self._picker_back, lv.EVENT.CLICKED, None)
        self._build_playlist_picker_hub()

        (
            self.artist_picker_panel,
            self.artist_picker_title,
            self.artist_picker_scroll,
            _hub,
            self.artist_picker_back_btn,
        ) = self._build_list_panel(parent, content_width, content_height, panel_y)
        self.artist_picker_panel.add_flag(lv.obj.FLAG.HIDDEN)
        self.artist_picker_back_btn.add_event_cb(self._artist_picker_back, lv.EVENT.CLICKED, None)

        self.devices_panel = lv.obj(parent)
        self.devices_panel.set_size(content_width, content_height)
        self.devices_panel.align(lv.ALIGN.TOP_MID, 0, panel_y)
        self.devices_panel.set_style_bg_color(_hex(PANEL), 0)
        self.devices_panel.set_style_border_width(0, 0)
        self.devices_panel.add_flag(lv.obj.FLAG.HIDDEN)

        self.device_list = lv.list(self.devices_panel)
        self.device_list.set_size(self._list_w, self._device_list_h)
        self.device_list.align(lv.ALIGN.TOP_MID, 0, PANEL_HEADER_H + 44)

        self.device_refresh_btn = lv.button(self.devices_panel)
        self.device_refresh_btn.set_size(72, PANEL_BACK_H)
        self.device_refresh_btn.align(lv.ALIGN.TOP_LEFT, PANEL_TITLE_X, 8)
        self.device_refresh_btn.add_event_cb(
            lambda _e: self.load_devices(), lv.EVENT.CLICKED, None
        )
        refresh_label = lv.label(self.device_refresh_btn)
        refresh_label.set_text("Refresh")
        _style_back_button(self.device_refresh_btn, refresh_label)

        self.device_back_btn = lv.button(self.devices_panel)
        self.device_back_btn.set_size(PANEL_BACK_W, PANEL_BACK_H)
        self.device_back_btn.align(lv.ALIGN.TOP_LEFT, 8, 8)
        self.device_back_btn.add_event_cb(self._nav_back, lv.EVENT.CLICKED, None)
        device_back_label = lv.label(self.device_back_btn)
        device_back_label.set_text("Back")
        _style_back_button(self.device_back_btn, device_back_label)
        _raise_back_button(self.device_back_btn)

        self._panel_backs = {
            "library": self.library_back_btn,
            "queue": self.queue_back_btn,
            "recent": self.recent_back_btn,
            "search": self.search_back_btn,
            "browse": self.browse_back_btn,
            "picker": self.playlist_picker_back_btn,
            "artist_picker": self.artist_picker_back_btn,
            "devices": self.device_back_btn,
        }

        self._build_auth_overlay(parent, width, height)
        self._build_action_sheet(parent, width, height)

        self._show_now(None)

    def _build_list_panel(self, parent, content_width, content_height, panel_y, with_hub=False):
        panel = lv.obj(parent)
        panel.set_size(content_width, content_height)
        panel.align(lv.ALIGN.TOP_MID, 0, panel_y)
        panel.set_style_bg_color(_hex(PANEL), 0)
        panel.set_style_border_width(0, 0)
        panel.remove_flag(lv.obj.FLAG.SCROLLABLE)

        title = lv.label(panel)
        title.set_width(content_width - PANEL_TITLE_X - 16)
        title.set_long_mode(lv.label.LONG.DOT)
        title.set_style_text_color(_hex(TEXT), 0)
        title.set_text("")
        title.align(lv.ALIGN.TOP_LEFT, PANEL_TITLE_X, 14)

        hub = lv.obj(panel)
        hub.set_size(content_width - 16, HUB_ROW_H)
        hub.align(lv.ALIGN.TOP_MID, 0, self._hub_y)
        hub.set_style_bg_opa(lv.OPA.TRANSP, 0)
        hub.set_style_border_width(0, 0)
        hub.set_style_pad_all(0, 0)
        hub.add_flag(lv.obj.FLAG.HIDDEN)
        hub.remove_flag(lv.obj.FLAG.SCROLLABLE)

        scroll = lv.obj(panel)
        if with_hub:
            scroll_y = self._scroll_y
            scroll_h = self._scroll_h
        else:
            scroll_y = self._list_y
            scroll_h = self._scroll_h_no_hub
        scroll.set_size(self._list_w, scroll_h)
        scroll.align(lv.ALIGN.TOP_MID, 0, scroll_y)
        scroll.set_style_bg_opa(lv.OPA.TRANSP, 0)
        scroll.set_style_border_width(0, 0)
        scroll.set_style_pad_all(0, 0)
        scroll.add_flag(lv.obj.FLAG.SCROLLABLE)
        scroll.set_scrollbar_mode(lv.SCROLLBAR_MODE.AUTO)

        back_btn = lv.button(panel)
        back_btn.set_size(PANEL_BACK_W, PANEL_BACK_H)
        back_btn.align(lv.ALIGN.TOP_LEFT, 8, 8)
        back_label = lv.label(back_btn)
        back_label.set_text("Back")
        _style_back_button(back_btn, back_label)
        _raise_back_button(back_btn)
        return panel, title, scroll, hub, back_btn

    def _action_chip(self, parent, text, x, y, width, height, callback):
        btn = lv.button(parent)
        btn.set_size(width, height)
        btn.align(lv.ALIGN.TOP_LEFT, x, y)
        label = lv.label(btn)
        label.set_text(text)
        label.center()
        _style_chip(btn, label, active=False)
        btn.add_event_cb(callback, lv.EVENT.CLICKED, None)
        btn.add_flag(lv.obj.FLAG.HIDDEN)
        return btn, label

    def _transport_button(self, parent, symbol, x, y, size):
        btn = lv.button(parent)
        btn.set_size(size, size)
        btn.align(lv.ALIGN.TOP_LEFT, x, y)
        _style_transport_secondary(btn, size)
        label = lv.label(btn)
        label.set_text(symbol)
        label.set_style_text_color(_hex(TEXT), 0)
        label.center()
        return btn

    def _transport_seek_button(self, parent, text, x, y, width, height):
        btn = lv.button(parent)
        btn.set_size(width, height)
        btn.align(lv.ALIGN.TOP_LEFT, x, y)
        _style_transport_secondary(btn, height)
        label = lv.label(btn)
        label.set_text(text)
        label.set_style_text_color(_hex(TEXT), 0)
        label.center()
        return btn, label

    def _nav_button(self, parent, text, x, width, height):
        btn = lv.button(parent)
        btn.set_size(width, height)
        btn.align(lv.ALIGN.BOTTOM_LEFT, x, -8)
        label = lv.label(btn)
        label.set_text(text)
        label.center()
        return btn, label

    def _set_active_tab(self, tab_id):
        self._active_tab = tab_id
        for current_id, (btn, label) in self._nav_tabs.items():
            _style_nav_button(btn, label, active=current_id == tab_id)

    def _row_button(self, parent, text, x, btn_w, btn_h):
        btn = lv.button(parent)
        btn.set_size(btn_w, btn_h)
        btn.align(lv.ALIGN.TOP_LEFT, x, 0)
        label = lv.label(btn)
        label.set_text(text)
        label.center()
        _style_chip(btn, label, active=False)
        return btn, label

    def _show_panel(self, name):
        panels = {
            "now": self.now_panel,
            "library": self.library_panel,
            "queue": self.queue_panel,
            "recent": self.recent_panel,
            "search": self.search_panel,
            "browse": self.browse_panel,
            "picker": self.playlist_picker_panel,
            "artist_picker": self.artist_picker_panel,
            "devices": self.devices_panel,
        }
        for panel_name, panel in panels.items():
            if panel_name == name:
                panel.remove_flag(lv.obj.FLAG.HIDDEN)
            else:
                panel.add_flag(lv.obj.FLAG.HIDDEN)
        if name != "now":
            self._hide_volume_popup()
        self._current_panel = name
        back_btn = self._panel_backs.get(name)
        if back_btn is not None:
            _raise_back_button(back_btn)

    def _push_return(self, handler):
        self._return_stack.append(handler)

    def _pop_return(self):
        if self._return_stack:
            self._return_stack.pop()()
        else:
            self._show_now(None)

    def _nav_back(self, _event):
        if self._current_panel == "devices":
            if self._pending_after_device is not None:
                self._pending_after_device = None
            elif not self._now_state.get("device_id"):
                self._device_prompt_dismissed = True
        self._pop_return()

    def prompt_for_device(self, message, pending_action=None):
        self._pending_after_device = pending_action
        self.set_status(message or "No active device — select one to play")
        if self._current_panel != "devices":
            self._push_return(lambda: self._show_now(None))
            self._show_panel("devices")
        self.load_devices()

    def _handle_playback_error(self, error, pending_action=None):
        if is_no_active_device_error(error):
            self._status_is_success = False
            self.prompt_for_device(
                "No active device — select one to play",
                pending_action=pending_action,
            )
            return
        self._status_is_success = False
        self.set_status(friendly_error(error), kind="error")

    def _run_transport(self, action):
        try:
            action()
            self.on_poll()
        except Exception as error:
            self._handle_playback_error(error, pending_action=action)

    def _run_async(self, work, on_ok=None, on_err=None, loading_panel=None):
        if loading_panel is not None:
            self._set_panel_loading(loading_panel, True)

        def task(_data):
            try:
                result = work()
            except Exception as exc:
                lv.async_call(
                    lambda _d, error=exc: self._async_done(
                        loading_panel, on_ok, on_err, error=error
                    ),
                    None,
                )
                return
            lv.async_call(
                lambda _d, value=result: self._async_done(
                    loading_panel, on_ok, on_err, value=value
                ),
                None,
            )

        lv.async_call(task, None)

    def _async_done(self, loading_panel, on_ok, on_err, value=None, error=None):
        self._set_panel_loading(loading_panel, False)
        if error is not None:
            if on_err:
                on_err(error)
            else:
                self.set_status(friendly_error(error), kind="error")
            return
        if on_ok:
            on_ok(value)

    def _set_panel_loading(self, panel, loading):
        if panel is None:
            self._loading_panel = None
            return
        self._loading_panel = panel if loading else None
        try:
            if loading:
                panel.set_style_opa(180, 0)
            else:
                panel.set_style_opa(255, 0)
        except AttributeError:
            pass

    def _build_auth_overlay(self, parent, width, height):
        self.auth_overlay = lv.obj(parent)
        self.auth_overlay.set_size(width, height)
        self.auth_overlay.align(lv.ALIGN.TOP_LEFT, 0, 0)
        self.auth_overlay.set_style_bg_color(_hex(BG), 0)
        self.auth_overlay.add_flag(lv.obj.FLAG.HIDDEN)

        self.auth_title = lv.label(self.auth_overlay)
        self.auth_title.set_text("Connect Spotify")
        self.auth_title.set_style_text_color(_hex(TEXT), 0)
        self.auth_title.align(lv.ALIGN.TOP_MID, 0, 80)

        self.auth_message = lv.label(self.auth_overlay)
        self.auth_message.set_width(width - 80)
        self.auth_message.set_long_mode(lv.label.LONG.WRAP)
        self.auth_message.set_style_text_color(_hex(MUTED), 0)
        self.auth_message.set_style_text_align(lv.TEXT_ALIGN.CENTER, 0)
        self.auth_message.set_text("Sign in to control playback.")
        self.auth_message.align(lv.ALIGN.TOP_MID, 0, 130)

        self.auth_retry_btn = lv.button(self.auth_overlay)
        self.auth_retry_btn.set_size(160, 44)
        self.auth_retry_btn.align(lv.ALIGN.CENTER, 0, 40)
        self.auth_retry_btn.add_event_cb(self._on_auth_retry, lv.EVENT.CLICKED, None)
        self.auth_retry_label = lv.label(self.auth_retry_btn)
        self.auth_retry_label.set_text("Authorize")
        _style_chip(self.auth_retry_btn, self.auth_retry_label, active=True)
        self._auth_retry_mode = "authorize"

    def show_auth_error(self, message, mode="authorize"):
        self._auth_ok = False
        self._auth_retry_mode = mode
        if mode == "retry":
            self.auth_title.set_text("Spotify unavailable")
            self.auth_retry_label.set_text("Retry")
        else:
            self.auth_title.set_text("Connect Spotify")
            self.auth_retry_label.set_text("Authorize")
        self.auth_message.set_text(message or "Sign in to control playback.")
        self.auth_overlay.remove_flag(lv.obj.FLAG.HIDDEN)
        _raise_back_button(self.auth_retry_btn)

    def hide_auth_overlay(self):
        self._auth_ok = True
        self.auth_overlay.add_flag(lv.obj.FLAG.HIDDEN)

    def _on_auth_retry(self, _event):
        if self._auth_retry_mode == "authorize":
            self.auth_message.set_text("Opening authorization...")
        else:
            self.auth_message.set_text("Retrying...")
        try:
            if self._auth_retry_mode == "authorize":
                from spotify_remote.spotify_ctrl import _ensure_scopes

                _ensure_scopes(self.controller._auth, self.controller._cache)
            self.controller._me = None
            me = self.controller.me()
            self.set_user(me.display_name)
            self.hide_auth_overlay()
            self.on_poll()
            self.set_status("Connected", kind="success")
        except Exception as error:
            message = friendly_error(error)
            if needs_authorization(error):
                self.show_auth_error(message, mode="authorize")
            elif is_transient_error(error):
                self.show_auth_error(message, mode="retry")
            else:
                self.show_auth_error(message, mode="retry")

    def _build_action_sheet(self, parent, width, height):
        self.action_sheet = lv.obj(parent)
        self.action_sheet.set_size(width, height)
        self.action_sheet.align(lv.ALIGN.TOP_LEFT, 0, 0)
        self.action_sheet.set_style_bg_color(_hex(BG), 0)
        self.action_sheet.set_style_bg_opa(200, 0)
        self.action_sheet.add_flag(lv.obj.FLAG.HIDDEN)
        self.action_sheet.add_event_cb(self._hide_action_sheet, lv.EVENT.CLICKED, None)

        self.action_sheet_panel = lv.obj(self.action_sheet)
        sheet_w = min(360, width - 48)
        self.action_sheet_panel.set_size(sheet_w, 240)
        self.action_sheet_panel.align(lv.ALIGN.BOTTOM_MID, 0, -24)
        self.action_sheet_panel.set_style_bg_color(_hex(PANEL), 0)
        self.action_sheet_panel.set_style_radius(12, 0)
        self.action_sheet_panel.remove_flag(lv.obj.FLAG.CLICKABLE)

        self.action_sheet_scroll = lv.obj(self.action_sheet_panel)
        self.action_sheet_scroll.set_size(sheet_w - 16, 200)
        self.action_sheet_scroll.align(lv.ALIGN.TOP_MID, 0, 8)
        self.action_sheet_scroll.set_style_bg_opa(lv.OPA.TRANSP, 0)
        self.action_sheet_scroll.add_flag(lv.obj.FLAG.SCROLLABLE)

    def _hide_action_sheet(self, _event=None):
        self.action_sheet.add_flag(lv.obj.FLAG.HIDDEN)
        self._clear_scroll(self.action_sheet_scroll)

    def _show_action_sheet(self, entry, actions, reload=None):
        self._clear_scroll(self.action_sheet_scroll)
        y = 0
        for action in actions:
            btn = lv.button(self.action_sheet_scroll)
            btn.set_size(self.action_sheet_scroll.get_width(), ROW_HEIGHT)
            btn.align(lv.ALIGN.TOP_MID, 0, y)
            _style_link_button(btn, None)
            label = lv.label(btn)
            label.set_text(action.get("text", "Action"))
            label.center()
            btn.add_event_cb(
                lambda event, act=action: self._run_sheet_action(entry, act, reload),
                lv.EVENT.CLICKED,
                None,
            )
            y += ROW_HEIGHT + 4
        self.action_sheet.remove_flag(lv.obj.FLAG.HIDDEN)

    def _run_sheet_action(self, entry, action, reload):
        self._hide_action_sheet()
        self._run_action(action["handler"], entry, reload=reload)

    def _build_library_hub(self):
        self._clear_scroll(self.library_hub)
        self.library_hub.remove_flag(lv.obj.FLAG.HIDDEN)
        self._library_hub_buttons = {}
        x = HUB_CHIP_X
        chip_w = 72
        for category in LIBRARY_CATEGORIES:
            btn, label = self._action_chip(
                self.library_hub,
                LIBRARY_TAB_TITLES[category],
                x,
                2,
                chip_w,
                CHIP_H,
                lambda event, cat=category: self._show_library_category(cat),
            )
            btn.remove_flag(lv.obj.FLAG.HIDDEN)
            self._library_hub_buttons[category] = (btn, label)
            x += chip_w + CHIP_GAP
        self._style_library_hub()

    def _style_library_hub(self):
        for category, (btn, label) in self._library_hub_buttons.items():
            _style_chip(btn, label, active=category == self._library_category)

    def _show_library_hub(self, _event=None):
        self._set_active_tab("library")
        self._show_panel("library")
        self.library_title.set_text("Library")
        self._build_library_hub()
        if self._library_category:
            self.load_library(
                LIBRARY_TAB_TITLES[self._library_category],
                self._library_category,
            )
        else:
            self._show_empty_state(
                self.library_scroll,
                "Choose Songs, Artists, Albums, Playlists, Episodes, Shows, or Audiobooks",
            )

    def _show_library_category(self, category):
        self._library_category = category
        self._style_library_hub()
        self.load_library(LIBRARY_TAB_TITLES[category], category)

    def _on_search_submit(self, _event):
        text = self.search_textarea.get_text()
        if text:
            self._search_fetch_limit = remote_config.SEARCH_RESULT_LIMIT
            self._run_search(text, genre_preset=False)

    def _populate_genre_dropdown(self, genres):
        options = ["Genre preset..."]
        self._search_genre_slugs = ("",) + tuple(genres)
        for slug in genres:
            options.append(_genre_label(slug))
        self.search_genre_dropdown.set_options("\n".join(options))
        self.search_genre_dropdown.set_selected(0)
        if self.controller.genres_from_api():
            self.search_genre_note.add_flag(lv.obj.FLAG.HIDDEN)
        else:
            self.search_genre_note.set_text("Offline genre list")
            self.search_genre_note.remove_flag(lv.obj.FLAG.HIDDEN)

    def _on_genre_dropdown_selected(self, event):
        dropdown = event.get_target()
        index = dropdown.get_selected()
        if index <= 0 or index >= len(self._search_genre_slugs):
            return
        slug = self._search_genre_slugs[index]
        if slug:
            self._search_fetch_limit = remote_config.SEARCH_RESULT_LIMIT
            self._run_search(slug, genre_preset=True)

    def _now_playing_match(self, entry):
        state = self._now_state
        entry_uri = entry.get("uri")
        state_uri = state.get("item_uri")
        if entry_uri and state_uri and entry_uri == state_uri:
            return True
        entry_id = entry.get("id")
        state_id = state.get("item_id")
        return bool(entry_id and state_id and entry_id == state_id)

    def _show_empty_state(self, scroll, message):
        self._clear_scroll(scroll)
        label = lv.label(scroll)
        label.set_width(self._list_w - 24)
        label.set_long_mode(lv.label.LONG.WRAP)
        label.set_text(message)
        label.set_style_text_color(_hex(MUTED), 0)
        label.align(lv.ALIGN.TOP_MID, 0, 16)

    def _build_search_hub(self):
        self.search_type_hub.align(lv.ALIGN.TOP_MID, 0, self._search_type_y)
        self._clear_scroll(self.search_type_hub)
        self.search_type_hub.remove_flag(lv.obj.FLAG.HIDDEN)
        self._search_type_buttons = {}
        x = HUB_CHIP_X
        type_chip_w = 72
        for type_id in SEARCH_TYPES:
            label = SEARCH_TYPE_LABELS.get(type_id, type_id)
            btn, btn_label = self._action_chip(
                self.search_type_hub,
                label,
                x,
                2,
                type_chip_w,
                CHIP_H,
                lambda event, tid=type_id: self._on_search_type_selected(tid),
            )
            btn.remove_flag(lv.obj.FLAG.HIDDEN)
            self._search_type_buttons[type_id] = (btn, btn_label)
            x += type_chip_w + CHIP_GAP
        self._style_search_type_buttons()

        def load_genres():
            try:
                return self.controller.find_genre_presets()
            except Exception as error:
                self.set_status(friendly_error(error), kind="error")
                return ()

        def on_genres(genres):
            self._populate_genre_dropdown(genres)
            _raise_back_button(self.search_back_btn)

        self._run_async(load_genres, on_ok=on_genres, loading_panel=self.search_panel)
        _raise_back_button(self.search_back_btn)

    def _style_search_type_buttons(self):
        for type_id, (btn, label) in self._search_type_buttons.items():
            _style_chip(btn, label, active=type_id == self._search_type)

    def _on_search_type_selected(self, type_id):
        self._search_type = type_id
        self._style_search_type_buttons()
        if self._search_query:
            self._run_search(self._search_query, self._search_genre_preset)

    def _build_playlist_picker_hub(self):
        self._clear_scroll(self.playlist_picker_hub)
        self.playlist_picker_hub.remove_flag(lv.obj.FLAG.HIDDEN)
        btn, label = self._action_chip(
            self.playlist_picker_hub,
            "+ New",
            HUB_CHIP_X,
            2,
            80,
            CHIP_H,
            self._on_create_playlist,
        )
        btn.remove_flag(lv.obj.FLAG.HIDDEN)
        _raise_back_button(self.playlist_picker_back_btn)

    def _run_action(self, action, entry=None, success_msg=None, reload=None, go_now=False):
        def complete_success():
            if success_msg:
                self._status_is_success = True
                self.set_status(success_msg, kind="success")
            if go_now:
                self._show_now(None)
            if reload:
                reload()
            if go_now or reload is None:
                self.on_poll()

        def run():
            action(entry) if entry is not None else action()

        def pending():
            run()
            complete_success()

        try:
            run()
            complete_success()
        except Exception as error:
            self._status_is_success = False
            self._handle_playback_error(error, pending_action=pending)

    def _track_action_specs(self, include_remove=False):
        specs = [
            {
                "text": "+Q",
                "handler": self._action_add_to_queue,
            },
            {
                "text": "Like",
                "handler": self._action_like_track,
                "active": lambda entry: bool(entry.get("saved")),
            },
            {
                "text": "+PL",
                "handler": self._action_add_to_playlist,
            },
        ]
        if include_remove:
            specs.append(
                {
                    "text": "-PL",
                    "handler": self._action_remove_from_playlist,
                }
            )
        return specs

    def _action_play_track(self, entry):
        self.controller.play_library_item(entry["uri"], entry.get("type", "track"))

    def _action_play_now(self, entry):
        self.controller.play_now(entry["uri"], entry.get("type", "track"))

    def _action_add_to_queue(self, entry):
        self.controller.add_to_queue(entry["uri"])

    def _action_like_track(self, entry):
        track_id = entry.get("id")
        if not track_id:
            return
        saved = entry.get("saved")
        if saved is None:
            saved = self.controller.track_is_saved(track_id)
        self.controller.toggle_save_track(track_id, bool(saved))
        entry["saved"] = not bool(saved)

    def _restore_after_picker(self):
        panel = self._current_panel
        if panel == "browse":
            return lambda: self._show_panel("browse")
        if panel == "library" and self._library_category:
            category = self._library_category
            return lambda: self._show_library(LIBRARY_TAB_TITLES[category], category)
        if panel == "recent":
            return lambda: self._show_recent(None)
        if panel == "queue":
            return lambda: self._show_queue(None)
        if panel == "search":
            return lambda: self._show_search(None, push_return=False)
        return lambda: self._show_now(None)

    def _action_add_to_playlist(self, entry):
        if entry.get("uri"):
            self._open_playlist_picker(entry["uri"], self._restore_after_picker())

    def _action_remove_from_playlist(self, entry):
        playlist_id = entry.get("context_id") or self._browse_playlist_id
        if playlist_id and entry.get("uri"):
            self.controller.remove_from_playlist(playlist_id, entry["uri"])
            if self._browse_playlist_id:
                playlist_entry = {
                    "id": self._browse_playlist_id,
                    "title": self.browse_title.get_text(),
                    "uri": None,
                    "type": "playlist",
                }
                self._open_playlist_tracks(playlist_entry, self._browse_back_panel)

    def _action_play_album(self, entry):
        self.controller.play_context(entry["uri"], shuffle=False)

    def _action_save_album(self, entry):
        album_id = entry.get("id")
        if not album_id:
            return
        saved = entry.get("saved")
        if saved is None:
            saved = self.controller._album_saved(album_id)
        self.controller.toggle_save_album(album_id, bool(saved))
        entry["saved"] = not bool(saved)

    def _action_follow_artist(self, entry):
        artist_id = entry.get("id")
        if not artist_id:
            return
        followed = entry.get("followed")
        if followed is None:
            followed = True
        self.controller.toggle_follow_artist(artist_id, bool(followed))
        entry["followed"] = not bool(followed)

    def _action_shuffle_play(self, entry):
        self.controller.play_context(entry["uri"], shuffle=True)

    def _visible_actions(self, actions, entry):
        visible = []
        for action in actions or ():
            checker = action.get("visible")
            if checker is None or checker(entry):
                visible.append(action)
        return visible

    def _populate_entry_scroll(
        self,
        scroll,
        entries,
        on_primary=None,
        actions=None,
        chip_w=ROW_CHIP_W,
        thumbs=False,
        load_more=None,
        highlight_now=False,
    ):
        self._clear_scroll(scroll)
        if not entries:
            return
        y = 0
        for entry in entries:
            is_now = highlight_now or entry.get("now_playing") or self._now_playing_match(entry)
            row_actions = actions(entry) if callable(actions) else self._visible_actions(actions, entry)
            row_h = ROW_HEIGHT
            if row_actions and len(row_actions) > remote_config.MAX_ROW_ACTIONS:
                row_h = ROW_HEIGHT * 2 - 8

            row = lv.obj(scroll)
            row.set_size(self._list_w - 8, row_h)
            row.align(lv.ALIGN.TOP_MID, 0, y)
            row.set_style_bg_opa(lv.OPA.TRANSP, 0)
            row.set_style_border_width(0, 0)
            row.set_style_pad_all(0, 0)
            row.remove_flag(lv.obj.FLAG.SCROLLABLE)

            left_pad = 8
            main_w = self._list_w - 8
            if thumbs and entry.get("art_url"):
                art_path = self.controller.art_cache.path_for_url(entry["art_url"])
                if art_path:
                    try:
                        img = lv.image(row)
                        img.set_size(LIST_THUMB, LIST_THUMB)
                        img.align(lv.ALIGN.LEFT_MID, 4, 0)
                        img.set_src(art_path)
                        left_pad = LIST_THUMB + THUMB_GAP + 8
                        main_w -= LIST_THUMB + THUMB_GAP
                    except Exception:
                        pass

            action_w = 0
            if row_actions:
                shown = row_actions[: remote_config.MAX_ROW_ACTIONS]
                extra = row_actions[remote_config.MAX_ROW_ACTIONS :]
                if extra:
                    shown = row_actions[: remote_config.MAX_ROW_ACTIONS - 1] + [
                        {"text": "...", "handler": lambda e, a=extra: None}
                    ]
                action_w = chip_w * len(shown) + CHIP_GAP * len(shown)
                main_w -= action_w + CHIP_GAP

            if on_primary is not None:
                main_btn = lv.button(row)
                main_btn.set_size(max(80, main_w), ROW_HEIGHT)
                main_btn.align(lv.ALIGN.LEFT_MID, 0, 0)
                _style_link_button(main_btn, None)
                text = lv.label(main_btn)
                text.set_width(max(60, main_w - 16))
                text.set_long_mode(lv.label.LONG.DOT)
                label_text = self._entry_label(entry)
                if is_now:
                    label_text = "> " + label_text
                text.set_text(label_text)
                text.align(lv.ALIGN.LEFT_MID, left_pad - 8, 0)
                if is_now:
                    text.set_style_text_color(_hex(ACCENT), lv.PART.MAIN)
                main_btn.add_event_cb(
                    lambda event, entry=entry: on_primary(entry),
                    lv.EVENT.CLICKED,
                    None,
                )
            else:
                text = lv.label(row)
                text.set_width(max(60, main_w - 8))
                text.set_long_mode(lv.label.LONG.DOT)
                label_text = self._entry_label(entry)
                if is_now:
                    label_text = "> " + label_text
                text.set_text(label_text)
                text.align(lv.ALIGN.LEFT_MID, left_pad, 0)
                if is_now:
                    text.set_style_text_color(_hex(ACCENT), 0)

            if row_actions:
                x = self._list_w - 8 - action_w
                y_chip = (ROW_HEIGHT - CHIP_H) // 2
                if len(row_actions) > remote_config.MAX_ROW_ACTIONS:
                    y_chip = 2
                shown = row_actions[: remote_config.MAX_ROW_ACTIONS]
                overflow = row_actions[remote_config.MAX_ROW_ACTIONS :]
                if overflow:
                    shown = row_actions[: remote_config.MAX_ROW_ACTIONS - 1]
                for index, action in enumerate(shown):
                    btn, label = self._row_action_chip(
                        row,
                        action["text"],
                        x,
                        y_chip,
                        chip_w,
                        CHIP_H,
                        lambda event, entry=entry, handler=action["handler"]: self._run_action(
                            handler,
                            entry,
                            reload=load_more,
                        ),
                    )
                    if action.get("active") and callable(action["active"]):
                        _style_chip(btn, label, active=action["active"](entry))
                    x += chip_w + CHIP_GAP
                if overflow:
                    btn, label = self._row_action_chip(
                        row,
                        "...",
                        x,
                        ROW_HEIGHT - CHIP_H - 2,
                        chip_w,
                        CHIP_H,
                        lambda event, entry=entry, extra=overflow: self._show_overflow_actions(
                            entry, extra, load_more
                        ),
                    )

            y += row_h + ROW_GAP

        if load_more:
            btn = lv.button(scroll)
            btn.set_size(self._list_w - 8, ROW_HEIGHT)
            btn.align(lv.ALIGN.TOP_MID, 0, y)
            _style_link_button(btn, None)
            lv.label(btn).set_text("Load more")
            lv.label(btn).center()
            btn.add_event_cb(lambda event: load_more(), lv.EVENT.CLICKED, None)

    def _row_action_chip(self, parent, text, x, y, width, height, callback):
        btn = lv.button(parent)
        btn.set_size(width, height)
        btn.align(lv.ALIGN.TOP_LEFT, x, y)
        label = lv.label(btn)
        label.set_text(text)
        label.center()
        _style_chip(btn, label, active=False)
        btn.add_event_cb(callback, lv.EVENT.CLICKED, None)
        return btn, label

    def _show_overflow_actions(self, entry, actions, reload):
        if not actions:
            return
        self._show_action_sheet(entry, actions, reload=reload)

    def _populate_simple_scroll(self, scroll, entries, on_select, actions=None, **kwargs):
        self._populate_entry_scroll(scroll, entries, on_primary=on_select, actions=actions, **kwargs)

    def _populate_track_scroll(self, scroll, entries, on_select, actions=None, **kwargs):
        self._populate_entry_scroll(scroll, entries, on_primary=on_select, actions=actions, **kwargs)

    def _show_now(self, _event):
        self._return_stack = []
        self._set_active_tab("now")
        self._show_panel("now")

    def _show_devices(self, _event):
        self._push_return(lambda: self._show_now(None))
        self._show_panel("devices")
        self.load_devices()

    def _show_library(self, title, category):
        self._library_offset = 0
        self._library_fetch_limit = remote_config.LIBRARY_LIST_LIMIT
        self._library_category = category
        self._set_active_tab("library")
        self._show_panel("library")
        self._build_library_hub()
        self.load_library(title, category)

    def _show_queue(self, _event):
        self._set_active_tab("queue")
        self._show_panel("queue")
        self.load_queue()

    def _show_recent(self, _event):
        self._set_active_tab("recent")
        self._show_panel("recent")
        self.load_recent()

    def _show_search(self, _event, push_return=True):
        if push_return:
            self._push_return(lambda: self._show_now(None))
        self._show_panel("search")
        self._build_search_hub()
        lv.group_focus_obj(self.search_textarea)
        if self._search_query:
            self._run_search(self._search_query, self._search_genre_preset)

    def _browse_back(self, _event):
        if self._browse_back_panel == "library" and self._library_category:
            self._show_library(
                LIBRARY_TAB_TITLES[self._library_category],
                self._library_category,
            )
        elif self._browse_back_panel == "search":
            self._show_search(None, push_return=False)
        else:
            self._show_now(None)

    def _picker_back(self, _event):
        self._pop_return()

    def _artist_picker_back(self, _event):
        self._pop_return()

    def _clear_scroll(self, scroll):
        count = scroll.get_child_count()
        for index in range(count):
            scroll.get_child(0).delete()
        gc.collect()

    def _entry_label(self, entry):
        label = entry["title"]
        if entry.get("subtitle"):
            label += " - " + entry["subtitle"]
        return label

    def _show_browse(
        self,
        title,
        entries,
        on_select,
        hub_actions=None,
        row_actions=None,
        load_more=None,
    ):
        self.browse_title.set_text(title)
        self._clear_scroll(self.browse_hub)
        if hub_actions:
            self.browse_hub.remove_flag(lv.obj.FLAG.HIDDEN)
            self.browse_scroll.align(lv.ALIGN.TOP_MID, 0, self._scroll_y)
            x = HUB_CHIP_X
            for action in hub_actions:
                btn, label = self._action_chip(
                    self.browse_hub,
                    action["text"],
                    x,
                    2,
                    action.get("width", 72),
                    CHIP_H,
                    action["handler"],
                )
                btn.remove_flag(lv.obj.FLAG.HIDDEN)
                if action.get("active"):
                    _style_chip(btn, label, active=True)
                x += action.get("width", 72) + CHIP_GAP
        else:
            self.browse_hub.add_flag(lv.obj.FLAG.HIDDEN)
            self.browse_scroll.align(lv.ALIGN.TOP_MID, 0, self._hub_y)

        self._populate_entry_scroll(
            self.browse_scroll,
            entries,
            on_primary=on_select,
            actions=row_actions,
            thumbs=bool(row_actions),
            load_more=load_more,
            highlight_now=True,
        )
        self._show_panel("browse")
        _raise_back_button(self.browse_back_btn)

    def _open_show_episodes(self, show_id, title, back_panel="now"):
        self._browse_back_panel = back_panel
        self._browse_fetch_limit = remote_config.BROWSE_LIST_LIMIT
        self._browse_context = ("show", show_id, title)

        def work():
            return self.controller.show_episodes(
                show_id, limit=self._browse_fetch_limit
            )

        def on_ok(entries):
            if not entries:
                self._show_browse(
                    title,
                    (),
                    lambda entry: None,
                )
                self._show_empty_state(
                    self.browse_scroll, "No episodes found for this show"
                )
                return
            load_more = None
            if len(entries) >= self._browse_fetch_limit:
                load_more = lambda: self._load_more_show_episodes()
            self._show_browse(
                title,
                entries,
                lambda entry: self._run_action(
                    self._action_play_track, entry, go_now=True
                ),
                row_actions=self._track_action_specs(),
                load_more=load_more,
            )

        self._run_async(work, on_ok=on_ok, loading_panel=self.browse_panel)

    def _load_more_show_episodes(self):
        self._browse_fetch_limit += remote_config.BROWSE_LIST_LIMIT
        kind, show_id, title = self._browse_context
        if kind == "show":
            self._open_show_episodes(show_id, title, self._browse_back_panel)

    def _open_album_tracks(self, album_id, title, back_panel="now"):
        self._browse_back_panel = back_panel
        self._browse_album_id = album_id
        self._browse_fetch_limit = remote_config.BROWSE_LIST_LIMIT
        self._browse_context = ("album", album_id, title)

        def work():
            entries = self.controller.album_tracks(
                album_id, limit=self._browse_fetch_limit
            )
            album_saved = self.controller._album_saved(album_id)
            return entries, album_saved

        def on_ok(result):
            entries, album_saved = result
            hub = [
                {
                    "text": "Save",
                    "width": 72,
                    "active": bool(album_saved),
                    "handler": lambda _event: self._run_action(
                        lambda: self.controller.toggle_save_album(
                            album_id, bool(album_saved)
                        ),
                        success_msg="Album saved"
                        if not album_saved
                        else "Album removed",
                    ),
                },
            ]
            load_more = None
            if len(entries) >= self._browse_fetch_limit:
                load_more = lambda: self._load_more_album_tracks()
            self._show_browse(
                title,
                entries,
                lambda entry: self._run_action(
                    self._action_play_track,
                    entry,
                    go_now=True,
                ),
                hub_actions=hub,
                row_actions=self._track_action_specs(),
                load_more=load_more,
            )

        def on_err(error):
            self.set_status(friendly_error(error), kind="error")

        self._run_async(work, on_ok=on_ok, on_err=on_err, loading_panel=self.browse_panel)

    def _load_more_album_tracks(self):
        self._browse_fetch_limit += remote_config.BROWSE_LIST_LIMIT
        kind, album_id, title = self._browse_context
        if kind == "album":
            self._open_album_tracks(album_id, title, self._browse_back_panel)

    def _open_artist_albums(self, artist, back_panel="now", append=False):
        self._browse_back_panel = back_panel
        self._browse_context = ("artist_albums", artist["id"], artist["name"])
        page_limit = remote_config.ARTIST_ALBUMS_PAGE_LIMIT
        if not append:
            self._browse_artist_albums_offset = 0
            self._browse_artist_albums_entries = ()
        offset = self._browse_artist_albums_offset

        def work():
            return self.controller.artist_albums(
                artist["id"], limit=page_limit, offset=offset
            )

        def on_ok(entries):
            if append:
                combined = list(self._browse_artist_albums_entries)
                combined.extend(entries)
                self._browse_artist_albums_entries = tuple(combined)
            else:
                self._browse_artist_albums_entries = tuple(entries)
            self._browse_artist_albums_offset = offset + len(entries)
            title = "{} — Albums".format(artist["name"])
            load_more = None
            if len(entries) >= page_limit:
                load_more = lambda: self._open_artist_albums(
                    artist, back_panel, append=True
                )
            self._show_browse(
                title,
                self._browse_artist_albums_entries,
                self._on_browse_album_selected,
                load_more=load_more,
            )

        def on_err(error):
            self.set_status(friendly_error(error), kind="error")

        self._run_async(work, on_ok=on_ok, on_err=on_err, loading_panel=self.browse_panel)

    def _open_artist_hub(self, entry, back_panel="library"):
        self._browse_back_panel = back_panel
        artist = {
            "id": entry["id"],
            "name": entry["title"],
            "uri": entry["uri"],
        }
        self._selected_artist = artist
        followed = entry.get("followed", True)
        self._show_browse(
            entry["title"],
            (),
            lambda entry: None,
            hub_actions=[
                {
                    "text": "Albums",
                    "width": 88,
                    "handler": lambda _event: self._open_artist_albums(artist, back_panel),
                },
                {
                    "text": "Play",
                    "width": 72,
                    "handler": lambda _event: self._run_action(
                        self._action_play_album,
                        entry,
                        go_now=True,
                    ),
                },
                {
                    "text": "Follow",
                    "width": 80,
                    "active": bool(followed),
                    "handler": lambda _event: self._run_action(
                        self._action_follow_artist,
                        entry,
                        reload=lambda: self._open_artist_hub(entry, back_panel),
                    ),
                },
            ],
        )

    def _open_playlist_tracks(self, entry, back_panel="library"):
        self._browse_back_panel = back_panel
        self._browse_playlist_id = entry["id"]
        try:
            owned = self.controller.playlist_is_owned(entry["id"])
            self._browse_playlist_owned = owned
            entries = self.controller.playlist_tracks(entry["id"], owned=owned)
            hub = [
                {
                    "text": "Play",
                    "width": 72,
                    "handler": lambda _event: self._run_action(
                        self._action_play_album,
                        entry,
                        go_now=True,
                    ),
                },
                {
                    "text": "Shuffle",
                    "width": 88,
                    "handler": lambda _event: self._run_action(
                        self._action_shuffle_play,
                        entry,
                        go_now=True,
                    ),
                },
            ]
            self._show_browse(
                entry["title"],
                entries,
                lambda track: self._run_action(
                    self._action_play_track,
                    track,
                    go_now=True,
                ),
                hub_actions=hub,
                row_actions=self._track_action_specs(include_remove=owned),
            )
        except Exception as error:
            self.set_status(str(error))

    def _open_playlist_picker(self, track_uri, return_handler=None):
        self._playlist_track_uri = track_uri
        if return_handler is not None:
            self._push_return(return_handler)
        self.playlist_picker_title.set_text("Add to Playlist")
        try:
            entries = self.controller.editable_playlists()
            self._populate_simple_scroll(
                self.playlist_picker_scroll,
                entries,
                self._on_playlist_picked,
            )
            self._build_playlist_picker_hub()
            self._show_panel("picker")
        except Exception as error:
            self.set_status(str(error))

    def _open_artist_picker(self, artists):
        self.artist_picker_title.set_text("Choose Artist")
        entries = []
        for artist in artists:
            entries.append(
                {
                    "title": artist["name"],
                    "subtitle": "",
                    "uri": artist.get("uri"),
                    "type": "artist",
                    "id": artist["id"],
                }
            )
        self._populate_simple_scroll(
            self.artist_picker_scroll,
            entries,
            self._on_artist_picked,
        )
        self._show_panel("artist_picker")

    def _active_artist(self):
        if self._selected_artist:
            return self._selected_artist
        artists = self._now_state.get("artists") or ()
        if artists:
            return artists[0]
        return None

    def _play_entry(self, entry):
        def run():
            self.controller.play_library_item(entry["uri"], entry["type"])
            self._show_now(None)
            self.on_poll()

        try:
            run()
        except Exception as error:
            self._handle_playback_error(error, pending_action=run)

    def _on_browse_track_selected(self, entry):
        def run():
            self.controller.play_library_item(entry["uri"], "track")
            self._show_now(None)
            self.on_poll()

        try:
            run()
        except Exception as error:
            self._handle_playback_error(error, pending_action=run)

    def _on_browse_album_selected(self, entry):
        self._open_album_tracks(entry["id"], entry["title"], self._browse_back_panel)

    def _on_playlist_picked(self, entry):
        try:
            self.controller.add_to_playlist(entry["id"], self._playlist_track_uri)
            self._status_is_success = True
            self.set_status("Added to {}".format(entry["title"]))
            self._pop_return()
        except Exception as error:
            self.set_status(str(error))

    def _on_create_playlist(self, _event):
        name = "New Playlist"
        try:
            self.controller.create_playlist(name)
            self._status_is_success = True
            self.set_status("Created {}".format(name))
            entries = self.controller.editable_playlists()
            self._populate_simple_scroll(
                self.playlist_picker_scroll,
                entries,
                self._on_playlist_picked,
            )
        except Exception as error:
            self.set_status(str(error))

    def _on_artist_picked(self, entry):
        self._selected_artist = {
            "id": entry["id"],
            "name": entry["title"],
            "uri": entry["uri"],
        }
        self._pop_return()
        self._open_artist_hub(entry, "now")

    def _on_like_track(self, _event):
        state = self._now_state
        if state.get("item_type") != "track" or not state.get("item_id"):
            return
        try:
            self.controller.toggle_save_track(state["item_id"], bool(state.get("saved")))
            self.on_poll()
        except Exception as error:
            self.set_status(str(error))

    def _on_add_to_playlist(self, _event):
        uri = self._now_state.get("item_uri")
        if not uri or self._now_state.get("item_type") != "track":
            return
        self._open_playlist_picker(uri, lambda: self._show_now(None))

    def _on_save_album(self, _event):
        state = self._now_state
        album_id = state.get("album_id")
        if not album_id:
            return
        try:
            self.controller.toggle_save_album(album_id, bool(state.get("album_saved")))
            self.on_poll()
        except Exception as error:
            self.set_status(str(error))

    def _on_artist_name_click(self, _event):
        artists = self._now_state.get("artists") or ()
        if len(artists) > 1:
            self._push_return(lambda: self._show_now(None))
            self._open_artist_picker(artists)
        elif len(artists) == 1:
            artist = artists[0]
            self._selected_artist = artist
            entry = {
                "id": artist["id"],
                "title": artist["name"],
                "uri": artist.get("uri"),
                "type": "artist",
                "followed": True,
            }
            self._browse_back_panel = "now"
            self._open_artist_hub(entry, "now")

    def _on_album_name_click(self, _event):
        album_id = self._now_state.get("album_id")
        if album_id:
            self._browse_back_panel = "now"
            self._open_album_tracks(album_id, self._now_state.get("album") or "Album", "now")

    def _on_artist_albums(self, _event):
        artist = self._active_artist()
        if artist:
            self._browse_back_panel = "now"
            self._open_artist_albums(artist, "now")

    def _on_follow_artist_now(self, _event):
        artist = self._active_artist()
        if not artist or not artist.get("id"):
            return
        followed = artist.get("followed")
        if followed is None:
            followed = False
        try:
            self.controller.toggle_follow_artist(artist["id"], bool(followed))
            self.on_poll()
        except Exception as error:
            self.set_status(friendly_error(error), kind="error")

    def _on_prev(self, _event):
        self._run_transport(self.controller.previous_track)

    def _on_play_pause(self, _event):
        self._run_transport(self.controller.play_pause)

    def _on_next(self, _event):
        self._run_transport(self.controller.next_track)

    def _on_shuffle(self, _event):
        self._run_transport(self.controller.toggle_shuffle)

    def _on_repeat(self, _event):
        self._run_transport(self.controller.cycle_repeat)

    def _on_seek_back(self, _event):
        self._run_transport(lambda: self.controller.seek_relative(-15000))

    def _on_seek_fwd(self, _event):
        self._run_transport(lambda: self.controller.seek_relative(15000))

    def _recreate_list(self, attr, parent, height, y_offset):
        old_list = getattr(self, attr)
        old_list.delete()
        gc.collect()
        new_list = lv.list(parent)
        new_list.set_size(self._list_w, height)
        new_list.align(lv.ALIGN.TOP_MID, 0, y_offset)
        setattr(self, attr, new_list)
        return new_list

    def load_devices(self):
        def work():
            return self.controller.available_devices()

        def on_ok(devices):
            self._recreate_list(
                "device_list",
                self.devices_panel,
                self._device_list_h,
                PANEL_HEADER_H + 44,
            )
            if not devices:
                self.device_list.add_text(
                    "No Spotify Connect devices — open Spotify on a phone or speaker."
                )
                _raise_back_button(self.device_back_btn)
                return
            active_id = self._now_state.get("device_id")
            for entry in devices:
                name = entry["name"]
                device_type = entry.get("type") or ""
                if device_type:
                    name = "[{}] {}".format(device_type, name)
                if entry["active"]:
                    name = "> " + name
                item = self.device_list.add_button(None, name)
                device_id = entry["id"]
                item.add_event_cb(
                    lambda event, device_id=device_id: self._on_device_selected(device_id),
                    lv.EVENT.CLICKED,
                    None,
                )
            _raise_back_button(self.device_back_btn)

        def on_err(error):
            self.set_status(friendly_error(error), kind="error")

        self._run_async(work, on_ok=on_ok, on_err=on_err, loading_panel=self.devices_panel)

    def load_queue(self):
        def work():
            return self.controller.queue_entries()

        def on_ok(entries):
            if not entries:
                self._show_empty_state(self.queue_scroll, "Queue is empty")
                return

            def on_primary(entry):
                if entry.get("now_playing"):
                    self._show_now(None)
                    return
                self._run_action(self._action_play_track, entry, go_now=True)

            def queue_actions(entry):
                if entry.get("now_playing"):
                    return []
                return [{"text": "Now", "handler": self._action_play_now}]

            self._populate_entry_scroll(
                self.queue_scroll,
                entries,
                on_primary=on_primary,
                actions=queue_actions,
                highlight_now=True,
            )

        def on_err(error):
            self.set_status(friendly_error(error), kind="error")

        self._run_async(work, on_ok=on_ok, on_err=on_err, loading_panel=self.queue_panel)

    def load_recent(self):
        def work():
            return self.controller.recently_played_entries()

        def on_ok(entries):
            if not entries:
                self._show_empty_state(self.recent_scroll, "Nothing played recently")
                return
            self._populate_entry_scroll(
                self.recent_scroll,
                entries,
                on_primary=lambda entry: self._run_action(
                    self._action_play_track,
                    entry,
                    go_now=True,
                ),
                actions=self._track_action_specs(),
                thumbs=True,
                highlight_now=True,
            )

        def on_err(error):
            self.set_status(friendly_error(error), kind="error")

        self._run_async(work, on_ok=on_ok, on_err=on_err, loading_panel=self.recent_panel)

    def _search_album_actions(self):
        return [
            {"text": "Play", "handler": self._action_play_album},
            {
                "text": "Save",
                "handler": self._action_save_album,
                "active": lambda entry: bool(entry.get("saved")),
            },
        ]

    def _search_artist_actions(self):
        return [
            {"text": "Play", "handler": self._action_play_album},
            {
                "text": "Follow",
                "handler": self._action_follow_artist,
                "active": lambda entry: bool(entry.get("followed")),
            },
        ]

    def _search_playlist_actions(self):
        return [
            {"text": "Play", "handler": self._action_play_album},
            {"text": "Shuffle", "handler": self._action_shuffle_play},
        ]

    def _search_episode_actions(self):
        return [
            {"text": "Play", "handler": self._action_play_track},
            {
                "text": "Save",
                "handler": self._action_save_episode,
                "active": lambda entry: bool(entry.get("saved")),
            },
        ]

    def _search_show_actions(self):
        return [{"text": "Episodes", "handler": self._action_open_show}]

    def _search_audiobook_actions(self):
        return [
            {"text": "Play", "handler": self._action_play_album},
            {
                "text": "Save",
                "handler": self._action_save_audiobook,
                "active": lambda entry: bool(entry.get("saved")),
            },
        ]

    def _action_save_episode(self, entry):
        episode_id = entry.get("id")
        if not episode_id:
            return
        saved = entry.get("saved")
        if saved is None:
            saved = False
        self.controller.toggle_save_episode(episode_id, bool(saved))
        entry["saved"] = not bool(saved)

    def _action_save_audiobook(self, entry):
        book_id = entry.get("id")
        if not book_id:
            return
        saved = entry.get("saved")
        if saved is None:
            saved = False
        self.controller.toggle_save_audiobook(book_id, bool(saved))
        entry["saved"] = not bool(saved)

    def _action_open_show(self, entry):
        back_panel = "library" if self._library_category == "shows" else "search"
        self._browse_back_panel = back_panel
        self._open_show_episodes(entry["id"], entry["title"], back_panel)

    def _run_search(self, query, genre_preset=False):
        self._search_query = query
        self._search_genre_preset = genre_preset
        result_type = self._search_type

        def work():
            built = self.controller.build_search_query(
                query, result_type, genre_preset=genre_preset
            )
            return self.controller.search_entries(
                built, result_type, limit=self._search_fetch_limit
            )

        def on_ok(entries):
            self._render_search_results(query, entries, result_type, genre_preset)

        self._run_async(
            work, on_ok=on_ok, loading_panel=self.search_panel
        )

    def _render_search_results(self, query, entries, result_type, genre_preset):
        type_label = SEARCH_TYPE_LABELS.get(result_type, result_type)
        if genre_preset:
            title_query = _genre_label(query)
        else:
            title_query = query
        self.search_title.set_text(
            "Find: {} · {}".format(title_query, type_label)
        )

        if not entries:
            self._show_empty_state(
                self.search_scroll,
                "No {} results for {}".format(type_label.lower(), title_query),
            )
            _raise_back_button(self.search_back_btn)
            return

        load_more = None
        if len(entries) >= self._search_fetch_limit:
            load_more = lambda: self._load_more_search()

        if result_type == "track":
            self._populate_entry_scroll(
                self.search_scroll,
                entries,
                on_primary=lambda entry: self._run_action(
                    self._action_play_track, entry, go_now=True
                ),
                actions=self._track_action_specs(),
                thumbs=True,
                load_more=load_more,
                highlight_now=True,
            )
        elif result_type == "artist":
            self._populate_entry_scroll(
                self.search_scroll,
                entries,
                on_primary=lambda entry: self._open_artist_hub(entry, "search"),
                actions=self._search_artist_actions(),
                thumbs=True,
                load_more=load_more,
            )
        elif result_type == "album":
            self._populate_entry_scroll(
                self.search_scroll,
                entries,
                on_primary=lambda entry: self._open_album_tracks(
                    entry["id"], entry["title"], "search"
                ),
                actions=self._search_album_actions(),
                thumbs=True,
                load_more=load_more,
            )
        elif result_type == "playlist":
            self._populate_entry_scroll(
                self.search_scroll,
                entries,
                on_primary=lambda entry: self._open_playlist_tracks(entry, "search"),
                actions=self._search_playlist_actions(),
                thumbs=True,
                load_more=load_more,
            )
        elif result_type == "episode":
            self._populate_entry_scroll(
                self.search_scroll,
                entries,
                on_primary=lambda entry: self._run_action(
                    self._action_play_track, entry, go_now=True
                ),
                actions=self._search_episode_actions(),
                thumbs=True,
                load_more=load_more,
            )
        elif result_type == "show":
            self._populate_entry_scroll(
                self.search_scroll,
                entries,
                on_primary=lambda entry: self._open_show_episodes(
                    entry["id"], entry["title"], "search"
                ),
                actions=self._search_show_actions(),
                thumbs=True,
                load_more=load_more,
            )
        elif result_type == "audiobook":
            self._populate_entry_scroll(
                self.search_scroll,
                entries,
                on_primary=lambda entry: self._run_action(
                    self._action_play_album, entry, go_now=True
                ),
                actions=self._search_audiobook_actions(),
                thumbs=True,
                load_more=load_more,
            )

        if len(entries) >= self._search_fetch_limit:
            self.set_status(
                "Showing first {} results".format(len(entries)),
                kind="info",
            )
        _raise_back_button(self.search_back_btn)

    def _load_more_search(self):
        self._search_fetch_limit += remote_config.SEARCH_RESULT_LIMIT
        self._run_search(self._search_query, self._search_genre_preset)

    def _progress_position_ms(self):
        duration = self._now_state.get("duration_ms") or 0
        if duration <= 0:
            return 0
        return int(duration * self.progress.get_value() / 1000)

    def _update_progress_label_from_slider(self):
        duration = self._now_state.get("duration_ms") or 0
        position = self._progress_position_ms()
        self.time_label.set_text(
            "{} / {}".format(_fmt_ms(position), _fmt_ms(duration))
        )

    def _on_progress_slider(self, event):
        code = event.get_code()
        if code == lv.EVENT.PRESSED:
            self._seek_dragging = True
        elif code == lv.EVENT.PRESSING:
            self._update_progress_label_from_slider()
        elif code == lv.EVENT.RELEASED:
            self._seek_dragging = False
            if not self._now_state.get("duration_ms"):
                return
            position_ms = self._progress_position_ms()

            def action():
                self.controller.seek_absolute(position_ms)
                self._seek_hold_until = time.ticks_add(time.ticks_ms(), 3500)
                self.on_poll()

            try:
                action()
            except Exception as error:
                self._handle_playback_error(error, pending_action=action)

    def _on_volume_slider(self, event):
        if event.get_code() != lv.EVENT.RELEASED:
            return
        if self._volume_slider_busy:
            return
        value = self.volume_slider.get_value()
        self._last_volume = int(value)
        self._volume_slider_busy = True
        try:
            self._run_transport(lambda: self.controller.change_volume_absolute(value))
        finally:
            self._volume_slider_busy = False

    def _on_volume_slider_activity(self, event):
        if event.get_code() not in (lv.EVENT.PRESSED, lv.EVENT.PRESSING, lv.EVENT.RELEASED):
            return
        self._reset_volume_hide_timer()

    def _on_volume_btn(self, _event):
        self._toggle_volume_popup()

    def _toggle_volume_popup(self):
        if self._volume_popup_visible:
            self._hide_volume_popup()
        else:
            self._show_volume_popup()

    def _show_volume_popup(self):
        self.volume_slider.set_value(self._last_volume, lv.ANIM.OFF)
        self.volume_popup.remove_flag(lv.obj.FLAG.HIDDEN)
        self.volume_popup.align_to(self.volume_btn, lv.ALIGN.OUT_TOP_MID, 0, -6)
        _raise_back_button(self.volume_popup)
        _raise_back_button(self.volume_btn)
        self._volume_popup_visible = True
        _style_chip(self.volume_btn, self.volume_btn_label, active=True)
        self._reset_volume_hide_timer()

    def _hide_volume_popup(self):
        self._cancel_volume_hide_timer()
        if not self._volume_popup_visible:
            return
        self.volume_popup.add_flag(lv.obj.FLAG.HIDDEN)
        self._volume_popup_visible = False
        vol_btn_size = self.volume_btn.get_height()
        _style_transport_secondary(self.volume_btn, vol_btn_size)

    def _cancel_volume_hide_timer(self):
        if self._volume_hide_timer is None:
            return
        try:
            self._volume_hide_timer.delete()
        except Exception:
            pass
        self._volume_hide_timer = None

    def _reset_volume_hide_timer(self):
        self._cancel_volume_hide_timer()
        if not self._volume_popup_visible:
            return
        self._volume_hide_timer = lv.timer_create(self._on_volume_hide_timer, 3000, None)
        if hasattr(self._volume_hide_timer, "set_repeat_count"):
            self._volume_hide_timer.set_repeat_count(1)

    def _on_volume_hide_timer(self, _timer):
        self._volume_hide_timer = None
        self._hide_volume_popup()

    def load_library(self, title, category):
        self.library_title.set_text(title)
        self._style_library_hub()

        def work():
            return self.controller.library_entries(
                category, limit=self._library_fetch_limit
            )

        def on_ok(entries):
            if not entries:
                self._show_empty_state(
                    self.library_scroll,
                    "No {} in your library".format(title.lower()),
                )
                return
            load_more = None
            if len(entries) >= self._library_fetch_limit:
                load_more = lambda: self._load_more_library(title, category)
            self._render_library_entries(category, entries, load_more)

        def on_err(error):
            self.set_status(friendly_error(error), kind="error")

        self._run_async(work, on_ok=on_ok, on_err=on_err, loading_panel=self.library_panel)

    def _render_library_entries(self, category, entries, load_more):
        if category == "tracks":
            self._populate_entry_scroll(
                self.library_scroll,
                entries,
                on_primary=lambda entry: self._run_action(
                    self._action_play_track,
                    entry,
                    go_now=True,
                ),
                actions=self._track_action_specs(),
                load_more=load_more,
                thumbs=True,
                highlight_now=True,
            )
        elif category == "albums":
            self._populate_entry_scroll(
                self.library_scroll,
                entries,
                on_primary=lambda entry: self._on_library_selected(entry, category),
                actions=[
                    {"text": "Play", "handler": self._action_play_album},
                    {
                        "text": "Save",
                        "handler": self._action_save_album,
                        "active": lambda entry: bool(entry.get("saved")),
                    },
                ],
                load_more=load_more,
            )
        elif category == "artists":
            self._populate_entry_scroll(
                self.library_scroll,
                entries,
                on_primary=lambda entry: self._on_library_selected(entry, category),
                actions=[
                    {"text": "Play", "handler": self._action_play_album},
                    {
                        "text": "Follow",
                        "handler": self._action_follow_artist,
                        "active": lambda entry: bool(entry.get("followed")),
                    },
                ],
                load_more=load_more,
            )
        elif category == "playlists":
            self._populate_entry_scroll(
                self.library_scroll,
                entries,
                on_primary=lambda entry: self._on_library_selected(entry, category),
                actions=[
                    {"text": "Play", "handler": self._action_play_album},
                    {"text": "Shuffle", "handler": self._action_shuffle_play},
                ],
                load_more=load_more,
            )
        elif category == "episodes":
            self._populate_entry_scroll(
                self.library_scroll,
                entries,
                on_primary=lambda entry: self._run_action(
                    self._action_play_track,
                    entry,
                    go_now=True,
                ),
                actions=self._search_episode_actions(),
                load_more=load_more,
                thumbs=True,
            )
        elif category == "shows":
            self._populate_entry_scroll(
                self.library_scroll,
                entries,
                on_primary=lambda entry: self._on_library_selected(entry, category),
                actions=self._search_show_actions(),
                load_more=load_more,
                thumbs=True,
            )
        elif category == "audiobooks":
            self._populate_entry_scroll(
                self.library_scroll,
                entries,
                on_primary=lambda entry: self._run_action(
                    self._action_play_album,
                    entry,
                    go_now=True,
                ),
                actions=self._search_audiobook_actions(),
                load_more=load_more,
                thumbs=True,
            )

    def _load_more_library(self, title, category):
        self._library_fetch_limit += remote_config.LIBRARY_LIST_LIMIT
        self.controller._library_cache.pop(category, None)
        self.load_library(title, category)

    def _on_library_track_selected(self, entry):
        def run():
            self.controller.play_library_item(entry["uri"], "track")
            self._show_now(None)
            self.on_poll()

        try:
            run()
        except Exception as error:
            self._handle_playback_error(error, pending_action=run)

    def _on_library_like(self, entry):
        track_id = entry.get("id")
        if not track_id:
            return
        try:
            saved = self.controller.track_is_saved(track_id)
            self.controller.toggle_save_track(track_id, saved)
            self.load_library(LIBRARY_TAB_TITLES["tracks"], "tracks")
        except Exception as error:
            self.set_status(str(error))

    def _on_library_add_playlist(self, entry):
        if entry.get("uri"):
            self._open_playlist_picker(entry["uri"])

    def _on_library_selected(self, entry, category):
        try:
            if category == "albums":
                self._browse_back_panel = "library"
                self._open_album_tracks(entry["id"], entry["title"], "library")
            elif category == "artists":
                self._open_artist_hub(entry, "library")
            elif category == "playlists":
                self._open_playlist_tracks(entry, "library")
            elif category == "shows":
                self._browse_back_panel = "library"
                self._open_show_episodes(entry["id"], entry["title"], "library")
            else:
                self._play_entry(entry)
        except Exception as error:
            self.set_status(str(error))

    def _on_device_selected(self, device_id):
        try:
            pending = self._pending_after_device
            self._pending_after_device = None
            self.controller.transfer_device(device_id, play=(pending is None))
            self.set_status("")
            if pending:
                pending()
            self._show_now(None)
            self.on_poll()
        except Exception as error:
            self.set_status(friendly_error(error), kind="error")

    def set_user(self, name):
        self.user_label.set_text(name or "Spotify")

    def set_device(self, name):
        self.device_btn_label.set_text(name or "Device")

    def set_status(self, text, kind="info"):
        self.status_label.set_text(text or "")
        if kind == "success":
            self.status_label.set_style_text_color(_hex(SUCCESS), 0)
        elif kind == "error":
            self.status_label.set_style_text_color(_hex(ERROR), 0)
        else:
            self.status_label.set_style_text_color(_hex(MUTED), 0)

    def clear_success_status(self):
        if self._status_is_success:
            self.status_label.set_text("")
            self._status_is_success = False

    def _set_track_actions_visible(self, visible):
        flag = lv.obj.FLAG.HIDDEN
        buttons = (
            self.like_btn,
            self.playlist_add_btn,
            self.artist_albums_btn,
            self.artist_follow_btn,
            self.album_save_btn,
        )
        for btn in buttons:
            if visible:
                btn.remove_flag(flag)
            else:
                btn.add_flag(flag)

    def _update_now_actions(self, state):
        item_type = state.get("item_type")
        is_track = item_type == "track"
        is_episode = item_type == "episode"
        has_album = bool(state.get("album_id")) and not is_episode
        has_artists = bool(state.get("artists")) and is_track

        self._set_track_actions_visible(is_track or has_album or has_artists or is_episode)

        if is_track:
            self.like_btn.remove_flag(lv.obj.FLAG.HIDDEN)
            self.playlist_add_btn.remove_flag(lv.obj.FLAG.HIDDEN)
            _style_chip(self.like_btn, self.like_label, active=bool(state.get("saved")))
        elif is_episode:
            self.like_btn.add_flag(lv.obj.FLAG.HIDDEN)
            self.playlist_add_btn.add_flag(lv.obj.FLAG.HIDDEN)
        else:
            self.like_btn.add_flag(lv.obj.FLAG.HIDDEN)
            self.playlist_add_btn.add_flag(lv.obj.FLAG.HIDDEN)

        if has_artists:
            self.artist_albums_btn.remove_flag(lv.obj.FLAG.HIDDEN)
            self.artist_follow_btn.remove_flag(lv.obj.FLAG.HIDDEN)
            active_artist = self._active_artist()
            if active_artist:
                _style_chip(
                    self.artist_follow_btn,
                    self.artist_follow_label,
                    active=bool(active_artist.get("followed")),
                )
        else:
            self.artist_albums_btn.add_flag(lv.obj.FLAG.HIDDEN)
            self.artist_follow_btn.add_flag(lv.obj.FLAG.HIDDEN)

        if has_album:
            self.album_save_btn.remove_flag(lv.obj.FLAG.HIDDEN)
            _style_chip(
                self.album_save_btn,
                self.album_save_label,
                active=bool(state.get("album_saved")),
            )
        else:
            self.album_save_btn.add_flag(lv.obj.FLAG.HIDDEN)

    def update_now_playing(self, state):
        self._now_state = state
        if state.get("item_id") != getattr(self, "_last_item_id", None):
            self._selected_artist = None
            self._last_item_id = state.get("item_id")

        self.track_label.set_text(state["track"] or "Nothing playing")
        self.artist_label.set_text(state["artist"] or "")
        self.album_label.set_text(state.get("album") or "")
        self.playback_flags_label.set_text(self._playback_flags(state))
        self._update_now_actions(state)
        self._update_aux_controls(state)
        self.set_device(state.get("device") or "")
        self.cover_art.set_art(state.get("art_path"))

        duration = state["duration_ms"] or 0
        progress = state["progress_ms"] or 0
        if not self._seek_dragging and self._seek_hold_until:
            if time.ticks_diff(self._seek_hold_until, time.ticks_ms()) >= 0:
                pass
            else:
                self._seek_hold_until = 0
                duration = state["duration_ms"] or 0
                progress = state["progress_ms"] or 0
                if duration > 0:
                    self.progress.set_value(
                        int(progress * 1000 / duration), lv.ANIM.OFF
                    )
                else:
                    self.progress.set_value(0, lv.ANIM.OFF)
                self.time_label.set_text(
                    "{} / {}".format(_fmt_ms(progress), _fmt_ms(duration))
                )
        elif not self._seek_dragging:
            duration = state["duration_ms"] or 0
            progress = state["progress_ms"] or 0
            if duration > 0:
                self.progress.set_value(int(progress * 1000 / duration), lv.ANIM.OFF)
            else:
                self.progress.set_value(0, lv.ANIM.OFF)
            self.time_label.set_text(
                "{} / {}".format(_fmt_ms(progress), _fmt_ms(duration))
            )

        playing = state["playing"]
        play_size = self.play_btn.get_height()
        _style_transport_primary(self.play_btn, play_size, playing=playing)
        self.play_label.set_text(lv.SYMBOL.PAUSE if playing else lv.SYMBOL.PLAY)
        self.play_label.set_style_text_color(_hex(TEXT), 0)

        if not self._device_startup_checked:
            self._device_startup_checked = True
            if not state.get("device_id") and not self._device_prompt_dismissed:
                self.prompt_for_device("No active device — select one to play")

    def _update_aux_controls(self, state):
        shuffle = bool(state.get("shuffle"))
        _style_chip(self.shuffle_btn, self.shuffle_label, active=shuffle)

        repeat = state.get("repeat") or "off"
        if repeat == "track":
            self.repeat_label.set_text("1")
        else:
            self.repeat_label.set_text(lv.SYMBOL.LOOP)
        _style_chip(self.repeat_btn, self.repeat_label, active=repeat != "off")

        volume = state.get("volume")
        if volume is not None and not self._volume_slider_busy:
            self._last_volume = int(volume)
            self.volume_slider.set_value(self._last_volume, lv.ANIM.OFF)

    def _playback_flags(self, state):
        parts = []
        item_type = state.get("item_type")
        if item_type:
            parts.append(_label_case(item_type))
        return " | ".join(parts)
