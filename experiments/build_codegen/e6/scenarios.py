"""Real E6 scenarios; source bodies stay unchanged in the consolidated TUs."""
from pathlib import Path
import json
import os
import struct
import tempfile

from wc1 import cemu, t4spec, symbols
from wc1.emu import Emu
from .mf_cemu import (HERE, Callback, Dependency, DependencySubstitutionPolicy,
                      MultiModule, MultiRun, PointerFieldSpec, VerificationMode,
                      make_boundary, compile_fixture, instructions)

FIXTURES = HERE / 'fixtures'
PREFS = 0x532b4
REFRESH, TIMER, DIALOG = 'OptionsRefresh_', 'OptionsApplyTimer_', 'OptionsDialog_'
LOADER, FRAME = 'IntroLoadCreditLines_', 'IntroFrame_'


def addr(name):
    return cemu._by_link()[name]['addr']


def dep(name, handler, *, pop=0, mechanism='orig_addr_stub'):
    return Dependency(addr(name), handler, pop, name, mechanism)


def options(mode='group', *, result=0, net=1, absent=0, race=1,
            legacy=False, mutation=None, clock_step=30):
    mode = VerificationMode(mode)
    emu = Emu(max_insns=200000)
    capture = emu.alloc(0x60)
    log = emu.alloc(0x100)
    # All mutable model state is in watched emulator memory, restored per side.
    def record(e, kind, values):
        n = e.u32(log)
        data = struct.pack('<' + 'I' * (len(values) + 1), kind, *values)
        assert n + len(data) <= 0xfc
        e.write(log + 4 + n, data)
        e.put_u32(log, n + len(data))

    def clock(e):
        n = e.u32(log + 0xfc) + 1
        e.put_u32(log + 0xfc, n)
        return 1000 + (n - 1) * clock_step

    def modal(e):
        record(e, 1, [e.reg('eax'), e.reg('edx')])
        return 0

    def sound(e):
        # Compare actual preferences passed to downstream sound code.
        record(e, 2, list(struct.unpack('<5I', e.read(e.reg('eax'), 20))))
        return 0

    def dialog(e):
        p = e.u32(e.reg('esp') + 4)
        record(e, 3, [e.reg(r) for r in ('eax', 'edx', 'ebx', 'ecx')])
        # Record the complete OptionsParams before AND after callback execution.
        e.write(capture, e.read(p, 32))
        yield Callback(e.u32(p + 20), (p,))
        timer_ret = yield Callback(e.u32(p + 24), (p,))
        record(e, 4, [timer_ret])
        e.write(capture + 32, e.read(p, 32))
        if mutation == 'alias' and run.side == 'c':
            e.put_u32(capture + 32 + 20, e.u32(p + 24))
        if mutation == 'non_pointer' and run.side == 'c':
            e.write(capture + 1, b'\x99')
        return result

    def isolated_callback(e):
        record(e, 5, [e.u32(e.reg('eax') + 28)])
        return 0

    dependencies = {
        'ModalScreen_': dep('ModalScreen_', modal),
        'clock_': dep('clock_', clock),
        'DialogRun_': dep('DialogRun_', dialog, pop=4),
    }
    names = {DIALOG, REFRESH, TIMER}
    if mode == VerificationMode.ISOLATED:
        names = {DIALOG}
        for name in (REFRESH, TIMER):
            dependencies[name] = dep(name, isolated_callback, mechanism='symbol_aware_reloc')
    if mode != VerificationMode.INTEGRATED:
        dependencies['SndApplyOptions_'] = dep('SndApplyOptions_', sound)
    else:
        # Real original SndApplyOptions executes on BOTH sides, outside the
        # verification boundary. Only its audio boundary dependencies are modeled.
        for name in ('SndSetSfxVolume_', 'SndSetMusicVolume_'):
            def volume(e, name=name):
                record(e, addr(name), [e.reg('eax') & 0xffff])
                return 0
            dependencies[name] = dep(name, volume)
    policy = DependencySubstitutionPolicy(dependencies)
    src = FIXTURES / ('options_swapped_tu.c' if mutation == 'swap' else 'options_tu.c')
    if legacy:
        cm = cemu.CModule(emu, str(src), mod=compile_fixture(src))
        return emu, cm, capture, log
    cm = MultiModule(emu, src, names, policy)
    run = MultiRun(emu, cm, make_boundary(cm, names), mode)
    emu.write(PREFS, struct.pack('<5I', 4, 48, 64, 2, 3))
    emu.write(0x50088, struct.pack('<H', race))
    emu.write(0x5a11a, struct.pack('<H', net))
    emu.write(0x59912, struct.pack('<H', 0xffff if absent & 1 else 0))
    emu.write(0x59902, struct.pack('<H', 0xffff if absent & 2 else 0))
    watch = [(PREFS, 20), (capture, 64), (log, 0x100)]
    fields = []
    if mode != VerificationMode.ISOLATED:
        for off in (0, 32):
            for slot, name in ((20, REFRESH), (24, TIMER)):
                fields.append(PointerFieldSpec(capture, off + slot, frozenset({name}), name))
    return run, watch, fields, capture


