# Experimental24kHz display profiles

Select a source/display in **24kHz profile**, then **Apply profile and select24kHz**.
The selection is saved; the ordinary24kHz button recalls it. Dropdown changes
alone do not apply. These are manual profiles, not automatic source/display detection.

| ID | Profile | Output | Status |
|---|---|---|---|
|0|480p4:3 MS9 candidate|384 active lines, about59.69Hz|VT3 capture tested; MS9 unverified|
|1|OutRun16:9 MS9 candidate|288 content lines, about59.54Hz|MS9 unverified|
|2|OutRun16:9 Toei LCD|348 content lines, about57.59Hz|Lindbergh/Toei geometry tested|
|3|480p4:3 Toei LCD|About450 scaled lines cropped to408 visible lines, about52.20Hz|VT3/Toei compromise; about9% total vertical crop|

Toei compensation is display-specific. It must not be used as evidence of MS9
geometry or signal compatibility. Full-screen4:3 Toei geometry at59.xxHz has
not been demonstrated without substantial cropping or repetition. High-resolution
RGBHV input is outside the tested480-line scaling path.

## Implementation

Profile IDs0–3 are appended as byte20 of `/preferencesv2.txt`. Old19-byte files
and invalid IDs default to0. Main-loop processing reapplies profiles after
preset loading and sync-watcher adjustments. IDs1–3 require RGBHV mode14 and
RGB output. ID0 applies its capture correction on that same path; other paths
retain the base preset. Reloading the base preset clears previous overrides.

`profiles_24khz.h` is generated from `bench-configs/` by
`python3 tools/generate_24khz_profiles.py`. After UI edits, run
`python3 tools/generate_webui.py`. Tests cover generation, register packing,
capture geometry, cropped-versus-scaled height, and UI request handling.

## API

- GET `/profiles/24k`: selected, active, pending, saved, mode, component.
- POST `/profiles/24k`, form `profile=0`, `1`, `2`, or `3`:202 queues application.
- Poll GET to confirm application and persistence. Invalid IDs return400; an
  already queued selection returns409.

`active` records successful software application, not continuous waveform
verification. Raw bench writes can override registers without changing the
selected ID; reload the profile to restore it.

Detailed findings, captures and notebook workflows belong to the private
[gbs-bench repository](https://github.com/lapastillaroja/gbs-bench).
