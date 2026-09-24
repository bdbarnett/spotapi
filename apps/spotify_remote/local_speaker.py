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


def _load_board_credentials(earful):
    if sys.platform != "esp32":
        return
    try:
        with open(CRED_FILE, "rb") as file:
            earful.set_credentials(file.read())
    except OSError:
        print("local speaker: no %s; pair once from the phone" % CRED_FILE)


class LocalSpeaker:
    def __init__(self, earful, name, device, pcm, fmt):
        self.name = name
        self.device = device
        self._earful = earful
        self._pcm = pcm
        self._service = getattr(device, "service", None)
        # 10 ms of silence keeps a queued host sink ticking until playback.
        self._silence = bytes(fmt.frame_size * fmt.rate * PUMP_MS // 1000)
        self._saved = earful.has_credentials()
        self._ticks = 0
        self._timer = lv.timer_create(self._pump, PUMP_MS, None)

    def _pump(self, _timer):
        if self._service is not None:
            self._service()
        if not self.device.playing and self._pcm.queued_size() < 4 * len(self._silence):
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
    pcm = pcm_out(fmt)
    pcm.open()
    _load_board_credentials(earful)
    device = earful.Device(name=name, bitrate=bitrate)
    device.start()
    device.attach(pcm)
    print("local speaker: %s started" % name)
    return LocalSpeaker(earful, name, device, pcm, fmt)
