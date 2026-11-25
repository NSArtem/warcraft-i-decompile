"""E6 acceptance tests: no skips/xfails and no production modifications."""
from pathlib import Path
import struct
import tempfile

import pytest
from wc1 import cemu
from wc1.emu import Emu
from . import mf_cemu as mf
from .scenarios import (DIALOG, REFRESH, TIMER, FRAME, LOADER, FIXTURES, NEGATIVES,
                        ISOLATION_NEGATIVES,
                        addr, dep, options, playflic, run_options, run_playflic,
                        baseline_options, baseline_playflic, inspect_playflic,
                        exercise_negative)


def test_baseline_options():
    result = baseline_options()
    assert result['diffs'] and result['c_stubbed']
    assert result['original_callback_pointers'] == [0x1a79c, 0x1a778]
    assert all(p >= 0x800000 for p in result['compiled_callback_pointers'])


def test_baseline_playflic():
    result = baseline_playflic()
    assert result['original_stub_calls'] == 1
    assert result['compiled_stub_calls'] == 0


def test_real_call_fixup_evidence():
    result = inspect_playflic()
    # Evidence corrects the assignment's zero-FIXUPP hypothesis: Watcom
    # 10.0a actually emits one EXTDEF FIXUPP for this particular TU.
    assert result['loader_call_omf_fixups'] == 1
    assert result['direct_loader_calls'] == [dict(offset=302, size=5,
        target_offset=0, omf_fixups=[303], fixup_targets=[LOADER])]


@pytest.mark.parametrize('mode', ['isolated', 'group', 'integrated'])
@pytest.mark.parametrize('button', [0, 1])
@pytest.mark.parametrize('absent', [0, 1, 2, 3])
def test_options_modes(mode, button, absent):
    r = run_options(mode, result=button, absent=absent, net=1, race=button)
    assert r['diffs'] == []
    assert all(v > 0 for v in r['instructions'].values())
    before, after = r['params_before_c'], r['params_after_c']
    if mode == 'isolated':
        assert r['callback_pointer_values_c'] == [0x1a79c, 0x1a778]
        assert r['pointer_slots'] == 0
    else:
        assert r['pointer_slots'] == 4
        assert all(p >= 0x800000 for p in r['callback_pointer_values_c'])
        assert after[7] == before[7] + 30  # real compiled timer callback
        assert after[1] == (0 if absent & 1 else before[1])
        assert after[2] == (0 if absent & 2 else before[2])
        assert r['callbacks']['orig'] == r['callbacks']['c'] == sorted([REFRESH, TIMER])
        assert r['prefs_final_c'] == (after[:5] if button == 0 else before[:5])
    assert r['callback_abi']['orig'] == r['callback_abi']['c']
    assert len(r['callback_abi']['c']) == 2
    for event in r['callback_abi']['c']:
        assert event['preserved_deltas'] == dict.fromkeys(mf.PRESERVED_REGS, 0)
        assert event['stack_delta'] == event['stack_pop'] == 0
    if mode == 'integrated':
        assert 'SndApplyOptions_' not in r['stub_logs']['c']
        assert r['stub_logs']['c'].count('SndSetMusicVolume_') == 2
        assert r['real_callees']['orig']['SndApplyOptions_'] == 2
        assert r['real_callees']['c']['SndApplyOptions_'] == 2


@pytest.mark.parametrize('mode', ['isolated', 'group', 'integrated'])
@pytest.mark.parametrize('step', [0, 25, 26])
def test_options_timer_threshold(mode, step):
    r = run_options(mode, net=0, clock_step=step)
    assert r['diffs'] == []
    expected = 1000 + step + 25 if step > 25 and mode != 'isolated' else 1025
    assert r['params_after_c'][7] == expected


@pytest.mark.parametrize('mode', ['group', 'integrated'])
@pytest.mark.parametrize('timer,empty,terminal', [
    (0, False, False), (5, False, False), (1, False, False),
    (1, True, False), (1, False, True)])
