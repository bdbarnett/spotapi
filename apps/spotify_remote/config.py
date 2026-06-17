# App tuning knobs. Adjust these for your device memory and library size.

# Cover-art files kept on disk under art_cache/ (oldest removed first).
# Set to 0 to disable the limit.
ART_CACHE_MAX_ITEMS = 24

# Saved library entries loaded per category tab.
LIBRARY_LIST_LIMIT = 30

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
