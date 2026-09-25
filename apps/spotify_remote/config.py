# App tuning knobs. Adjust these for your device memory and library size.

# Cover-art files kept on disk under art_cache/ (oldest removed first).
# Set to 0 to disable the limit.
ART_CACHE_MAX_ITEMS = 24

# List-row thumbnails (smallest Spotify image, a few KB each) kept on disk
# under thumb_cache/. Set to 0 to disable the limit.
THUMB_CACHE_MAX_ITEMS = 300

# Keep cover art and thumbnails in RAM instead of on disk, up to this many
# bytes each (oldest dropped first). None: in RAM on ESP32 boards, where flash
# writes stall the display and Wi-Fi and file lookups are slow; on disk
# elsewhere. 0 forces disk.
ART_CACHE_MEMORY_BYTES = None
THUMB_CACHE_MEMORY_BYTES = None

# Saved library entries loaded per category tab (and per "Load more").
LIBRARY_LIST_LIMIT = 30

# Saved albums per page: each comes with its whole track list (~11 KB), so a
# 30-album page was 325 KB -- 15 s over a weak link on an ESP32-S3.
LIBRARY_ALBUMS_LIMIT = 10

# Tracks/albums shown in album and playlist browse views.
BROWSE_LIST_LIMIT = 30

# Artist discography page size (Dev Mode max is 10 for GET /artists/{id}/albums).
ARTIST_ALBUMS_PAGE_LIMIT = 10

# Queue entries shown (API typically returns ~20).
QUEUE_LIST_LIMIT = 30

# Recently played tracks shown.
RECENT_LIST_LIMIT = 20

# Search results (Dev Mode max is 10 per request).
SEARCH_RESULT_LIMIT = 10

# Action chips per list row before wrapping to a second chip row.
MAX_ROW_ACTIONS = 4

# Name for a local Spotify Connect speaker in this process (needs the earful
# usermod), e.g. "earful-win". None leaves it off. The first command-line
# argument overrides it: micropython.exe apps/spotify_remote/main.py earful-win
LOCAL_SPEAKER = None

# Where the local speaker's audio goes: None for this machine's own output,
# "usb" for a hosted USB sound card (e.g. a P4 running usbif's soundcard.py).
LOCAL_SPEAKER_OUTPUT = None
