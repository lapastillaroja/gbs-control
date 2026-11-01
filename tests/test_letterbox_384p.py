"""Compile-time checks of the exact helper used by bench firmware.
Set CXX to the ESP8266 compiler if no host C++ compiler is installed.
"""
from pathlib import Path
import os
import shutil
import subprocess
import tempfile
import unittest
ROOT = Path(__file__).resolve().parents[1]

class LetterboxTests(unittest.TestCase):
    def test_display_aspect_and_fractional_rate(self):
        compiler = os.environ.get('CXX') or shutil.which('c++')
        if not compiler:
            self.skipTest('Set CXX to a C++11 compiler to check firmware geometry')
        program = r'''
#include "letterbox_384p.h"
constexpr long absolute(long n) { return n < 0 ? -n : n; }
template<unsigned P, unsigned N, unsigned D> struct Check {
    static constexpr auto g = letterbox384(P);
    static_assert(g.lines + g.top + g.bottom == 384, "full raster accounted for");
    static_assert(g.bottom >= g.top && g.bottom - g.top <= 1, "centered bars");
    // Aspect error <= half an output line after rounding.
    static_assert(absolute(512L*D - long(g.lines)*N)*2 <= N, "display aspect");
    static_assert(g.rate <= 4095, "rate fits hardware field");
    // Candidate accumulator output length error < 0.1 line.
    static_assert(absolute(480L*4096 - long(g.lines)*(4096+g.rate))*10
                  < 4096+g.rate, "fractional rate rounding");
    static_assert((408-g.bottom)-(24+g.top) == g.lines, "content window");
    static_assert(408-g.bottom < 411, "window inside raster");
};
Check<0,4,3> full;
Check<1,16,9> wide;
Check<2,5,3> squarePixels;
static_assert(letterbox384(0).rate == 1024, "baseline preserved");
static_assert(letterbox384(1).top == 48, "16:9 bars");
static_assert(letterbox384(1).lines == 288, "16:9 content");
'''
        with tempfile.TemporaryDirectory() as d:
            source = Path(d) / 'geometry.cpp'
            source.write_text(program)
            subprocess.run([compiler, '-std=c++11', '-Wall', '-Wextra', '-Werror',
                            '-I', str(ROOT), '-c', str(source), '-o', str(Path(d)/'geometry.o')], check=True)

if __name__ == '__main__':
    unittest.main()
