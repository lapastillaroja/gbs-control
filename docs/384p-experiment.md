# Experimental 24 kHz / 384p for regular GBS-Control

This branch targets ramapcsx2/gbs-control on a GBS8200/8220 with an ESP8266
controller and analog VGA output. It is NOT a RetroScaler GBSC-Pro firmware.
No hardware has been flashed or tested. First intended source: NAOMI at 480p.

## Current limits — read before flashing

This is a bench experiment, NOT MS9-ready support. The preset still produces a
nominal 24.000 kHz / 60 Hz raster (64.8 MHz clock, 2700 horizontal clocks,
400 total lines, 384 active lines). This preserves the earlier prototype;
it has NOT been retuned for the MS9. The MS9-29SU documentation describes
24.39 kHz example timing and a 24.6 kHz +/-300 Hz troubleshooting range.
Do not connect this candidate to the MS9 before revising and measuring timings.

The inherited downscale pipeline discards about half of the 480p source lines,
then interpolates approximately 240 retained lines to 384. This is NOT
full-detail 480-to-384 resampling. Feasibility of better scaling is unresolved.

Only the firmware's 480p input classification (mode 3) is supported. RGBHV
mode 15 is allowed to initialize detection with output muted, pending 480p
classification. Other applyPresets input modes and direct HD bypass are muted
while this mode is selected. These checks are NOT a complete startup/transition
safety audit. Custom slots, manual register/PLL controls, component output,
scanline effects and other advanced settings have not been qualified.

Automatic H-total matching, frame lock and automatic external-clock switching
are suppressed for this mode. Non-60 Hz sources can tear or have cadence issues.
PAL/576p, native 24 kHz input, HD input and arbitrary VGA modes are not supported.
A frequency filter such as VIDEOAMP does not replace waveform verification.

## Use and reproduce

Select **24 kHz / 384p (experimental)** in the web UI (user command J,
preference 7, preset ID 0x07). RGBHV scaling is enabled by that selection.
The OLED status identifies the preset; physical-menu selection is not added.

```sh
python3 tools/generate_384p.py
python3 tools/generate_webui.py
python3 -m unittest discover -s tests -v
pio run -e d1_mini_384p
```

The generated header derives from this repository's ntsc_downscale.h, not the
Pro preset. Host tests check timing arithmetic, active lines, scaling, polarity,
register bounds, preserved input pipeline and embedded web UI reproducibility.
They do not simulate hardware or establish CRT compatibility.

## Bench sequence

1. Record the exact GBS board and ESP8266 model; back up firmware and establish
   recovery. Check stock NAOMI 480p -> GBS-C -> Toei LCD first.
2. With the CRT disconnected, measure sync frequency, pulse widths, polarity,
   and RGB levels; test boot/reset, input loss/reconnection and mode changes.
3. Check the NAOMI test grid and image geometry. The Toei TLC-V8RD0SE's 24 kHz
   acceptance remains unconfirmed, so a blank LCD is not a definitive failure.
4. Revise the output timing for the actual MS9 revision and verify it on the
   bench, including frequency-filter behavior, before connecting the CRT.
5. Validate all ordinary presets still work and that recovery is reliable.

MS9 reference: Sega Touring Car manual, included MS9-29SU service section:
https://www.hard--candy.com/wp-content/uploads/2022/03/SegaTouringCarChampionship-1996-Sega.pdf

The dedicated build environment uses ESP8266 platform 4.2.1 and maintained
ESP32Async packages because the original web-server registry package is no
longer available. Request parameter reads are const-correct for the newer API.

Board-specific update/recovery evidence: [Project C Rev.1](project-c-rev1-recovery.md).
