import os

import pytest

from wc1 import t4spec, path

pytestmark = pytest.mark.skipif(
    not (os.path.exists(path('original', 'install', 'war.exe')) and os.environ.get('WATCOM')),
    reason='needs original/ and $WATCOM')


def test_t3_files_still_match():
    t4spec.assert_t3_matches(path('src/mod_339d0'), ['palette_begin_fade.c'])
