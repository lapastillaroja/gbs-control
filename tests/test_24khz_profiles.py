"""Check replay profiles and generated firmware use identical, valid timing data."""
import importlib.util
import json
from pathlib import Path
import unittest
ROOT = Path(__file__).resolve().parents[1]
def module(name):
    spec = importlib.util.spec_from_file_location(name, ROOT/'tools'/f'{name}.py')
    result = importlib.util.module_from_spec(spec); spec.loader.exec_module(result); return result
class ProfilesTests(unittest.TestCase):
    def test_generated_firmware_matches_saved_profiles(self):
        self.assertEqual((ROOT/'profiles_24khz.h').read_text(), module('generate_24khz_profiles').generate())
    def test_profiles_are_encodable_and_distinct_display_geometries(self):
        encoder = module('gbs_config')
        for name, lines, total, rate in [('outrun-ms9-384p',288,412,2731),('outrun-toei-426',348,426,1554),('standard-rgbhv-384p',384,411,1024)]:
            with self.subTest(profile=name):
                config=json.loads((ROOT/'bench-configs'/f'{name}-candidate.json').read_text())
                encoder.encode_config(config)
                f=config['fields']
                self.assertEqual(f['VDS_VSYNC_RST']+1,total)
                self.assertEqual(f['VDS_DIS_VB_ST']-f['VDS_DIS_VB_SP'],lines)
                self.assertEqual(f['VDS_EXT_VB_ST'],f['VDS_DIS_VB_ST'])
                self.assertEqual(f['VDS_EXT_VB_SP'],f['VDS_DIS_VB_SP'])
                self.assertLess(f['VDS_DIS_VB_ST'],total)
                for i in range(8):
                    self.assertEqual(f[f'MADPT_VSCALE_RATE_SEG{i}']*16+f['MADPT_VSCALE_RATE_LOW'],rate)
                self.assertAlmostEqual(480*4096/(4096+rate),lines,delta=0.1)
                self.assertEqual(((f['IF_HB_ST2']-f['IF_HB_SP2'])%(f['IF_HSYNC_RST']+1))//4,f['PB_FETCH_NUM'])
                # Scaling the visible output must not read beyond the captured row.
                visible_clocks = f['VDS_DIS_HB_ST'] - f['VDS_DIS_HB_SP']
                self.assertLessEqual(visible_clocks * f['VDS_HSCALE'],
                                     f['PB_FETCH_NUM'] * 4 * 1024)

    def test_toei_43_fits_complete_source_with_proportional_width(self):
        config=json.loads((ROOT/'bench-configs/vt3-toei-52hz-candidate.json').read_text())
        module('gbs_config').encode_config(config)
        f=config['fields']
        rate=f['MADPT_VSCALE_RATE_SEG0']*16+f['MADPT_VSCALE_RATE_LOW']
        source_height=480*4096/(4096+rate)
        visible_height=f['VDS_DIS_VB_ST']-f['VDS_DIS_VB_SP']
        self.assertAlmostEqual(source_height,400,delta=0.1)
        self.assertEqual(visible_height,408)
        self.assertLess(source_height,visible_height)
        # Equal fractional rates preserve linear scaling throughout the frame.
        for i in range(8):
            self.assertEqual(f[f'MADPT_VSCALE_RATE_SEG{i}']*16+f['MADPT_VSCALE_RATE_LOW'],rate)
        # Reduce width with height relative to the previous 450-line geometry.
        self.assertAlmostEqual(688 / f['VDS_HSCALE'], source_height / 450, delta=0.002)
        self.assertLessEqual((f['VDS_DIS_HB_ST']-f['VDS_DIS_HB_SP'])*f['VDS_HSCALE'],
                             f['PB_FETCH_NUM']*4*1024)
        self.assertEqual(f['VDS_EXT_HB_ST'],f['VDS_DIS_HB_ST'])
        self.assertEqual(f['VDS_EXT_HB_SP'],f['VDS_DIS_HB_SP'])
        self.assertAlmostEqual(40500000/(f['VDS_HSYNC_RST']+1)/(f['VDS_VSYNC_RST']+1),52.2,delta=0.02)
        self.assertLess(f['VDS_DIS_VB_ST'],f['VDS_VSYNC_RST']+1)
        self.assertEqual(f['VDS_EXT_VB_ST'],f['VDS_DIS_VB_ST'])
        self.assertEqual(f['VDS_EXT_VB_SP'],f['VDS_DIS_VB_SP'])
