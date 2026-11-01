# Live LCD bench configuration

The `d1_mini_bench` build exposes volatile register transactions. Normal builds
have no `/bench/registers` endpoint. This is a local LCD experiment interface;
it does not validate CRT timings or automatically identify a source mode.

After installing this build once, new timing/capture/scaling experiments do not
require compiling firmware. Field names come directly from `tv5725.h`.

```sh
# Snapshot raw registers plus decoded named fields (any current output mode).
python3 tools/gbs_config.py --output /tmp/before.json

# Select experimental 384p before applying changes.
curl --noproxy '*' 'http://192.168.4.1/uc?J'

# Apply multiple fields in one queued operation, with masked readback.
python3 tools/gbs_config.py --output /tmp/trial.json \
  --set VDS_HSCALE=640 --set VDS_HB_ST=1500 --set VDS_HB_SP=150

# Restore just the fields changed by that operation.
python3 tools/gbs_config.py --apply /tmp/trial.undo.json \
  --output /tmp/restored.json
```

An apply saves `trial.before.json` and `trial.undo.json` **before writing**.
The receipt records exact requested masks, original values and readback.
This is immediate register verification, not a claim of visual correctness;
the source watcher or a later preset change can still overwrite registers.
Use `--dry-run` to validate/encode locally. A JSON configuration accepts:

```json
{
  "fields": {"VDS_HSCALE": 640, "VDS_HB_ST": 1500, "VDS_HB_SP": 150},
  "registers": [{"segment": 3, "address": "0x16", "mask": "0xff", "value": "0x80"}],
  "actions": ["reset_memory"]
}
```

Overlapping fields must agree. Actions are `latch_pllad` and `reset_memory`.
The API accepts at most 128 distinct byte registers in segments 0..5,
addresses 0x00..0xef. Writes require preference/preset 7 both when queued and
when applied. The main loop applies the batch with RGB output muted and then
restores the prior DAC power state. This avoids I2C operations in asynchronous
HTTP callbacks; it does not guarantee a seamless mode transition.
Raw writes to read-only/self-clearing registers can fail readback. A snapshot
is for inspection, not a blanket replay of status, reset, and runtime registers.
Only explicitly changed fields belong in an undo/configuration file.

Protocol: POST form data to `/bench/registers`, `action=snapshot`, or
`action=apply&ops=...&actions=0`. Each operation is eight hex digits:
segment, address, mask, value (one byte each). Action flags 1=latch PLLAD,
2=reset SDRAM. HTTP 202 returns a job id. GET the same endpoint until that id
has `busy:false`; check `ok` and the masked `before`/`after` bytes. Concurrent
clients must not run experiments on the same device.

The earlier `/bench/set` controls remain available for bounded named settings
and computed aspect/clock profiles. Their request files and camera captures
are recorded by the private `gbs-bench/tools/gbs_bench.py`; diagnostics are now checkpointed before
camera capture so interrupted captures retain register evidence.

Camera capture, OTA and notebook orchestration tools live in the private [gbs-bench repository](https://github.com/lapastillaroja/gbs-bench). The register codec remains here because firmware profile generation/tests use the same register definitions.
