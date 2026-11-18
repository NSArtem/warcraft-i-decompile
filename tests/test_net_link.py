"""Structural tests for the two-player link ring layer.

Area = module mod_12c70's ring code (0x12c70..0x12d7c; names in
analysis/symbols/net_link.toml): the link state reset, the two slot counters,
the outstanding-message count and the two ring searches.  The send helper
NetSendMessage 0x131d8 and its callers are covered by
tests/test_save_score.py.

All six functions are T3 (byte-identical C under Watcom 10.0a); this file
re-checks that so a compiler or flag change cannot silently break them.
"""
import os

import pytest

from wc1 import match, path, symbols

HAVE = os.path.exists(path("original", "install", "war.exe")) and bool(os.environ.get("WATCOM"))
pytestmark = pytest.mark.skipif(not HAVE, reason="needs original/ and $WATCOM (nix develop)")

BUILT = [path("src", "mod_12c70", "net_reset_link.c"),
         path("src", "mod_12c70", "net_next_recv_slot.c"),
         path("src", "mod_12c70", "net_next_send_slot.c"),
         path("src", "mod_12c70", "pending_message_count.c"),
         path("src", "mod_12c70", "net_find_sent_record.c"),
         path("src", "mod_12c70", "net_find_received_record.c")]


@pytest.fixture(scope="module")
def prog():
    from wc1 import codegen_sweep
    return codegen_sweep.program()


@pytest.mark.parametrize("src", BUILT)
def test_built_c_matches(prog, src):
    """Every function in the built files is byte-identical (T3)."""
    flags = match.file_cflags(src)
    out = path("build", "mod_12c70",
               "t3_" + os.path.splitext(os.path.basename(src))[0] + ".obj")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    mod = match.compile_c(src, flags, out)
    funcs, datas, _ = symbols.load()
    by_link = {e["link_name"]: e for t in (funcs, datas) for e in t.values()}
    res = match.match_module(prog, mod, by_link)
    assert res, "no functions found"
    bad = [(n, s, p) for n, s, p in res if s != "MATCH"]
    assert not bad, bad


def test_ring_layout_constants():
    """The ring sizes the C relies on: 10 x 136 and 4 x 136 bytes, which is
    what NetResetLink's two memsets clear (0x550 / 0x220)."""
    src = path("src", "include", "net_link.h")
    text = open(src).read()
    assert "#define NET_SEND_SLOTS 10" in text
    assert "#define NET_RECV_SLOTS 4" in text
    assert "unsigned char payload[0x80]" in text      # 8 + 0x80 = 0x88
