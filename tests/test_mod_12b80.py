import os

import pytest

from wc1 import path, t4spec


pytestmark = pytest.mark.skipif(not (os.path.exists(path('original','install','war.exe')) and os.environ.get('WATCOM')), reason='needs original/ and $WATCOM')


def test_t3_matches():
    t4spec.assert_t3_matches(path('src/mod_12b80'), ['check_dos_block_marker.c', 'compute_bios_drive_fingerprint.c'])
