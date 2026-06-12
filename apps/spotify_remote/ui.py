import lvgl as lv

WIDTH = 640
HEIGHT = 480
ACCENT = 0x1DB954
BG = 0x121212
PANEL = 0x1E1E1E
MUTED = 0xB3B3B3


def _hex(color):
    return lv.color_hex(color)


def _fmt_ms(ms):
    ms = int(ms or 0)
    total_seconds = ms // 1000
    minutes = total_seconds // 60
    seconds = total_seconds % 60
    return "{}:{:02d}".format(minutes, seconds)


class SpotifyUI:
    def __init__(self, controller, on_poll):
        self.controller = controller
        self.on_poll = on_poll
        scr = lv.screen_active()
        self._build(scr)

    def _build(self, parent):
        parent.set_style_bg_color(_hex(BG), 0)

        header = lv.obj(parent)
        header.set_size(WIDTH, 48)
        header.align(lv.ALIGN.TOP_MID, 0, 0)
        header.set_style_bg_color(_hex(PANEL), 0)
        header.set_style_border_width(0, 0)
        header.remove_flag(lv.obj.FLAG.SCROLLABLE)

        self.user_label = lv.label(header)
        self.user_label.set_text("Spotify")
        self.user_label.align(lv.ALIGN.LEFT_MID, 12, 0)

        self.device_label = lv.label(header)
        self.device_label.set_text("")
        self.device_label.align(lv.ALIGN.RIGHT_MID, -12, 0)

        self.tab_now = lv.button(parent)
        self.tab_now.set_size(120, 40)
        self.tab_now.align(lv.ALIGN.BOTTOM_LEFT, 20, -8)
        self.tab_now.add_event_cb(self._show_now, lv.EVENT.CLICKED, None)
        lv.label(self.tab_now).set_text("Now")

        self.tab_lists = lv.button(parent)
        self.tab_lists.set_size(120, 40)
        self.tab_lists.align(lv.ALIGN.BOTTOM_RIGHT, -20, -8)
        self.tab_lists.add_event_cb(self._show_lists, lv.EVENT.CLICKED, None)
        lv.label(self.tab_lists).set_text("Lists")

        self.now_panel = lv.obj(parent)
        self.now_panel.set_size(WIDTH - 32, HEIGHT - 120)
        self.now_panel.align(lv.ALIGN.TOP_MID, 0, 56)
        self.now_panel.set_style_bg_color(_hex(PANEL), 0)
        self.now_panel.set_style_border_width(0, 0)

        self.track_label = lv.label(self.now_panel)
        self.track_label.set_width(WIDTH - 64)
        self.track_label.set_long_mode(lv.label.LONG_MODE.DOTS)
        self.track_label.set_text("—")
        self.track_label.align(lv.ALIGN.TOP_MID, 0, 24)

        self.artist_label = lv.label(self.now_panel)
        self.artist_label.set_width(WIDTH - 64)
        self.artist_label.set_long_mode(lv.label.LONG_MODE.DOTS)
        self.artist_label.set_text("")
        self.artist_label.set_style_text_color(_hex(MUTED), 0)
        self.artist_label.align(lv.ALIGN.TOP_MID, 0, 64)

        self.progress = lv.bar(self.now_panel)
        self.progress.set_size(WIDTH - 96, 16)
        self.progress.align(lv.ALIGN.TOP_MID, 0, 120)
        self.progress.set_range(0, 1000)

        self.time_label = lv.label(self.now_panel)
        self.time_label.set_text("0:00 / 0:00")
        self.time_label.align(lv.ALIGN.TOP_MID, 0, 148)

        btn_row = lv.obj(self.now_panel)
        btn_row.set_size(WIDTH - 96, 72)
        btn_row.align(lv.ALIGN.BOTTOM_MID, 0, -24)
        btn_row.set_style_bg_opa(lv.OPA.TRANSP, 0)
        btn_row.set_style_border_width(0, 0)
        btn_row.remove_flag(lv.obj.FLAG.SCROLLABLE)

        self.prev_btn = self._transport_button(btn_row, "PREV", -140)
        self.play_btn = lv.button(btn_row)
        self.play_btn.set_size(96, 56)
        self.play_btn.align(lv.ALIGN.CENTER, 0, 0)
        self.play_btn.set_style_bg_color(_hex(ACCENT), 0)
        self.play_label = lv.label(self.play_btn)
        self.play_label.set_text("PLAY")
        self.play_label.center()
        self.next_btn = self._transport_button(btn_row, "NEXT", 140)

        self.prev_btn.add_event_cb(self._on_prev, lv.EVENT.CLICKED, None)
        self.play_btn.add_event_cb(self._on_play_pause, lv.EVENT.CLICKED, None)
        self.next_btn.add_event_cb(self._on_next, lv.EVENT.CLICKED, None)

        self.status_label = lv.label(self.now_panel)
        self.status_label.set_width(WIDTH - 64)
        self.status_label.set_long_mode(lv.label.LONG_MODE.DOTS)
        self.status_label.set_text("")
        self.status_label.set_style_text_color(_hex(MUTED), 0)
        self.status_label.align(lv.ALIGN.BOTTOM_MID, 0, -8)

        self.lists_panel = lv.obj(parent)
        self.lists_panel.set_size(WIDTH - 32, HEIGHT - 120)
        self.lists_panel.align(lv.ALIGN.TOP_MID, 0, 56)
        self.lists_panel.set_style_bg_color(_hex(PANEL), 0)
        self.lists_panel.set_style_border_width(0, 0)
        self.lists_panel.add_flag(lv.obj.FLAG.HIDDEN)

        self.playlist_list = lv.list(self.lists_panel)
        self.playlist_list.set_size(WIDTH - 48, HEIGHT - 140)
        self.playlist_list.align(lv.ALIGN.TOP_MID, 0, 8)

        self._show_now(None)

    def _transport_button(self, parent, text, x_offset):
        btn = lv.button(parent)
        btn.set_size(96, 56)
        btn.align(lv.ALIGN.CENTER, x_offset, 0)
        btn.set_style_bg_color(_hex(ACCENT), 0)
        label = lv.label(btn)
        label.set_text(text)
        label.center()
        return btn

    def _show_now(self, _event):
        self.now_panel.remove_flag(lv.obj.FLAG.HIDDEN)
        self.lists_panel.add_flag(lv.obj.FLAG.HIDDEN)

    def _show_lists(self, _event):
        self.now_panel.add_flag(lv.obj.FLAG.HIDDEN)
        self.lists_panel.remove_flag(lv.obj.FLAG.HIDDEN)
        self.load_playlists()

    def _on_prev(self, _event):
        try:
            self.controller.previous_track()
            self.on_poll()
        except Exception as error:
            self.set_status(str(error))

    def _on_play_pause(self, _event):
        try:
            self.controller.play_pause()
            self.on_poll()
        except Exception as error:
            self.set_status(str(error))

    def _on_next(self, _event):
        try:
            self.controller.next_track()
            self.on_poll()
        except Exception as error:
            self.set_status(str(error))

    def load_playlists(self):
        self.playlist_list.clean()
        try:
            for entry in self.controller.owned_playlists():
                item = self.playlist_list.add_button(None, entry["name"])
                item.add_event_cb(self._on_playlist_click, lv.EVENT.CLICKED, entry["uri"])
        except Exception as error:
            self.set_status(str(error))

    def _on_playlist_click(self, event):
        uri = event.get_user_data()
        try:
            self.controller.play_context(uri)
            self._show_now(None)
            self.on_poll()
        except Exception as error:
            self.set_status(str(error))

    def set_user(self, name):
        self.user_label.set_text(name or "Spotify")

    def set_status(self, text):
        self.status_label.set_text(text or "")

    def update_now_playing(self, state):
        self.track_label.set_text(state["track"] or "Nothing playing")
        self.artist_label.set_text(state["artist"] or "")
        self.device_label.set_text(state["device"] or "")

        duration = state["duration_ms"] or 0
        progress = state["progress_ms"] or 0
        if duration > 0:
            self.progress.set_value(int(progress * 1000 / duration))
        else:
            self.progress.set_value(0)

        self.time_label.set_text(
            "{} / {}".format(_fmt_ms(progress), _fmt_ms(duration))
        )

        playing = state["playing"]
        self.play_btn.set_style_bg_color(
            _hex(0xE91429 if playing else ACCENT), 0
        )
        self.play_label.set_text("PAUSE" if playing else "PLAY")
