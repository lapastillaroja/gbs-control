# Project C Rev.1: firmware updates and recovery evidence

Checked 2026-10-25. Record verified findings and unresolved questions here as
hardware testing progresses. Do not turn generic ESP8266 advice into a confirmed
Project C pinout.

## Hardware reported by the owner

- GBS8200 with a GBS-Control Rev.1 add-on, no USB connector.
- Six through-holes labelled GND, RXD, TXD, IO, RST, 3.3V.
- These labels are user observations, not a verified schematic. The Project C
  Rev.1 documentation below is the candidate board documentation; exact module
  identity and pad routing have not been independently established.
- Linux host. No original flash backup or wired recovery test has been made.

## Manufacturer manual

Project C, **GBS-Control アドオン基板**, third edition, 2022-09-23,
linked from the Kadenken Rev.1 product page:

- [Rev.1 product page](https://www.kadenken.com/view/item/000000001457)
- [Manufacturer PDF: GBSアドオンボードv2rev1.pdf](https://www.dropbox.com/s/2nd1mhx3ymeodpi/GBS%E3%82%A2%E3%83%89%E3%82%AA%E3%83%B3%E3%83%9C%E3%83%BC%E3%83%89v2rev1.pdf?dl=0)

The two-page manual was downloaded and read. It documents:

- A preprogrammed Wi-Fi add-on fitted over the GBS board's MTV230M PLCC IC;
  pin-1 dot orientation must match.
- Settings via Wi-Fi; the GBS board's tactile buttons no longer function.
- SSID `gbscontrol`, password `qqqqqqqq`.
- Web access at `http://gbscontrol.local/` or `http://192.168.4.1/`.
- Input requirements stated by the maker: sync at most 3.3 Vp-p and RGB 0.7 Vp-p.
  These are video-input specifications, not a programming-header pinout.

**The manual does not document the six-pad header, IO-to-GPIO mapping, serial
programming wiring, power arrangement for programming, or bootloader entry.**
It therefore does not establish that the pad labelled IO is GPIO0, or that
shorting any particular pads is the correct recovery procedure.

## Firmware author's documented update method

- [tceoo1/gbs-control README](https://github.com/tceoo1/gbs-control#readme)
  explicitly identifies standard ESP8266 ArduinoOTA (`espota.py`) as the update
  protocol. Its release firmware includes Neo Geo synchronization changes; it
  is not our experimental 384p firmware and may differ from the shipped version.
- [tceoo1/espota README](https://github.com/tceoo1/espota#readme) describes its
  .NET command-line implementation and Windows-only WPF GUI.
- [KVClab instructions](https://kvclab.com/shopdetail/000000000430/) specify
  enabling OTA through the lightning menu, then uploading the release
  `gbs-control-d1_mini.bin`. Its instructions target Project C hardware.

Linux can use the standard Python uploader. From the repository root, after
connecting to the board's Wi-Fi and selecting EnableOTA:

```sh
python3 tools/espota.py -i 192.168.4.1 -f /absolute/path/to/verified-firmware.bin -r
```

This is an upload command, not a backup command. Choose an image verified for
this board before executing it. An OTA rollback requires firmware that still
boots, networking that works, and an available OTA service. A reset/power cycle
does not reinstall the old firmware.

## Wired recovery: not yet verified for this board

[Espressif esptool documentation](https://docs.espressif.com/projects/esptool/en/latest/esp8266/esptool/basic-commands.html)
confirms serial flash reading and writing on ESP8266 devices. This establishes
a chip-level capability, not this add-on's header wiring or accessible recovery
procedure. The earlier conversational suggestions to cross TX/RX, power the
assembled board normally, and ground IO during reset were generic suggestions;
they are NOT established Project C Rev.1 instructions and should not be used as
such.

Before experimental flashing, establish:

1. Exact board/module identity and the documented header mapping.
2. Programming power requirements and bootloader entry procedure.
3. Serial connection and detected flash size.
4. A full flash backup, read twice and compared, stored privately with its hash.
   Full flash can include Wi-Fi credentials; do not commit it to this repository.
5. A compatible known-good image and a verified restoration procedure.

Unresolved: no official wired-recovery procedure was found in the checked
manufacturer manual, firmware README, updater README or retailer instructions.
Maker clarification or additional schematic/documentation is still needed;
no recovery wiring is prescribed here. No message has been sent to the maker.

## Experiment status

See [384p bench notes](384p-experiment.md). The regular GBS-Control branch builds
for `d1_mini_384p`; compilation and six host tests passed on 2026-10-24.
This does not establish compatibility with this particular add-on's flash layout
or physical hardware. The 24.000 kHz timing is not MS9-ready, and scaling still
uses the temporary 480 -> approximately 240 -> 384 pipeline. Nothing has been
flashed by the assistant. The owner plans stock 240p testing with Lindbergh VT3;
no result is recorded yet.
