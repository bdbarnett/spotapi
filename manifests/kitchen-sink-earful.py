# The PyDevices kitchen sink, earful (a Spotify Connect speaker), and spotapi
# with the remote, frozen: one standalone micropython.exe (or board image)
# that is both the remote and the speaker. Assumes the workspace layout:
# ~/gh/pydevices/micropython and ~/gh/bdbarnett/{earful,spotapi}.
#   make ... FROZEN_MANIFEST=/home/brad/gh/bdbarnett/spotapi/manifests/kitchen-sink-earful.py
include("$(MPY_DIR)/../../bdbarnett/earful/manifests/kitchen-sink.py")
include("../manifest.py")
