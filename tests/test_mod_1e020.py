import os

import pytest

from wc1 import path, t4spec


pytestmark = pytest.mark.skipif(not (os.path.exists(path('original','install','war.exe')) and os.environ.get('WATCOM')), reason='needs original/ and $WATCOM')


def test_t3_matches():
    t4spec.assert_t3_matches(path('src/mod_1e020'), ['show_splash_screen.c'])