def test_playflic_modes(mode, timer, empty, terminal):
    r = run_playflic(mode, timer=timer, empty=empty, terminal=terminal)
    assert r['diffs'] == []
    assert r['visits']['c'][FRAME] > 0 and r['visits']['c'][LOADER] > 0
    if mode == 'integrated':
        assert r['stub_logs']['c'] == []  # real TextWidth / memset downstream
        if timer == 1:
            callee = 'memset_' if empty else 'TextWidth_'
            assert r['real_callees']['orig'][callee] == 1
            assert r['real_callees']['c'][callee] == 1


def test_playflic_isolated():
    r = run_playflic('isolated')
    assert r['stub_logs']['orig'] == r['stub_logs']['c'] == [LOADER]
    assert LOADER not in r['visits']['c']


def test_zero_fixup_entry_hook():
    mod = mf.compile_fixture(FIXTURES / 'no_fixup_call.asm')
    seg = mod.segments[0]
    calls = [i for i in mf.instructions(seg.data, 0) if i.mnemonic == 'call']
    assert len(calls) == 1
    assert not any(calls[0].address <= f.offset < calls[0].address + calls[0].size
                   for f in seg.fixups)
    r = run_playflic('isolated', fixture='no_fixup_call.asm')
    assert r['diffs'] == []
    assert r['stub_logs']['orig'] == r['stub_logs']['c'] == [LOADER]


@pytest.mark.parametrize('control,reason', NEGATIVES.items())
def test_required_negatives(control, reason):
    error = mf.IsolationImpossibleError if control in ISOLATION_NEGATIVES else mf.VerificationError
    with pytest.raises(error, match=reason):
        exercise_negative(control)


@pytest.mark.parametrize('mode', ['group', 'integrated'])
@pytest.mark.parametrize('mutation,reason', [
    ('register', 'callback_register_clobber: c: ebx'),
    ('cleanup', 'callback_stack_cleanup: c')])
def test_callback_abi_before_context_restore(mode, mutation, reason):
    run, watch, fields, _ = options(mode, mutation=mutation)
    with pytest.raises(mf.VerificationError, match=reason):
        run.run_pair(DIALOG, watch=watch, pointer_fields=fields)
    # Original callbacks completed with intact registers and stack; C's first
    # callback is rejected before an event or parent-context restore can hide it.
    assert len(run.callback_abi['orig']) == 2
    assert run.callback_abi['c'] == []
    if mutation == 'register':
        assert run.emu.reg('ebx') == 0
    else:
        assert run.emu.uc.reg_read(mf.UC_X86_REG_EIP) == mf.SENTINEL


@pytest.mark.parametrize('fixture', ['trailing_entry.asm', 'trailing_entry_indirect.asm'])
def test_trailing_code_ownership_and_rejection(fixture):
    e = Emu()
    policy = mf.DependencySubstitutionPolicy({
        LOADER: dep(LOADER, lambda e: 0, mechanism='c_entry_hook')})
    cm = mf.MultiModule(e, FIXTURES / fixture, {FRAME}, policy)
    lo, hi = cm.function_ranges[LOADER]
    si, off = cm.mod.publics[LOADER]
    assert hi == cm.base[si] + cm.mod.segments[si - 1].length
    assert cm.reachable[LOADER] == {lo}  # only the first ret is reachable
    assert cm.code_owner(lo + 1) == LOADER
    decoded = mf.instructions(e.read(lo, hi - lo), lo)
    assert [(i.mnemonic, i.op_str) for i in decoded] == [
        ('ret', ''), ('mov', 'word ptr [0x59ee2], 7'), ('ret', '')]
    e.write(0x59ee2, b'\0\0')
    if fixture == 'trailing_entry.asm':
        with pytest.raises(mf.IsolationImpossibleError, match='interior_entry_bypass'):
            mf.MultiRun(e, cm, mf.make_boundary(cm, {FRAME}), 'isolated')
    else:
        run = mf.MultiRun(e, cm, mf.make_boundary(cm, {FRAME}), 'isolated')
        run.side = 'c'
        with pytest.raises(mf.IsolationImpossibleError, match='dynamic interior_entry_bypass'):
            run._execute(cm.fn(FRAME))
        assert run.visits['c'][FRAME] > 0
    assert e.read(0x59ee2, 2) == b'\0\0'


