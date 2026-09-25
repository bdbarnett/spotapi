"""Web API calls off the UI thread.

Every Spotify request used to run inside an LVGL callback, so the screen froze
for as long as the request took: 0.2-1.5 s each on an ESP32-S3, and a tap on
Next made two of them. Work submitted here runs on one background thread, in
order; its result (or error) comes back to the UI thread through a queue that
an LVGL timer drains, so LVGL is only ever touched from the UI thread.

Without a usable thread (the Windows and unix ports) the work runs on the next
LVGL tick instead, as before: the UI still works, it just blocks while it waits.
"""

import time

import lvgl as lv

import sys

try:
    import _thread
except ImportError:
    _thread = None

# Only where the interpreter has a GIL: ESP32 MicroPython and CPython. The
# unix port runs threads without one, and this app (LVGL binding and all)
# segfaulted there with the worker thread running, so it runs work inline.
if sys.implementation.name == "micropython" and sys.platform != "esp32":
    _thread = None

# The thread's stack comes from internal RAM on ESP32, which is scarce on an
# S3 with an RGB panel. Its high-water mark after TLS and JSON was ~7.8 KB.
STACK_BYTES = 12 * 1024


class Worker:
    def __init__(self, threaded=True):
        self._jobs = []
        self._done = []
        self._busy_key = None
        self.threaded = False
        # The last few jobs, (key or name, ms), for a debugging harness.
        self.recent = []
        # The unix port runs threads without a GIL, so the two queues are
        # shared under a lock (without it the desktop build segfaulted).
        self._lock = _thread.allocate_lock() if _thread is not None else None
        # The idle thread blocks on this; submit() releases it. Not a sleep
        # loop: on the ESP32 port time.sleep_ms() under one FreeRTOS tick
        # (10 ms) busy-waits holding the GIL, so a 10 ms idle poll took 90% of
        # a core and starved the UI thread (2026-09-25).
        self._wake = _thread.allocate_lock() if _thread is not None else None
        if self._wake is not None:
            self._wake.acquire()
        if threaded and _thread is not None:
            try:
                try:
                    _thread.stack_size(STACK_BYTES)
                except (AttributeError, ValueError):
                    pass
                _thread.start_new_thread(self._loop, ())
                self.threaded = True
            except (OSError, RuntimeError) as error:
                print("worker: no thread (%s); running work inline" % error)
        self._timer = lv.timer_create(self._drain, 20, None)

    def submit(self, work, done=None, key=None):
        """Run ``work()`` in the background, then ``done(value, error)`` on the UI thread.

        A ``key`` coalesces: a job still waiting with the same key is replaced,
        so a burst of volume changes or polls sends only the latest.
        """
        self._acquire()
        try:
            if key is not None:
                self._jobs = [job for job in self._jobs if job[2] != key]
            self._jobs.append((work, done, key))
        finally:
            self._release()
        if self.threaded:
            try:
                self._wake.release()
            except RuntimeError:
                pass  # already awake
        else:
            lv.async_call(lambda _d: self._run_one(), None)

    def pending(self, key):
        """True while a job with this key is queued or running."""
        self._acquire()
        try:
            if self._busy_key == key:
                return True
            for job in self._jobs:
                if job[2] == key:
                    return True
            return False
        finally:
            self._release()

    def _acquire(self):
        if self._lock is not None:
            self._lock.acquire()

    def _release(self):
        if self._lock is not None:
            self._lock.release()

    def _run_one(self):
        self._acquire()
        try:
            if not self._jobs:
                return
            work, done, key = self._jobs.pop(0)
            self._busy_key = key
        finally:
            self._release()
        value = None
        error = None
        started = time.ticks_ms()
        try:
            value = work()
        except Exception as exc:  # noqa: BLE001 - reported to the UI
            error = exc
        self.recent.append((key or getattr(work, "__name__", "?"), time.ticks_diff(time.ticks_ms(), started)))
        if len(self.recent) > 12:
            self.recent.pop(0)
        self._acquire()
        try:
            self._busy_key = None
            if done is not None:
                self._done.append((done, value, error))
        finally:
            self._release()

    def _loop(self):
        # One step below the UI thread, where the firmware lets us: at equal
        # priority the GIL never passes back to the UI while this computes.
        try:
            import earful

            prio = earful.thread_priority()
            if prio:
                earful.thread_priority(prio - 1)
        except (ImportError, AttributeError, ValueError):
            pass
        while True:
            while self._jobs:
                self._run_one()
            self._wake.acquire()  # blocks, GIL released, until submit()

    def _drain(self, _timer):
        while True:
            self._acquire()
            try:
                if not self._done:
                    return
                done, value, error = self._done.pop(0)
            finally:
                self._release()
            started = time.ticks_ms()
            try:
                done(value, error)
            except Exception as exc:  # noqa: BLE001 - keep the timer alive
                print("worker: done callback raised", repr(exc))
            spent = time.ticks_diff(time.ticks_ms(), started)
            if spent >= 20:
                self.recent.append(("ui", spent))
