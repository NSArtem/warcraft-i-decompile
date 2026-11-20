import os
import struct

import pytest

from wc1 import path, t4spec

pytestmark = pytest.mark.skipif(
    not (os.path.exists(path('original', 'install', 'war.exe')) and os.environ.get('WATCOM')),
    reason='needs original/ and $WATCOM')

SRC = path('src/mod_25ba0/selection_next_reference.c')


def _addr(name):
    return t4spec.by_link_lenient()[name]['addr']


def _case(label, idx, pending, units):
    sel = _addr('_selected_units')
    mem = {
        sel: struct.pack('<8I', *units),
        _addr('_selection_index'): struct.pack('<H', idx),
        _addr('_net_event_pending'): struct.pack('<H', pending),
    }
    return t4spec.T4Case(args=(), mem=mem, label=label)


def _watch():
    return [(_addr('_selected_units'), 32),
            (_addr('_selection_index'), 2),
            (_addr('_net_event_pending'), 2)]


def test_t3_files_match():
    t4spec.assert_t3_matches(path('src/mod_25ba0'), ['selection_first.c', 'selection_set.c'])


def test_ref_mismatch_guard():
    t4spec.assert_ref_mismatch(path('src/mod_25ba0'), ['selection_next_reference.c'])


def test_selection_next():
    full = [0x1000, 0x1004, 0x1008, 0x100c, 0x2000, 0x2004, 0x2008, 0x200c]
    cases = [
        _case('start0_p0', 0, 0, full),
        _case('start2_p1', 2, 1, full),
        _case('start4_done', 4, 0, full),
        _case('start5', 5, 1, full),
        _case('all_empty', 0, 0, [0] * 8),
        _case('skip_empty', 0, 0, [0, 0, 0x77, 0, 0x9, 0, 0, 0]),
        _case('last_only', 1, 1, [0] * 7 + [0x55]),
        _case('p1_gap', 0, 1, [1, 2, 3, 4, 0, 0, 0x66, 0]),
        _case('after_last', 3, 0, [0, 0, 0, 0x44, 0, 0, 0, 0]),
    ]
    t4spec.run_spec(SRC, 'SelectionNext_', 0x25c50, cases, watch=_watch())
