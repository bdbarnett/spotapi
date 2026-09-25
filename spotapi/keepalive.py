"""A small HTTP/1.1 client that keeps its TLS connections open.

MicroPython's ``requests`` opens a new TCP connection and does a new TLS
handshake for every request. On an ESP32-S3 that handshake is most of a
second or more of CPU, so every tap in a remote cost one, and the remote felt
stuck. This keeps one connection per host and reuses it until the server
closes it, which is what a browser or a phone app does.

Only what spotapi needs: GET/POST/PUT/DELETE with a body, ``Content-Length``
or chunked responses, and one transparent retry when a reused connection turns
out to have been closed by the server while idle.
"""

import json
import socket

try:
    import ssl
except ImportError:
    try:
        import tls as ssl  # MicroPython's built-in; ssl is a micropython-lib wrapper
    except ImportError:  # pragma: no cover
        ssl = None

try:
    import _thread

    def _lock():
        return _thread.allocate_lock()
except ImportError:

    class _NoLock:
        def acquire(self, *_a):
            return True

        def release(self):
            pass

    def _lock():
        return _NoLock()


TIMEOUT_S = 20


class Response:
    def __init__(self, status_code, headers, content):
        self.status_code = status_code
        self.headers = headers
        self.content = content

    @property
    def text(self):
        return self.content.decode("utf-8")

    def json(self):
        return json.loads(self.content)

    def close(self):
        pass


class _Conn:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.sock = None
        self.used = 0

    def open(self):
        ai = socket.getaddrinfo(self.host, self.port, 0, socket.SOCK_STREAM)[0]
        s = socket.socket(ai[0], socket.SOCK_STREAM, ai[2])
        try:
            s.settimeout(TIMEOUT_S)
            s.connect(ai[-1])
            if hasattr(ssl, "SSLContext"):
                ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
                ctx.verify_mode = ssl.CERT_NONE
                if hasattr(ctx, "check_hostname"):
                    ctx.check_hostname = False
                s = ctx.wrap_socket(s, server_hostname=self.host)
            else:
                s = ssl.wrap_socket(s, server_hostname=self.host)
        except Exception:
            s.close()
            raise
        self.sock = s
        self.used = 0

    def close(self):
        if self.sock is not None:
            try:
                self.sock.close()
            except OSError:
                pass
        self.sock = None


def _split_url(url):
    if url.startswith("https://"):
        rest = url[8:]
        port = 443
    else:
        raise ValueError("keepalive handles https:// only: " + url)
    slash = rest.find("/")
    hostport, path = (rest, "/") if slash < 0 else (rest[:slash], rest[slash:])
    if ":" in hostport:
        host, p = hostport.split(":", 1)
        port = int(p)
    else:
        host = hostport
    return host, port, path


class _Reader:
    """Framed reads. MicroPython's stream read(n) waits for all n bytes, so
    headers come a line at a time and bodies by their exact length."""

    def __init__(self, sock):
        self.sock = sock

    def line(self):
        data = self.sock.readline()
        if not data:
            raise OSError("connection closed")
        if data.endswith(b"\r\n"):
            return data[:-2]
        return data.rstrip(b"\n")

    def exact(self, n):
        parts = []
        while n > 0:
            data = self.sock.read(n)
            if not data:
                raise OSError("connection closed")
            parts.append(data)
            n -= len(data)
        return b"".join(parts)

    def rest(self):
        parts = []
        while True:
            try:
                d = self.sock.read(4096)
            except OSError:
                break
            if not d:
                break
            parts.append(d)
        return b"".join(parts)


class Session:
    def __init__(self):
        self._conns = {}
        self._lock = _lock()

    def _conn(self, host, port):
        key = (host, port)
        c = self._conns.get(key)
        if c is None:
            c = _Conn(host, port)
            self._conns[key] = c
        return c

    def close(self):
        for c in self._conns.values():
            c.close()
        self._conns = {}

    def request(self, method, url, data=None, headers=None):
        host, port, path = _split_url(url)
        if isinstance(data, str):
            data = data.encode("utf-8")
        head = ["%s %s HTTP/1.1" % (method, path), "Host: " + host,
                "Connection: keep-alive"]
        if headers:
            for k, v in headers.items():
                if k.lower() in ("host", "connection", "content-length"):
                    continue
                head.append("%s: %s" % (k, v))
        if data is not None or method in ("POST", "PUT", "PATCH", "DELETE"):
            head.append("Content-Length: %d" % (len(data) if data else 0))
        req = ("\r\n".join(head) + "\r\n\r\n").encode("utf-8")
        self._lock.acquire()
        try:
            c = self._conn(host, port)
            for attempt in (0, 1):
                reused = c.sock is not None
                if not reused:
                    c.open()
                got_any = [False]
                try:
                    return self._exchange(c, req, data, got_any)
                except OSError:
                    c.close()
                    # A reused connection the server had already closed fails
                    # before any byte of a response: that request was never
                    # seen, so ask once more on a fresh connection.
                    if attempt == 0 and reused and not got_any[0]:
                        continue
                    raise
        finally:
            self._lock.release()

    def _exchange(self, c, req, data, got_any):
        s = c.sock
        s.write(req) if hasattr(s, "write") else s.sendall(req)
        if data:
            s.write(data) if hasattr(s, "write") else s.sendall(data)
        r = _Reader(s)
        status_line = r.line()
        got_any[0] = True
        parts = status_line.split(None, 2)
        status = int(parts[1])
        headers = {}
        while True:
            line = r.line()
            if not line:
                break
            k, _, v = line.partition(b":")
            headers[k.strip().lower().decode()] = v.strip().decode()
        if status in (204, 304) or 100 <= status < 200:
            body = b""
        elif headers.get("transfer-encoding", "").lower() == "chunked":
            chunks = []
            while True:
                size = int(r.line().split(b";")[0], 16)
                if size == 0:
                    while r.line():
                        pass
                    break
                chunks.append(r.exact(size))
                r.line()
            body = b"".join(chunks)
        elif "content-length" in headers:
            body = r.exact(int(headers["content-length"]))
        else:
            # No length: the body runs to the end of the connection.
            body = r.rest()
            headers["connection"] = "close"
        c.used += 1
        if headers.get("connection", "").lower() == "close":
            c.close()
        return Response(status, headers, body)

    def get(self, url, headers=None):
        return self.request("GET", url, None, headers)

    def post(self, url, data=None, headers=None):
        return self.request("POST", url, data, headers)

    def put(self, url, data=None, headers=None):
        return self.request("PUT", url, data, headers)

    def delete(self, url, data=None, headers=None):
        return self.request("DELETE", url, data, headers)
