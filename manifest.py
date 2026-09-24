# MicroPython manifest: freeze spotapi and the spotify_remote app.
#
# Every .py in both packages. A firmware that includes this runs the remote
# with no files but its config:
#   micropython -m spotify_remote [speaker-name]
# from a directory holding spotapi.local.json and tokens.json (see
# apps/spotify_remote/README.md).
package("spotapi")
package("spotify_remote", base_path="apps")
