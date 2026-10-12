"""Rebuild the embedded UI reproducibly using only the Python standard library."""
from pathlib import Path
import gzip
FW = Path(__file__).resolve().parents[1]
def generate():
    data = gzip.compress((FW / 'webui.html').read_bytes(), compresslevel=9, mtime=0)
    rows = ['  ' + ', '.join(f'0x{b:02x}' for b in data[i:i+12]) + ',' for i in range(0, len(data), 12)]
    return 'const uint8_t webui_html[] PROGMEM = {\n' + '\n'.join(rows) + '\n};\nconst unsigned int webui_html_len = ' + str(len(data)) + ';\n'
if __name__ == '__main__':
    (FW / 'webui_html.h').write_text(generate())
