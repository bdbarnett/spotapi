import argparse

try:
    from generate_object_specs import DEFAULT_SCHEMA_URL, load_schema
except ImportError:
    from scripts.generate_object_specs import DEFAULT_SCHEMA_URL, load_schema


IMPLEMENTED_ENDPOINTS = (
    ("DELETE", "/me/albums"),
    ("DELETE", "/me/audiobooks"),
    ("DELETE", "/me/episodes"),
    ("DELETE", "/me/following"),
    ("DELETE", "/me/library"),
    ("DELETE", "/me/shows"),
    ("DELETE", "/me/tracks"),
    ("DELETE", "/playlists/{playlist_id}/followers"),
    ("DELETE", "/playlists/{playlist_id}/items"),
    ("DELETE", "/playlists/{playlist_id}/tracks"),
    ("GET", "/albums"),
    ("GET", "/albums/{id}"),
    ("GET", "/albums/{id}/tracks"),
    ("GET", "/artists"),
    ("GET", "/artists/{id}"),
    ("GET", "/artists/{id}/albums"),
    ("GET", "/artists/{id}/related-artists"),
    ("GET", "/artists/{id}/top-tracks"),
    ("GET", "/audio-analysis/{id}"),
    ("GET", "/audio-features"),
    ("GET", "/audio-features/{id}"),
    ("GET", "/audiobooks"),
    ("GET", "/audiobooks/{id}"),
    ("GET", "/audiobooks/{id}/chapters"),
    ("GET", "/browse/categories"),
    ("GET", "/browse/categories/{category_id}"),
    ("GET", "/browse/categories/{category_id}/playlists"),
    ("GET", "/browse/featured-playlists"),
    ("GET", "/browse/new-releases"),
    ("GET", "/chapters"),
    ("GET", "/chapters/{id}"),
    ("GET", "/episodes"),
    ("GET", "/episodes/{id}"),
    ("GET", "/markets"),
    ("GET", "/me"),
    ("GET", "/me/albums"),
    ("GET", "/me/albums/contains"),
    ("GET", "/me/audiobooks"),
    ("GET", "/me/audiobooks/contains"),
    ("GET", "/me/episodes"),
    ("GET", "/me/episodes/contains"),
    ("GET", "/me/following"),
    ("GET", "/me/following/contains"),
    ("GET", "/me/library/contains"),
    ("GET", "/me/player"),
    ("GET", "/me/player/currently-playing"),
    ("GET", "/me/player/devices"),
    ("GET", "/me/player/queue"),
    ("GET", "/me/player/recently-played"),
    ("GET", "/me/playlists"),
    ("GET", "/me/shows"),
    ("GET", "/me/shows/contains"),
    ("GET", "/me/top/{type}"),
    ("GET", "/me/tracks"),
    ("GET", "/me/tracks/contains"),
    ("GET", "/playlists/{playlist_id}"),
    ("GET", "/playlists/{playlist_id}/followers/contains"),
    ("GET", "/playlists/{playlist_id}/images"),
    ("GET", "/playlists/{playlist_id}/items"),
    ("GET", "/playlists/{playlist_id}/tracks"),
    ("GET", "/recommendations"),
    ("GET", "/recommendations/available-genre-seeds"),
    ("GET", "/search"),
    ("GET", "/shows"),
    ("GET", "/shows/{id}"),
    ("GET", "/shows/{id}/episodes"),
    ("GET", "/tracks"),
    ("GET", "/tracks/{id}"),
    ("GET", "/users/{user_id}"),
    ("GET", "/users/{user_id}/playlists"),
    ("POST", "/me/player/next"),
    ("POST", "/me/player/previous"),
    ("POST", "/me/player/queue"),
    ("POST", "/me/playlists"),
    ("POST", "/playlists/{playlist_id}/items"),
    ("POST", "/playlists/{playlist_id}/tracks"),
    ("POST", "/users/{user_id}/playlists"),
    ("PUT", "/me/albums"),
    ("PUT", "/me/audiobooks"),
    ("PUT", "/me/episodes"),
    ("PUT", "/me/following"),
    ("PUT", "/me/library"),
    ("PUT", "/me/player"),
    ("PUT", "/me/player/pause"),
    ("PUT", "/me/player/play"),
    ("PUT", "/me/player/repeat"),
    ("PUT", "/me/player/seek"),
    ("PUT", "/me/player/shuffle"),
    ("PUT", "/me/player/volume"),
    ("PUT", "/me/shows"),
    ("PUT", "/me/tracks"),
    ("PUT", "/playlists/{playlist_id}"),
    ("PUT", "/playlists/{playlist_id}/followers"),
    ("PUT", "/playlists/{playlist_id}/images"),
    ("PUT", "/playlists/{playlist_id}/items"),
    ("PUT", "/playlists/{playlist_id}/tracks"),
)


def main():
    parser = argparse.ArgumentParser(description="Compare SpotifyClient endpoint coverage to the OpenAPI schema.")
    parser.add_argument("--schema", default=DEFAULT_SCHEMA_URL, help="OpenAPI schema URL or local file path")
    args = parser.parse_args()

    schema = load_schema(args.schema)
    report = endpoint_coverage(schema)

    print("openapi endpoints:", len(report["openapi"]))
    print("implemented endpoints:", len(report["implemented"]))
    print("covered endpoints:", len(report["covered"]))
    print("missing endpoints:", len(report["missing"]))

    if report["missing"]:
        print()
        print("missing:")
        for method, path, operation_id in report["missing"]:
            print(method, path, operation_id)

    if report["extra"]:
        print()
        print("implemented_not_in_schema:")
        for method, path in report["extra"]:
            print(method, path)


def endpoint_coverage(schema, implemented=IMPLEMENTED_ENDPOINTS):
    openapi = openapi_endpoints(schema)
    implemented_set = set(implemented)
    openapi_keys = set((method, path) for method, path, operation_id in openapi)

    missing = tuple(item for item in openapi if (item[0], item[1]) not in implemented_set)
    covered = tuple(item for item in openapi if (item[0], item[1]) in implemented_set)
    extra = tuple(sorted(implemented_set - openapi_keys))

    return {
        "openapi": openapi,
        "implemented": tuple(sorted(implemented_set)),
        "covered": covered,
        "missing": missing,
        "extra": extra,
    }


def openapi_endpoints(schema):
    endpoints = []
    for path in sorted(schema.get("paths", {})):
        methods = schema["paths"][path]
        for method in ("DELETE", "GET", "POST", "PUT"):
            operation = methods.get(method.lower())
            if operation is not None:
                endpoints.append((method, path, operation.get("operationId")))
    return tuple(endpoints)


if __name__ == "__main__":
    main()
