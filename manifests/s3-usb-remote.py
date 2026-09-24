# The remote and a Connect speaker on a codec-less ESP32-S3 panel, playing
# through a hosted USB sound card: LVGL with displayif (the RGB panel's
# dotclockframebuffer, jpegio), usbif (the UAC host), earful, and spotapi with
# the remote. Much smaller than the kitchen sink, which doesn't fit an 8 MB S3.
# Assumes the workspace layout: ~/gh/pydevices/{micropython,micropython-pydevices,
# usbif} and ~/gh/bdbarnett/{earful,spotapi}.
#   make ... FROZEN_MANIFEST=/home/brad/gh/bdbarnett/spotapi/manifests/s3-usb-remote.py
include("$(MPY_DIR)/../micropython-pydevices/manifests/lvgl.py")
include("$(MPY_DIR)/../usbif/manifest.py")
include("$(MPY_DIR)/../../bdbarnett/earful/manifest.py")
include("../manifest.py")
