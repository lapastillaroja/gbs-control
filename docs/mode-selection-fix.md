# Explicit VGA mode selection

Selecting a scaled output preset now enables `preferScalingRgbhv` in the shared
user-command handler. Previously, an existing passthrough preference could make
a resolution selection appear ineffective. Browser and API requests follow the
same path, and the preference is saved with the output selection.

Explicit passthrough disables that scaling preference and selects OutputBypass
before setup. Sources classified as RGBHV (14/15) enter the dedicated RGBHV
ADC-to-DAC path through applyPresets(15), rather than generic HD bypass. Bypass
entry clears pending preset application and stale scaler/HD-bypass state.

The UI places the existing experimental 24 kHz button immediately before 15 kHz
and passthrough in a separate row. The VGA setting label uses "Scaling" rather
than "Upscaling", since supported sources can also be downscaled. This change
does not broaden supported input timings or validate experimental 24 kHz output.

## Validation and scope

On 2026-11-01, regular GBS8200 plus Rev.1 add-on / Lindbergh / Toei LCD bench
runs exercised explicit 480p selection, RGBHV passthrough selection, restart,
and repeated mode transitions with these fixes in the working firmware.
Dedicated passthrough produced an image where generic HD bypass had failed.
This does not claim that passthrough noise or all geometry issues are resolved.

The selected commit was separately reconstructed over the preceding HEAD in
an isolated directory, excluding later diagnostics and scaling experiments.
Its six existing host checks passed, including generated UI consistency, and
PlatformIO d1_mini_384p compiled successfully. The isolated build was not
flashed; physical observations above came from the combined working firmware.

Later fractional 384p timing changes, bench mutation API, diagnostic additions,
and OutRun letterbox profiles are intentionally outside this commit.
