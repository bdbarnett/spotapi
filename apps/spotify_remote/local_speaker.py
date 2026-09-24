"""Optional local Spotify Connect speaker, so the remote can play on itself.

When the interpreter has the earful usermod, start() makes this process a
Connect speaker under the given name. It then shows up in the Devices panel
like any other speaker. Audio goes out through audiodev on the VM thread,
pumped from an LVGL timer: earful's C thread fills its PCM ring, and only
this thread may write to the audio output.

Pairing is earful's: the phone pairs once over Zeroconf and earful keeps the
credentials. On a host its C side reads them from ~/.earful/credentials (or
earful.credentials in the working directory). On a board, Python hands them
over from earful.credentials, because the C side cannot reach the VFS.
"""

import sys

import lvgl as lv

PUMP_MS = 10
CRED_FILE = "earful.credentials"
# On a board with audiodev's audio pump, how much PCM its ring holds. The pump
# plays from it on its own task; this thread only tops it up, so the UI can
# stall this long (a redraw, a Web API call) without a gap.
PUMP_RING_SECONDS = 4


def _load_board_credentials(earful):
    if sys.platform != "esp32":
        return
    try:
        with open(CRED_FILE, "rb") as file:
            earful.set_credentials(file.read())
    except OSError:
        print("local speaker: no %s; pair once from the phone" % CRED_FILE)


class _PumpPCM:
    """earful's view of an audiodev pump stream.

    earful's attach() calls write/space/service/set_volume as real methods
    (it looks them up in C, so no __getattr__). The pump's C task drains the
    ring into I2S; the board transport is never opened -- the pump owns the
    peripheral -- and is kept only for its codec volume.
    """

    def __init__(self, stream, transport, driver):
        self._stream = stream
        self._transport = transport
        self.driver = driver

    def write(self, buf):
        return self._stream.write(buf)

    def space(self):
        return self._stream.space()

    def queued_size(self):
        return self._stream.level()

    def service(self):
        pass

    def set_volume(self, volume):
        self._transport.set_volume(volume)

    def open(self):
        pass

    def close(self):
        self._stream.deinit()


def _pump_output(fmt):
    """A pump stream on this board, or None to use the board's pcm_out()."""
    try:
        from audiodev import pump
    except ImportError:
        return None
    mod = pump.module()
    if mod is None or not hasattr(mod, "Ring") or not pump.on_board():
        return None
    from boarddev import pcm_out

    # The transport publishes the board's I2S pins and codec power; find it
    # the way audiodev's AudioOut does, through any wrappers.
    transport = pcm_out(fmt)
    while transport is not None and getattr(transport, "wire", None) is None:
        transport = getattr(transport, "_inner", None)
    if transport is None:
        return None
    driver = pump.BusioDriver(
        transport.wire,
        fmt,
        power=getattr(transport, "audio_power", None),
        volume=transport.volume,
        transport=transport,
    )
    frames = 256
    capacity = max(2, fmt.rate * PUMP_RING_SECONDS // frames)
    stream = pump.attach_stream(fmt, driver=driver, frames=frames, capacity=capacity)
    print("local speaker: audio pump, %d s ring" % PUMP_RING_SECONDS)
    return _PumpPCM(stream, transport, driver)


class LocalSpeaker:
    def __init__(self, earful, name, device, pcm, fmt):
        self.name = name
        self.device = device
        self._earful = earful
        self._pcm = pcm
        self._service = getattr(device, "service", None)
        # 10 ms of silence keeps a queued host sink ticking until playback.
        self._silence = bytes(fmt.frame_size * fmt.rate * PUMP_MS // 1000)
        self._host = sys.platform != "esp32"
        self._saved = earful.has_credentials()
        self._ticks = 0
        self._timer = lv.timer_create(self._pump, PUMP_MS, None)

    def _pump(self, _timer):
        if self._service is not None:
            self._service()
        # Queued host sinks stall without a keepalive; a board's I2S does not
        # queue (queued_size() is 0), so it gets none.
        if self._host and not self.device.playing:
            if self._pcm.queued_size() < 4 * len(self._silence):
                self._pcm.write(self._silence)
        self._pcm.service()
        self._ticks += 1
        if self._ticks % 100 == 0:
            self._save_board_credentials()

    def _save_board_credentials(self):
        # A board keeps the pairing only if Python writes it; once per run.
        if self._saved or sys.platform != "esp32" or not self._earful.has_credentials():
            return
        self._saved = True
        try:
            with open(CRED_FILE, "wb") as file:
                file.write(self._earful.credentials())
        except OSError as error:
            print("local speaker: credentials not saved: %r" % (error,))

    def stop(self):
        self._timer.delete()
        self.device.stop()
        self._pcm.close()


def start(name, bitrate=160):
    """Start a Connect speaker named name; return a LocalSpeaker or None."""
    try:
        import earful
    except ImportError:
        print("local speaker: this interpreter has no earful module")
        return None
    if not earful.available():
        print("local speaker: earful is not available on this port")
        return None

    from audiodev import AudioFormat
    from boarddev import pcm_out

    # Spotify's PCM: 44.1 kHz stereo 16-bit. The default (buffered) host
    # profile rides out the pauses while the UI waits on the Web API.
    fmt = AudioFormat(44100, 2, 16)
    pcm = _pump_output(fmt)
    if pcm is None:
        pcm = pcm_out(fmt)
    pcm.open()
    _load_board_credentials(earful)
    device = earful.Device(name=name, bitrate=bitrate)
    device.start()
    device.attach(pcm)
    print("local speaker: %s started" % name)
    return LocalSpeaker(earful, name, device, pcm, fmt)
