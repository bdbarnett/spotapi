import os

from spotapi.transport import get_bytes


def _exists(path):
    try:
        os.stat(path)
        return True
    except OSError:
        return False


def _mkdir(path):
    if _exists(path):
        return
    os.mkdir(path)


def _simple_hash(value):
    result = 2166136261
    for char in value:
        result ^= ord(char)
        result = (result * 16777619) & 0xFFFFFFFF
    return "{:08x}".format(result)


def _extension_from_url(url):
    path = url.split("?", 1)[0].rsplit("/", 1)[-1].lower()
    if "." in path:
        ext = path.rsplit(".", 1)[-1]
        if ext in ("jpg", "jpeg", "png", "bmp"):
            if ext == "jpeg":
                return "jpg"
            return ext
    return "jpg"


def _extension_from_bytes(data, fallback):
    if data.startswith(b"\xff\xd8"):
        return "jpg"
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return "png"
    if data.startswith(b"BM"):
        return "bmp"
    return fallback


class ArtworkCache:
    def __init__(self, directory, max_items=24):
        self.directory = directory
        self.max_items = max_items
        if self.max_items:
            self._trim_cache()

    def path_for_url(self, url):
        if not url:
            return None

        fallback_ext = _extension_from_url(url)
        base = _simple_hash(url)
        for ext in ("jpg", "png", "bmp", fallback_ext):
            path = self._cache_path(base, ext)
            if _exists(path):
                return path

        return self._download(url, base, fallback_ext)

    def _download(self, url, base, fallback_ext):
        _mkdir(self.directory)
        data = get_bytes(url, base_url="")
        ext = _extension_from_bytes(data, fallback_ext)
        path = self._cache_path(base, ext)
        tmp_path = path + ".tmp"

        with open(tmp_path, "wb") as file:
            file.write(data)

        try:
            os.remove(path)
        except OSError:
            pass
        os.rename(tmp_path, path)
        self._trim_cache()
        return path

    def _cache_path(self, base, ext):
        return self.directory + "/" + base + "." + ext

    def _cached_files(self):
        if not _exists(self.directory):
            return []

        files = []
        for name in os.listdir(self.directory):
            if name.endswith(".tmp"):
                continue
            path = self.directory + "/" + name
            try:
                mtime = os.stat(path)[8]
            except OSError:
                continue
            files.append((mtime, path))
        return files

    def _trim_cache(self):
        if not self.max_items:
            return

        files = self._cached_files()
        overflow = len(files) - self.max_items
        if overflow <= 0:
            return

        files.sort()
        for mtime, path in files[:overflow]:
            try:
                os.remove(path)
            except OSError:
                pass
