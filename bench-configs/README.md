# Firmware profile inputs

These JSON files generate `profiles_24khz.h`; keep them with the firmware so
normal and diagnostic builds are reproducible. See
[profile IDs and behavior](../docs/24khz-app-profiles.md).

- `standard-rgbhv-384p-candidate.json`:4:3 MS9 candidate, about59.69Hz.
- `outrun-ms9-384p-candidate.json`:16:9 MS9 candidate, about59.54Hz.
- `outrun-toei-426-candidate.json`:16:9 Toei, about57.59Hz.
- `vt3-toei-52hz-candidate.json`:4:3 Toei, about52.20Hz, full-picture scaling with proportional width reduction.

MS9 profiles remain unqualified on actual CRT hardware.

Use `python3 tools/generate_24khz_profiles.py` after changing these files.
`tools/gbs_config.py --apply FILE --output RECEIPT` can replay one on an
already-running compatible bench build. It saves a before snapshot and undo
transaction first. Whole snapshots include status/reset fields and must not
be replayed indiscriminately.

Experimental-only configurations and hardware workflows live in the private
[gbs-bench repository](https://github.com/lapastillaroja/gbs-bench).