def run_options(mode='group', **kw):
    run, watch, fields, capture = options(mode, **kw)
    result = run.run_pair(DIALOG, watch=watch, pointer_fields=fields)
    result['callback_pointer_values_c'] = [run.emu.u32(capture + i) for i in (20, 24)]
    result['params_before_c'] = list(struct.unpack('<8I', run.emu.read(capture, 32)))
    result['params_after_c'] = list(struct.unpack('<8I', run.emu.read(capture + 32, 32)))
    result['prefs_final_c'] = list(struct.unpack('<5I', run.emu.read(PREFS, 20)))
    return result


def playflic(mode='group', *, timer=1, credits=1, empty=False, terminal=False,
             fixture='playflic_pair_tu.c'):
    mode = VerificationMode(mode)
    emu = Emu(max_insns=200000)
    scratch = emu.alloc(0x10000)
    log = emu.alloc(0x40)
    def record(e, kind, vals=()):
        n = e.u32(log)
        data = struct.pack('<' + 'I' * (1 + len(vals)), kind, *vals)
        assert n + len(data) < 0x3c
        e.write(log + 4 + n, data)
        e.put_u32(log, n + len(data))
    def load(e):
        record(e, 1)
        e.write(0x59ee2, struct.pack('<H', 7))
        return 0
    def width(e):
        record(e, 2, (e.reg('eax'), e.reg('edx')))
        return 100
    dependencies = {}
    names = {FRAME, LOADER}
    if mode == VerificationMode.ISOLATED:
        names = {FRAME}
        dependencies[LOADER] = dep(LOADER, load, mechanism='c_entry_hook')
    elif mode == VerificationMode.GROUP:
        dependencies['TextWidth_'] = dep('TextWidth_', width)
    cm = MultiModule(emu, FIXTURES / fixture, names,
                     DependencySubstitutionPolicy(dependencies))
    run = MultiRun(emu, cm, make_boundary(cm, names), mode)
    emu.write(0x59efc, b'\0\0')
    emu.write(0x59ef8, b'\xff\xff')
    emu.write(0x59ee4, struct.pack('<H', credits))
    emu.write(0x59ee2, struct.pack('<H', timer))
    emu.write(0x59ee8, struct.pack('<H', 0))
    emu.write(0x59ef2, struct.pack('<H', 1))
    emu.write(scratch, b'Credits\0')
    emu.write(scratch + 0x20, b'\0')
    target = scratch + 0x20 if empty else scratch
    delay = 0xffff if terminal else 3
    emu.write(0x52d18, b''.join(struct.pack('<HI', delay, target) for _ in range(5)))
    emu.put_u32(0x59ec4, scratch + 0x100)
    emu.write(0x5944a, struct.pack('<H', 100))
    emu.put_u32(0x5acf0, scratch + 0x50)
    # A small valid synthetic font for Integrated's real original TextWidth.
    # Font.first=0, Font.glyphs=font+8; each 3-byte glyph has width at +2.
    emu.write(scratch + 0x60, b'\0' * 8)
    emu.put_u32(scratch + 0x64, scratch + 0x10000 - 0x300)
    emu.write(scratch + 0x10000 - 0x300, b'\0\0\x08' * 256)
    emu.put_u32(0x5acf0, scratch + 0x60)
    watch = [(0x59eb8, 0x48), (log, 0x40), (scratch, 0x10000)]
    return run, watch


def run_playflic(mode='group', **kw):
    run, watch = playflic(mode, **kw)
    return run.run_pair(FRAME, watch=watch)


def inspect_playflic():
    mod = compile_fixture(FIXTURES / 'playflic_pair_tu.c')
    si, start = mod.publics[FRAME]
    seg = mod.segments[si - 1]
    e = Emu()
    cm = cemu.CModule(e, str(FIXTURES / 'playflic_pair_tu.c'), mod=mod)
    base = cm.base[si]
    target = cm.fn(LOADER)
    calls = []
    for ins in instructions(e.read(base + start, seg.length - start), base + start):
        if ins.mnemonic == 'call' and ins.op_str == hex(target):
            fixups = [f.offset for f in seg.fixups
                      if ins.address - base <= f.offset < ins.address - base + ins.size]
            calls.append(dict(offset=ins.address - base, size=ins.size,
                              target_offset=target - base, omf_fixups=fixups,
                              fixup_targets=[f.target for f in seg.fixups if f.offset in fixups]))
    return dict(publics={n: list(v) for n, v in sorted(mod.publics.items())},
                direct_loader_calls=calls,
                loader_call_omf_fixups=sum(len(c['omf_fixups']) for c in calls))