@pytest.mark.parametrize('transfer', ['jmp $$', 'call $$', 'mov eax, $$\ncall eax'])
def test_unowned_executable_prefix(transfer):
    # The static prefix misaligns whole-segment decoding. The dynamic prefix
    # is executable, so rejection must come from our hook before it runs.
    prefix = 'ret' if transfer.startswith('mov') else 'db 0x0f'
    source = ('BITS 32\nsegment _TEXT public align=16 class=CODE use32\n'
              'global IntroFrame_\n' + prefix + '\nIntroFrame_:\n' + transfer + '\nret\n')
    with tempfile.TemporaryDirectory(prefix='.gap-', dir=mf.HERE) as tmp:
        src = Path(tmp) / 'unowned.asm'
        src.write_text(source)
        e = Emu()
        cm = mf.MultiModule(e, src, {FRAME}, mf.DependencySubstitutionPolicy())
        assert cm.in_code(cm.fn(FRAME) - 1)
        assert cm.code_owner(cm.fn(FRAME) - 1) is None
        if transfer.startswith('mov'):
            run = mf.MultiRun(e, cm, mf.make_boundary(cm, {FRAME}), 'isolated')
            run.side = 'c'
            with pytest.raises(mf.IsolationImpossibleError, match='dynamic unowned executable gap'):
                run._execute(cm.fn(FRAME))
        else:
            with pytest.raises(mf.IsolationImpossibleError, match='unowned executable gap'):
                mf.MultiRun(e, cm, mf.make_boundary(cm, {FRAME}), 'isolated')


@pytest.mark.parametrize('reg', mf.PRESERVED_REGS)
def test_all_callback_preserved_registers(reg):
    # A minimal callback prevents a real prologue/epilogue from restoring the
    # deliberately clobbered register before the ABI checker sees it.
    with tempfile.TemporaryDirectory(prefix='.register-', dir=mf.HERE) as tmp:
        src = Path(tmp) / 'bad.asm'
        src.write_text('BITS 32\nsegment _TEXT public align=16 class=CODE use32\n'
                       f'global OptionsRefresh_\nOptionsRefresh_:\nxor {reg}, {reg}\nret\n')
        e = Emu()
        cm = mf.MultiModule(e, src, {REFRESH}, mf.DependencySubstitutionPolicy())
        run = mf.MultiRun(e, cm, mf.make_boundary(cm, {REFRESH}), 'isolated')
        run.side = 'c'
        request = mf.Callback(cm.fn(REFRESH))
        with pytest.raises(mf.VerificationError, match='callback_register_clobber: c: ' + reg):
            run._execute(request.address, callback_contract=request)


@pytest.mark.parametrize('stack_arg,ret_pop,expected', [
    (False, 0, None), (True, 4, None),
    (False, 4, 'callback_stack_cleanup'), (True, 0, 'callback_stack_cleanup')])
def test_callback_stack_argument_cleanup(stack_arg, ret_pop, expected):
    with tempfile.TemporaryDirectory(prefix='.stack-', dir=mf.HERE) as tmp:
        src = Path(tmp) / 'cleanup.asm'
        # Check placement of the fifth argument as well as the ret N result.
        body = 'mov eax, [esp + 4]\n' if stack_arg else 'mov eax, 17\n'
        src.write_text('BITS 32\nsegment _TEXT public align=16 class=CODE use32\n'
                       'global OptionsRefresh_\nOptionsRefresh_:\n' + body + f'ret {ret_pop}\n')
        e = Emu()
        cm = mf.MultiModule(e, src, {REFRESH}, mf.DependencySubstitutionPolicy())
        run = mf.MultiRun(e, cm, mf.make_boundary(cm, {REFRESH}), 'isolated')
        run.side = 'c'
        args = (1, 2, 3, 4, 17) if stack_arg else ()
        request = mf.Callback(cm.fn(REFRESH), args, 4 if stack_arg else 0)
        if expected:
            with pytest.raises(mf.VerificationError, match=expected):
                run._execute(request.address, args, callback_contract=request)
        else:
            assert run._execute(request.address, args, callback_contract=request) == 17
            assert run.callback_abi['c'][0]['preserved_deltas'] == dict.fromkeys(mf.PRESERVED_REGS, 0)
            assert run.callback_abi['c'][0]['stack_delta'] == request.expected_stack_pop


