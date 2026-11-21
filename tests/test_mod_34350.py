import os

import pytest

from wc1 import path, t4spec

pytestmark = pytest.mark.skipif(
    not (os.path.exists(path('original', 'install', 'war.exe')) and os.environ.get('WATCOM')),
    reason='needs original/ and $WATCOM')


def test_t3_files_match():
    files = ['resource_read_header_body2.c']
    t4spec.assert_t3_matches(path('src/mod_34350'), files)