def baseline_options():
    emu, cm, capture, log = options(legacy=True)
    def dialog(e):
        p = e.u32(e.reg('esp') + 4)
        e.write(capture, e.read(p, 32))
        return 1
    emu.stubs[addr('DialogRun_')] = dialog
    emu.stub_pops[addr('DialogRun_')] = 4
    for name in ('ModalScreen_', 'SndApplyOptions_', 'clock_'):
        emu.stubs[addr(name)] = lambda e: 0
    diffs = cemu.run_pair(emu, addr(DIALOG), cm, DIALOG,
                          watch=[(capture, 32), (PREFS, 20)], out_regs=())
    assert diffs, 'legacy pointer bug did not reproduce'
    pointers = [emu.u32(capture + i) for i in (20, 24)]
    assert pointers == [cm.fn(REFRESH), cm.fn(TIMER)]
    # Capture the real legacy c_stubbed audit field (its normal audit rejects
    # this even though a dependency outside the intended boundary is stubbed).
    with tempfile.TemporaryDirectory(prefix='.baseline-', dir=HERE) as tmp:
        audit = Path(tmp) / 'audit.jsonl'
        old = os.environ.get('WC1_T4_AUDIT_LOG')
        try:
            os.environ['WC1_T4_AUDIT_LOG'] = str(audit)
            emu.stubs[cm.fn(REFRESH)] = lambda e: 0
            cemu.run_pair(emu, addr(DIALOG), cm, DIALOG,
                          watch=[(PREFS, 20)], out_regs=())
        finally:
            if old is None:
                os.environ.pop('WC1_T4_AUDIT_LOG', None)
            else:
                os.environ['WC1_T4_AUDIT_LOG'] = old
        records = [json.loads(s) for s in audit.read_text().splitlines()]
        assert records[-1]['c_stubbed']
        ok, reason = t4spec.audit_t4_log(str(audit))
        assert not ok and 'compiled C segment range was stubbed' in reason
    return dict(diffs=diffs, original_callback_pointers=[addr(REFRESH), addr(TIMER)],
                compiled_callback_pointers=pointers, c_stubbed=True,
                legacy_audit_rejected=True, audit_reason=reason)


def baseline_playflic():
    e = Emu(max_insns=200000)
    src = FIXTURES / 'playflic_pair_tu.c'
    cm = cemu.CModule(e, str(src), mod=compile_fixture(src))
    log = e.alloc(4)
    def load(e):
        e.put_u32(log, e.u32(log) + 1)
        return 0
    e.stubs[addr(LOADER)] = load
    e.write(0x59ee4, b'\1\0')
    e.write(0x59ee2, b'\5\0')
    diffs = cemu.run_pair(e, addr(FRAME), cm, FRAME,
                          watch=[(0x59eb8, 0x48), (log, 4)], out_regs=())
    assert diffs and e.u32(log) == 0
    return dict(diffs=diffs, original_stub_calls=1, compiled_stub_calls=e.u32(log),
                compiled_loader_bypassed_original_stub=True)


NEGATIVES = {
    'N1': 'boundary_stubbed',
    'N2': 'undeclared_stub',
    'N3_orig': 'asymmetric_substitution',
    'N3_c': 'asymmetric_substitution',
    'N4a': 'incorrect_pointer_normalization',
    'N4b': 'incorrect_pointer_normalization: broken aliasing',
    'N4c': 'non_pointer_memory_diff',
    'N5': 'verified_c_redirected_to_orig',
    'N6': 'interior_entry_bypass',
    'N7': 'inlined/eliminated',
}


def exercise_negative(control):
    """Perform an actual prohibited action; callers must assert rejection."""
    if control == 'N5':
        e = Emu()
        policy = DependencySubstitutionPolicy({
            REFRESH: dep(REFRESH, lambda e: 0, mechanism='symbol_aware_reloc')})
        MultiModule(e, FIXTURES / 'options_tu.c', {DIALOG, REFRESH, TIMER}, policy)
        return
    if control in ('N6', 'N7'):
        e = Emu()
        policy = DependencySubstitutionPolicy({
            LOADER: dep(LOADER, lambda e: 0, mechanism='c_entry_hook')})
        fixture = 'interior_entry.asm' if control == 'N6' else 'inlined_tu.c'
        cm = MultiModule(e, FIXTURES / fixture, {FRAME}, policy)
        MultiRun(e, cm, make_boundary(cm, {FRAME}), 'isolated')
        return
    if control.startswith('N4'):
        return run_options('group', mutation={'N4a': 'swap', 'N4b': 'alias',
                                               'N4c': 'non_pointer'}[control])
    if control in ('N3_orig', 'N3_c'):
        run, watch = playflic('isolated')
        if control == 'N3_c':
            del run.entry_hooks[run.cm.fn(LOADER)]
        else:
            del run.emu.stubs[addr(LOADER)]
        return run.run_pair(FRAME, watch=watch)
    run, watch, fields, _ = options('group')
    if control == 'N1':
        run.emu.stubs[run.cm.fn(REFRESH)] = lambda e: 0
    elif control == 'N2':
        run.emu.stubs[addr('TextWidth_')] = lambda e: 0
    else:
        raise ValueError(control)
    return run.run_pair(DIALOG, watch=watch, pointer_fields=fields)
