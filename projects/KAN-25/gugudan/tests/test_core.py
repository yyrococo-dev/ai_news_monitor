import sys
from pathlib import Path
# ensure projects/KAN-25 is on sys.path so 'gugudan' package imports correctly
root = Path(__file__).resolve().parents[2]
if str(root) not in sys.path:
    sys.path.insert(0, str(root))

import sys
from pathlib import Path
# ensure project/gugudan dir on sys.path
root = Path(__file__).resolve().parents[2]
modpath = root / 'gugudan'
if str(modpath) not in sys.path:
    sys.path.insert(0, str(modpath))

import core


def test_generate_dan_lines():
    g1 = core.generate_dan(1)
    assert g1[0] == '1 x 1 = 1'
    assert g1[-1] == '1 x 9 = 9'
    g2 = core.generate_dan(2)
    assert g2[0] == '2 x 1 = 2'
    assert g2[-1] == '2 x 9 = 18'


def test_build_full_output_exact():
    expected = '\n'.join([
        '1 x 1 = 1','1 x 2 = 2','1 x 3 = 3','1 x 4 = 4','1 x 5 = 5','1 x 6 = 6','1 x 7 = 7','1 x 8 = 8','1 x 9 = 9',
        '',
        '2 x 1 = 2','2 x 2 = 4','2 x 3 = 6','2 x 4 = 8','2 x 5 = 10','2 x 6 = 12','2 x 7 = 14','2 x 8 = 16','2 x 9 = 18',
    ]) + '\n'
    out = core.build_full_output(2)
    assert out == expected
