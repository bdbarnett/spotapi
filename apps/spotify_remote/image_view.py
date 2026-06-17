import gc

import lvgl as lv

_TJPGD_READY = False


def _hex(color):
    return lv.color_hex(color)


def _jpeg_size(data):
    index = 2
    length = len(data)
    while index + 9 < length:
        if data[index] != 0xFF:
            index += 1
            continue

        marker = data[index + 1]
        index += 2
        if marker in (0xD8, 0xD9):
            continue

        segment_size = (data[index] << 8) | data[index + 1]
        if marker in (0xC0, 0xC1, 0xC2, 0xC3):
            height = (data[index + 3] << 8) | data[index + 4]
            width = (data[index + 5] << 8) | data[index + 6]
            return width, height

        index += segment_size

    return 0, 0


def _image_descriptor(path):
    with open(path, "rb") as file:
        data = file.read()

    if data.startswith(b"\xff\xd8"):
        _ensure_tjpgd()
        width, height = _jpeg_size(data)
    else:
        width = 0
        height = 0

    if not width or not height:
        return None, None

    descriptor = lv.image_dsc_t()
    descriptor.header.magic = lv.IMAGE_HEADER_MAGIC
    descriptor.header.cf = lv.COLOR_FORMAT.RAW
    descriptor.header.w = width
    descriptor.header.h = height
    descriptor.header.stride = 0
    descriptor.data_size = len(data)
    descriptor.data = data
    return descriptor, data


def _ensure_tjpgd():
    global _TJPGD_READY
    if _TJPGD_READY:
        return
    try:
        lv.tjpgd_init()
        _TJPGD_READY = True
    except Exception:
        pass


class CoverArtView:
    def __init__(self, parent, size, bg_color, text_color):
        self.size = size
        self.path = None
        self.src = None
        self._data = None
        self._descriptor = None

        self.container = lv.obj(parent)
        self.container.set_size(size, size)
        self.container.set_style_bg_color(_hex(bg_color), 0)
        self.container.set_style_border_width(0, 0)
        self.container.remove_flag(lv.obj.FLAG.SCROLLABLE)

        self.image = lv.image(self.container)
        self.image.center()

        self.placeholder = lv.label(self.container)
        self.placeholder.set_width(size - 24)
        self.placeholder.set_style_text_color(_hex(text_color), 0)
        self.placeholder.set_text("No cover art")
        self.placeholder.center()

    def align(self, align, x, y):
        self.container.align(align, x, y)

    def set_art(self, path):
        if path == self.path and self._descriptor is not None:
            return

        self._release_art()
        self.path = path
        if not path:
            self._show_placeholder("No cover art")
            return

        descriptor, data = _image_descriptor(path)
        if descriptor is not None:
            try:
                self.image.set_src(descriptor)
                self.src = descriptor
                self._descriptor = descriptor
                self._data = data
                # LVGL's TJPGD decoder renders JPEGs in tiles and does not
                # support zoom/rotation. Keep native scale and choose a
                # reasonably sized Spotify image before it reaches the view.
                self.image.set_scale(256)
                self.image.center()
                self.image.remove_flag(lv.obj.FLAG.HIDDEN)
                self.placeholder.add_flag(lv.obj.FLAG.HIDDEN)
                self.image.invalidate()
                self.container.invalidate()
                return
            except Exception:
                pass

        self._show_placeholder("Cover unavailable")

    def _release_art(self):
        self.src = None
        self._data = None
        self._descriptor = None
        gc.collect()

    def _show_placeholder(self, text):
        self._release_art()
        self.image.add_flag(lv.obj.FLAG.HIDDEN)
        self.placeholder.set_text(text)
        self.placeholder.remove_flag(lv.obj.FLAG.HIDDEN)
        self.placeholder.center()
