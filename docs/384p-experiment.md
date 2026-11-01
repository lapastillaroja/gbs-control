# Experimental24kHz output for regular GBS-Control

This branch targets the regular GBS8200/8220 with an ESP8266 controller, not
GBSC Pro. Firmware support includes a24kHz UI selection, fractional vertical
downscaling, explicit RGBHV scaling selection, and persistent source/display
profiles. See [profiles and qualification](24khz-app-profiles.md).

The384-line path uses fractional480→384 conversion rather than first discarding
every other source line. Fractional rate1024, decimation0, Y/UV scaling enabled
and VDS vertical interpolation bypassed implement the candidate conversion.
Source capture width, memory stride and output geometry are profile-specific.

## Build

```sh
python3 -m venv .venv
.venv/bin/pip install platformio==6.2.0
.venv/bin/pio run -e d1_mini_384p
# Optional diagnostic firmware:
.venv/bin/pio run -e d1_mini_bench
```

Normal builds omit volatile bench-register HTTP access. Bench builds enable
the [register transaction API](live-bench-config.md). Both include the same
user-facing profiles. Building does not flash the device.

## Generated files and tests

```sh
python3 tools/generate_384p.py
python3 tools/generate_24khz_profiles.py
python3 tools/generate_webui.py
python3 -m unittest discover -s tests -v
node tests/test_24khz_ui.js
```

The geometry compile check requires a C++ compiler (`CXX` may select one).
No MS9 hardware qualification is claimed. Nominal/internal frequency readbacks
are not connector-level measurements. The Toei's short-raster repetition is
unresolved at the standard near60Hz timing; its separate profile uses a lower
refresh rate and deliberate cropping.

Private findings, successful/failed trials, camera tooling, recovery notes and
notebook setup are maintained in
[gbs-bench](https://github.com/lapastillaroja/gbs-bench).
