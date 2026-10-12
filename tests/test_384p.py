"""Host checks of the actual generated TV5725 register image and embedded UI."""
from pathlib import Path
import gzip
import importlib.util
import re
import unittest
ROOT = Path(__file__).resolve().parents[1]
FW = ROOT

def registers(name):
    return {(int(s), int(a, 16)): int(v, 16) for v, s, a in
            re.findall(r'(0x[0-9a-fA-F]+),\s*//\s*s(\d)_([0-9a-fA-F]+)', (FW / name).read_text())}

def field(regs, name):
    match = re.search(r'UReg<(0x\w+), (0x\w+), (\d+), (\d+)> ' + name + r'\s*;', (FW / 'tv5725.h').read_text())
    segment, address, offset, width = (int(x, 0) for x in match.groups())
    packed = sum(regs.get((segment, address+i), 0) << (8*i) for i in range(3))
    return (packed >> offset) & ((1 << width)-1)

class TimingTests(unittest.TestCase):
    def setUp(self):
        self.regs = registers('ntsc_384p.h')
    def test_nominal_frequencies(self):
        self.assertEqual(field(self.regs, 'PLL648_CONTROL_01'), 0x55)
        h = field(self.regs, 'VDS_HSYNC_RST')
        v = field(self.regs, 'VDS_VSYNC_RST')
        self.assertEqual(64800000 / h, 24000)
        self.assertEqual(64800000 / h / v, 60)
    def test_active_lines_and_scaling(self):
        self.assertEqual(field(self.regs, 'VDS_DIS_VB_ST') - field(self.regs, 'VDS_DIS_VB_SP'), 384)
        self.assertEqual(field(self.regs, 'VDS_VSCALE_BYPS'), 0)
        self.assertEqual(240 * 1024 / field(self.regs, 'VDS_VSCALE'), 384)
        self.assertEqual(field(self.regs, 'GBS_PRESET_ID'), 7)
    def test_negative_sync_and_bounds(self):
        for axis, bits in [('H', 12), ('V', 11)]:
            total = field(self.regs, f'VDS_{axis}SYNC_RST')
            start = field(self.regs, f'VDS_{axis}S_ST')
            stop = field(self.regs, f'VDS_{axis}S_SP')
            self.assertLess(stop, start)
            self.assertLess(start, total)
            self.assertLess(total, 2**bits)
            for suffix in ['B_ST', 'B_SP', 'S_ST', 'S_SP']:
                self.assertLess(field(self.regs, f'VDS_{axis}{suffix}'), total)
    def test_capture_pipeline_unchanged(self):
        original = registers('ntsc_downscale.h')
        self.assertEqual(set(original), set(self.regs))
        for key, value in original.items():
            if key[0] not in (0, 1, 3) or (key[0] == 0 and key[1] != 0x41) or (key[0] == 1 and key[1] != 0x2b):
                self.assertEqual(value, self.regs[key], key)
    def test_generated_files_current(self):
        for script, output in [('generate_384p', 'ntsc_384p.h'), ('generate_webui', 'webui_html.h')]:
            spec = importlib.util.spec_from_file_location(script, ROOT / 'tools' / (script + '.py'))
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            self.assertEqual(module.generate(), (FW / output).read_text())
    def test_served_ui_matches_source(self):
        data = bytes(int(x, 16) for x in re.findall(r'0x([0-9a-f]{2})', (FW / 'webui_html.h').read_text()))
        self.assertEqual(gzip.decompress(data), (FW / 'webui.html').read_bytes())
        html = gzip.decompress(data).decode()
        self.assertIn('gbs-message="J" gbs-message-type="user"', html)
        self.assertIn('7: "button24kHzScaleDown"', html)

if __name__ == '__main__':
    unittest.main()
