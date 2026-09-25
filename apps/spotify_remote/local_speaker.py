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
# How long to wait for a hosted USB sound card to enumerate.
USB_FIND_MS = 15000
# The USB host ring between earful and the bus (usbif#36). earful drains into
# it from its own task (usbif#43), so it no longer has to outlast the
# interpreter's stalls -- earful's ~5 s ring does that. What it holds plays
# after a pause or a skip, so it is short: at 2 s, pause took 2 s to be heard
# on the LCD-7 (2026-09-25).
USB_RING_MS = 400


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


class _UsbPCM:
    """earful's view of a hosted USB sound card (usbif.uac_audio output).

    The C host driver drains the ring onto the bus in real time. earful
    writes at most space() and uses try_write(), which never waits for the
    bus, so a full ring can never stall the UI.
    """

    def __init__(self, host, out):
        self._host = host  # keep the USB host running while we play
        self._out = out

    def write(self, buf):
        return self._out.try_write(buf)

    def space(self):
        return self._out.space()

    def queued_size(self):
        return self._out.queued_size()

    def service(self):
        self._out.service()

    def set_volume(self, volume):
        self._out.set_volume(volume)

    def c_sink(self):
        # earful drains into this from its own task, so the VM no longer
        # moves the bytes (usbif#43). A usbif without it raises
        # AttributeError here, and earful keeps its VM pump.
        return self._out.c_sink()

    def open(self):
        self._out.open()

    def close(self):
        self._out.close()
        self._host.stop()


def _usb_output(fmt):
    """A hosted USB sound card at fmt, or None when there is none.

    No resampling: the card must offer fmt's rate (earful's is 44.1 kHz), and
    uac_audio.output raises, listing what the card does offer, if it doesn't.
    """
    try:
        import time

        import usbif.auto
        from usbif import uac, uac_audio
    except ImportError:
        print("local speaker: no usbif in this firmware for a USB sound card")
        return None
    host = usbif.auto.host(classes=("uac",)).start()
    deadline = time.ticks_add(time.ticks_ms(), USB_FIND_MS)
    while time.ticks_diff(deadline, time.ticks_ms()) > 0:
        for dev_id, streams in uac_audio.audio_devices():
            if any(s.direction == uac.OUT for s in streams):
                try:
                    out = uac_audio.output(
                        dev_id,
                        rate=fmt.rate,
                        channels=fmt.channels,
                        bits=fmt.bits,
                        ring_ms=USB_RING_MS,
                    )
                except TypeError:
                    host.stop()
                    print("local speaker: this firmware's usbif predates ring_ms "
                          "(usbif#36); rebuild with current usbif")
                    return None
                except ValueError as error:
                    # Says what the card does offer; usbif#35 adds 44.1 kHz
                    # to the P4's sound card.
                    host.stop()
                    print("local speaker: USB sound card unusable: %s" % (error,))
                    return None
                print("local speaker: USB sound card, device %s" % (dev_id,))
                return _UsbPCM(host, out)
        time.sleep_ms(250)
    host.stop()
    print("local speaker: no USB sound card found")
    return None


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


def start(name, bitrate=160, output=None, volume=None):
    """Start a Connect speaker named name; return a LocalSpeaker or None.

    output: None for this machine's own audio (the board's, through the audio
    pump where the firmware has it, or the host's), "usb" for a hosted USB
    sound card (an S3 without a codec driving a P4 running soundcard.py).
    volume: the speaker's volume (0-100) before anything sets one; None keeps
    earful's default (100).
    """
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
    if output == "usb":
        pcm = _usb_output(fmt)
        if pcm is None:
            return None
    else:
        pcm = _pump_output(fmt)
        if pcm is None:
            pcm = pcm_out(fmt)
    pcm.open()
    _load_board_credentials(earful)
    device = earful.Device(name=name, bitrate=bitrate)
    if volume is not None:
        # Before start(): earful hands it to the session, which reports it
        # to Spotify and scales the audio by it.
        device.volume = volume
    device.start()
    device.attach(pcm)
    print("local speaker: %s started" % name)
    return LocalSpeaker(earful, name, device, pcm, fmt)
