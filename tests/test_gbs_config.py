import importlib.util
from pathlib import Path
import unittest
ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('gbs_config', ROOT / 'tools/gbs_config.py')
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)

class ConfigTests(unittest.TestCase):
    def test_shared_register_packing(self):
        ops, wire, flags = m.encode_config({'fields': {'VDS_HSYNC_RST': 1650, 'VDS_VSYNC_RST': 410}})
        actual = {(o['segment'], o['address']): (o['mask'], o['value']) for o in ops}
        self.assertEqual(actual, {(3, 1): (255, 0x72), (3, 2): (255, 0xa6), (3, 3): (127, 0x19)})
        self.assertEqual(flags, 0)
        raw = bytearray(1440)
        for o in ops: raw[o['segment'] * 240 + o['address']] = o['value']
        decoded = m.decode_fields(raw)
        self.assertEqual(decoded['VDS_HSYNC_RST'], 1650)
        self.assertEqual(decoded['VDS_VSYNC_RST'], 410)
    def test_mask_preserves_neighbours(self):
        ops, _, _ = m.encode_config({'fields': {'VDS_VSCALE_BYPS': 1}})
        self.assertEqual(ops, [dict(segment=3, address=0, mask=32, value=32)])
        old = 0x85
        self.assertEqual((old & ~ops[0]['mask']) | ops[0]['value'], 0xa5)
    def test_invalid_configs_do_not_encode(self):
        cases = [ {'fields': {'VDS_HSYNC_RST': 1650.5}},
                  {'fields': {'VDS_HSYNC_RST': True}},
                  {'fields': {'VDS_HSYNC_RST': 4096}}, {'fields': {'missing': 1}},
                  {'registers': [dict(segment=6, address=1, value=0)]},
                  {'registers': [dict(segment=3, address=240, value=0)]},
                  {'fields': {'VDS_VSCALE_BYPS': 1}, 'registers': [dict(segment=3,address=0,mask=32,value=0)]},
                  {'fields': {'VDS_VSCALE_BYPS': 0}, 'actions': ['unknown']} ]
        for config in cases:
            with self.subTest(config=config), self.assertRaises(ValueError): m.encode_config(config)
