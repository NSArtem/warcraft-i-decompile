import os

import pytest

from wc1 import path, t4spec

pytestmark = pytest.mark.skipif(not (os.path.exists(path('original','install','war.exe')) and os.environ.get('WATCOM')), reason='needs original/ and $WATCOM')


def test_t3_matches():
    t4spec.assert_t3_matches(path('src/mod_2c3f0'), ['run_setup_menu.c'])
