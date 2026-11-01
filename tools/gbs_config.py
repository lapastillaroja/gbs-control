#!/usr/bin/env python3
"""Apply and verify volatile LCD bench configurations without recompiling firmware."""
import argparse
import json
import re
import time
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import ProxyHandler, build_opener

ROOT = Path(__file__).resolve().parents[1]

def field_map():
    pattern = r'typedef UReg<(0x[0-9a-fA-F]+),\s*(0x[0-9a-fA-F]+),\s*(\d+),\s*(\d+)>\s+(\w+);'
    return {name: (int(seg, 16), int(addr, 16), int(bit), int(width))
            for seg, addr, bit, width, name in re.findall(pattern, (ROOT / 'tv5725.h').read_text())}

def integer(value):
    if isinstance(value, bool) or not isinstance(value, (int, str)):
        raise ValueError('Register values must be integers or integer strings')
    return int(value, 0) if isinstance(value, str) else value

def encode_config(config, definitions=None):
    definitions = definitions or field_map()
    merged = {}
    def add(seg, addr, mask, value):
        if not 0 <= seg <= 5 or not 0 <= addr < 240 or not 1 <= mask <= 255 or not 0 <= value <= 255:
            raise ValueError('Register segment/address/mask/value out of range')
        old_mask, old_value = merged.get((seg, addr), (0, 0))
        if old_mask & mask and (old_value ^ value) & old_mask & mask:
            raise ValueError(f'Conflicting overlapping fields at {seg}:{addr:02x}')
        merged[seg, addr] = (old_mask | mask, (old_value & ~mask) | (value & mask))
    for name, value in config.get('fields', {}).items():
        if name not in definitions: raise ValueError(f'Unknown field: {name}')
        seg, addr, bit, width = definitions[name]
        value = integer(value)
        if not 0 <= value < 1 << width: raise ValueError(f'{name} does not fit {width} bits')
        for index in range(width):
            shift = (bit + index) % 8
            add(seg, addr + (bit + index) // 8, 1 << shift, ((value >> index) & 1) << shift)
    for item in config.get('registers', []):
        add(integer(item['segment']), integer(item['address']), integer(item.get('mask', 255)), integer(item['value']))
    if not 1 <= len(merged) <= 128: raise ValueError('Configuration must touch 1..128 registers')
    flags = 0
    for action in config.get('actions', []):
        if action not in ('latch_pllad', 'reset_memory'): raise ValueError(f'Unknown action: {action}')
        flags |= {'latch_pllad': 1, 'reset_memory': 2}[action]
    ops = [dict(segment=seg, address=addr, mask=mask, value=value)
           for (seg, addr), (mask, value) in merged.items()]
    encoded = ''.join(f"{o['segment']:02x}{o['address']:02x}{o['mask']:02x}{o['value']:02x}" for o in ops)
    return ops, encoded, flags

def decode_fields(registers, definitions=None):
    definitions = definitions or field_map()
    values = {}
    for name, (seg, addr, bit, width) in definitions.items():
        count = (bit + width + 7) // 8
        if addr + count <= 240:
            data = registers[seg * 240 + addr:seg * 240 + addr + count]
            values[name] = (int.from_bytes(data, 'little') >> bit) & ((1 << width) - 1)
    return values

class Device:
    def __init__(self, host):
        self.url = f'http://{host}/bench/registers'
        self.opener = build_opener(ProxyHandler({}))
    def request(self, payload=None):
        body = None if payload is None else urlencode(payload).encode()
        with self.opener.open(self.url, body, timeout=8) as response:
            return json.load(response)
    def job(self, payload):
        job_id = self.request(payload)['id']
        deadline = time.monotonic() + 15
        while time.monotonic() < deadline:
            result = self.request()
            if result['id'] != job_id: raise RuntimeError('Another client replaced the bench transaction')
            if not result['busy']: return result
            time.sleep(.15)
        raise TimeoutError('Bench transaction did not complete; query /bench/registers before retrying')
    def snapshot(self):
        result = self.job({'action': 'snapshot'})
        if not result['ok']: raise RuntimeError(result['error'])
        raw = bytes.fromhex(result['registers'])
        if len(raw) != 1440: raise RuntimeError('Incomplete register snapshot')
        result['fields'] = decode_fields(raw)
        return result

def save(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + '\n')

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--host', default='192.168.4.1')
    p.add_argument('--output', type=Path, required=True, help='Receipt/snapshot file; apply also saves .before and .undo files')
    p.add_argument('--apply', type=Path, help='JSON with fields, raw registers and optional actions')
    p.add_argument('--set', action='append', default=[], metavar='REGISTER_FIELD=VALUE')
    p.add_argument('--action', action='append', choices=['latch_pllad', 'reset_memory'], default=[])
    p.add_argument('--dry-run', action='store_true', help='Validate/encode locally without contacting hardware')
    args = p.parse_args()
    config = json.loads(args.apply.read_text()) if args.apply else {}
    config.setdefault('fields', {})
    for assignment in args.set:
        name, value = assignment.split('=', 1)
        config['fields'][name] = integer(value)
    config.setdefault('actions', []).extend(args.action)
    applying = bool(args.apply or args.set)
    encoded = encode_config(config) if applying else None
    if args.dry_run:
        if not encoded: p.error('--dry-run needs --apply or --set')
        save(args.output, {'config': config, 'ops': encoded[0], 'wire': encoded[1], 'actions': encoded[2]})
        print(args.output); return 0
    device = Device(args.host)
    before = device.snapshot()
    if not applying:
        save(args.output, before)
        print(args.output); return 0
    ops, wire, flags = encoded
    save(args.output.with_suffix('.before.json'), before)
    raw = bytes.fromhex(before['registers'])
    undo = {'registers': [dict(op, value=raw[op['segment'] * 240 + op['address']] & op['mask']) for op in ops],
            'actions': config['actions']}
    save(args.output.with_suffix('.undo.json'), undo)
    # Both pre-state and an executable undo config exist before the first write.
    result = device.job({'action': 'apply', 'ops': wire, 'actions': flags})
    result.update(config=config, ops=ops)
    save(args.output, result)
    after = bytes.fromhex(result.get('after', ''))
    verified = result['ok'] and len(after) == len(ops) and all(
        value & op['mask'] == op['value'] & op['mask'] for value, op in zip(after, ops))
    print(f"{args.output}: {'verified' if verified else 'READBACK FAILED'} ({len(ops)} registers)")
    return 0 if verified else 2

if __name__ == '__main__':
    raise SystemExit(main())
