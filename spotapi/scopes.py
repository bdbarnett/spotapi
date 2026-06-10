USER_PROFILE_SCOPES = (
    "user-read-email",
)

LIBRARY_READ_SCOPES = (
    "user-library-read",
)

LIBRARY_WRITE_SCOPES = (
    "user-library-modify",
)

PLAYLIST_READ_SCOPES = (
    "playlist-read-private",
)

PLAYLIST_WRITE_SCOPES = (
    "playlist-modify-private",
    "playlist-modify-public",
    "ugc-image-upload",
)

PLAYBACK_READ_SCOPES = (
    "user-read-playback-state",
    "user-read-currently-playing",
    "user-read-recently-played",
    "user-top-read",
)

PLAYBACK_WRITE_SCOPES = (
    "user-modify-playback-state",
)

FOLLOW_WRITE_SCOPES = (
    "user-follow-modify",
)

EXAMPLE_SCOPES = (
    USER_PROFILE_SCOPES
    + LIBRARY_READ_SCOPES
    + LIBRARY_WRITE_SCOPES
    + PLAYLIST_READ_SCOPES
    + PLAYLIST_WRITE_SCOPES
    + PLAYBACK_READ_SCOPES
    + PLAYBACK_WRITE_SCOPES
    + FOLLOW_WRITE_SCOPES
)