@pytest.mark.parametrize('side', ['orig', 'c'])
@pytest.mark.parametrize('offset', [0, 1])
def test_boundary_stub_ranges(side, offset):
    run, watch, fields, _ = options()
    f = next(f for f in run.boundary.functions if f.symbol == REFRESH)
    run.emu.stubs[getattr(f, side)[0] + offset] = lambda e: 0
    with pytest.raises(mf.VerificationError, match='boundary_stubbed'):
        run.run_pair(DIALOG, watch=watch, pointer_fields=fields)


@pytest.mark.parametrize('side', ['orig', 'c'])
def test_public_redirection(side):
    run, watch, fields, _ = options()
    if side == 'orig':
        run.cm.publics[REFRESH] = 0x1a79c
    else:
        run.cm.publics[REFRESH] = run.cm.fn(TIMER)
    with pytest.raises(mf.VerificationError, match='verified_c_redirected_to_orig'):
        run.run_pair(DIALOG, watch=watch, pointer_fields=fields)


@pytest.mark.parametrize('side', ['orig', 'c'])
def test_code_tampering(side):
    run, watch, fields, _ = options()
    # A negative audit probe, never an interception mechanism or a stub.
    a = 0x1a79c if side == 'orig' else run.cm.fn(REFRESH)
    run.emu.write(a, bytes([run.emu.read(a, 1)[0] ^ 1]))
    with pytest.raises(mf.VerificationError, match=side + '_patched'):
        run.run_pair(DIALOG, watch=watch, pointer_fields=fields)


@pytest.mark.parametrize('reason', ['trace_active', 'zero_observations', 'zero_instructions'])
def test_other_anti_cheat_invariants(reason):
    run, watch, fields, _ = options()
    if reason == 'trace_active':
        run.emu.trace = lambda *a: None
        action = lambda: run.run_pair(DIALOG, watch=watch, pointer_fields=fields)
    else:
        run.counts = {'orig': 10, 'c': 10} if reason == 'zero_observations' else {'orig': 0, 'c': 1}
        action = lambda: mf.audit_mf_run(run, completed=True, observed=reason != 'zero_observations')
    with pytest.raises(mf.VerificationError, match=reason):
        action()


def test_untyped_pointer_diffs_fail():
    run, watch, fields, _ = options()
    with pytest.raises(mf.VerificationError, match='non_pointer_memory_diff'):
        run.run_pair(DIALOG, watch=watch)  # no declared PointerFieldSpecs


def test_pointer_callbacks_must_execute():
    b = mf.VerificationBoundary((mf.FunctionRange('f_', (1, 2), (100, 101)),))
    spec = mf.PointerFieldSpec(0x1000, 0, frozenset({'f_'}), 'f_')
    with pytest.raises(mf.VerificationError, match='callback_behavior_unobserved'):
        mf.compare_memory(b, [(0x1000, struct.pack('<I', 1))],
                          [(0x1000, struct.pack('<I', 100))], [spec])


def test_inlined_fixture_proof():
    mod = mf.compile_fixture(FIXTURES / 'inlined_tu.c')
    si, off = mod.publics[FRAME]
    seg = mod.segments[si - 1]
    assert LOADER in mod.statics  # retained helper, unreachable from caller
    caller = mf.instructions(seg.data[off:], off)
    assert [(i.mnemonic, i.op_str) for i in caller] == [
        ('mov', 'eax, 7'), ('add', 'eax, 3'), ('ret', '')]
    assert not any(i.mnemonic == 'call' for i in caller)


def test_fresh_source_provenance():
    # Fresh compilation is independent of cemu's process-wide source cache.
    # Keep even temporary source inside the experiment's permitted paths.
    with tempfile.TemporaryDirectory(prefix='.source-', dir=mf.HERE) as tmp:
        src = Path(tmp) / 'options_tu.c'
        src.write_text((FIXTURES / 'options_tu.c').read_text())
        e = Emu()
        cm = mf.MultiModule(e, src, {DIALOG, REFRESH, TIMER}, mf.DependencySubstitutionPolicy())
        run = mf.MultiRun(e, cm, mf.make_boundary(cm, cm.verified_names), 'group')
        src.write_text(src.read_text() + '\n/* changed source */\n')
        with pytest.raises(mf.VerificationError, match='source_changed'):
            mf.audit_mf_run(run)
