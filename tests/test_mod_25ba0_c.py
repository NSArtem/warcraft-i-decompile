import os
import struct

import pytest

from wc1 import path, t4spec

pytestmark = pytest.mark.skipif(
    not (os.path.exists(path('original', 'install', 'war.exe')) and os.environ.get('WATCOM')),
    reason='needs original/ and $WATCOM')

SRC = path('src/mod_25ba0/selection_next_reference.c')


def _case(by, label, idx, pending, units):
    sel = by['_selected_units']['addr']
    mem = {
        sel: struct.pack('<8I', *units),
        by['_selection_index']['addr']: struct.pack('<H', idx),
        by['_net_event_pending']['addr']: struct.pack('<H', pending),
    }
    return t4spec.T4Case(args=(), mem=mem, label=label)


def _watch(by):
    return [(by['_selected_units']['addr'], 32),
            (by['_selection_index']['addr'], 2),
            (by['_net_event_pending']['addr'], 2)]


def test_t3_files_match():
    t4spec.assert_t3_matches(path('src/mod_25ba0'), ['selection_first.c', 'selection_set.c'])


def test_ref_mismatch_guard():
    t4spec.assert_ref_mismatch(path('src/mod_25ba0'), ['selection_next_reference.c'])


def test_selection_next():
    by = t4spec.by_link_lenient()       # one snapshot for the whole test
    full = [0x1000, 0x1004, 0x1008, 0x100c, 0x2000, 0x2004, 0x2008, 0x200c]
    cases = [
        _case(by, 'start0_p0', 0, 0, full),
        _case(by, 'start2_p1', 2, 1, full),
        _case(by, 'start4_done', 4, 0, full),
        _case(by, 'start5', 5, 1, full),
        _case(by, 'all_empty', 0, 0, [0] * 8),
        _case(by, 'skip_empty', 0, 0, [0, 0, 0x77, 0, 0x9, 0, 0, 0]),
        _case(by, 'last_only', 1, 1, [0] * 7 + [0x55]),
        _case(by, 'p1_gap', 0, 1, [1, 2, 3, 4, 0, 0, 0x66, 0]),
        _case(by, 'after_last', 3, 0, [0, 0, 0, 0x44, 0, 0, 0, 0]),
    ]
    t4spec.run_spec(SRC, 'SelectionNext_', 0x25c50, cases, watch=_watch(by))
