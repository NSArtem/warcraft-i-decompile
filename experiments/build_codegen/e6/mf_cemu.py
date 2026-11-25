"""E6 only: explicit multi-function T4 contracts. No production monkeypatches.

Trust boundary matches docs/ANALYST_GUIDE.md: trusted Python scenario setup,
not a sandbox against hostile Python/Unicorn hooks. Code images, source and
OMF provenance are checked independently of the differential observations.
"""
from dataclasses import dataclass, field
from enum import Enum
import hashlib
import inspect
from pathlib import Path
import struct
import subprocess
import tempfile

from capstone import Cs, CS_ARCH_X86, CS_MODE_32, CS_GRP_JUMP, CS_GRP_CALL, CS_GRP_RET
from capstone.x86_const import X86_OP_IMM
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import UC_X86_REG_EIP, UC_X86_REG_EFLAGS
from wc1 import cemu, match, omf, symbols
from wc1.emu import Emu, REGS, SENTINEL, STACK_TOP, _memcpy

HERE = Path(__file__).resolve().parent
FLAGS = '-s -ot -ol -4r -zp2'


class VerificationError(cemu.CEmuError):
    pass


class IsolationImpossibleError(VerificationError):
    def __init__(self, reason):
        super().__init__(f'{reason}; use Group or Integrated mode')


class VerificationMode(str, Enum):
    ISOLATED = 'isolated'
    GROUP = 'group'
    INTEGRATED = 'integrated'


@dataclass(frozen=True)
class FunctionRange:
    symbol: str
    orig: tuple[int, int]
    c: tuple[int, int]


@dataclass(frozen=True)
class VerificationBoundary:
    functions: tuple[FunctionRange, ...]

    @property
    def names(self):
        return frozenset(f.symbol for f in self.functions)

    def contains(self, addr):
        return any(lo <= addr < hi for f in self.functions for lo, hi in (f.orig, f.c))

    def logical(self, addr, side):
        return next((f.symbol for f in self.functions
                     if getattr(f, side)[0] == addr), None)


@dataclass(frozen=True)
class Dependency:
    orig_addr: int
    stub_handler: object
    stack_pop: int
    expected_symbol: str
    mechanism: str = 'orig_addr_stub'


@dataclass(frozen=True)
class DependencySubstitutionPolicy:
    dependencies: dict[str, Dependency] = field(default_factory=dict)
    trusted_runtime: frozenset[int] = frozenset({0x31789})


@dataclass(frozen=True)
class PointerFieldSpec:
    watch_addr: int
    offset: int
    expected_logical_domain: frozenset[str]
    # A slot can require one particular callback, not merely any function.
    expected_symbol: str | None = None
    require_callback: bool = True


@dataclass(frozen=True)
class Callback:
    address: int
    args: tuple[int, ...] = ()


def compile_fixture(src):
    """Always compile source; all temporary outputs stay in E6 and are removed."""
    src = Path(src).resolve()
    with tempfile.TemporaryDirectory(prefix='.compile-', dir=HERE) as tmp:
        if src.suffix == '.asm':
            out = str(Path(tmp) / 'fixture.obj')
            subprocess.run(['nasm', '-f', 'obj', str(src), '-o', out], check=True,
                           capture_output=True)
            return omf.parse_object(out)
        return match.compile_c(str(src), FLAGS, str(Path(tmp) / 'fixture.obj'),
                               cc='10.0a', quiet=True)


def instructions(data, base):
    md = Cs(CS_ARCH_X86, CS_MODE_32)
    md.detail = True
    return list(md.disasm(bytes(data), base))


def function_spans(mod, bases, *, with_reachability=False):
    """Extent of reachable instructions, excluding inter-function alignment.

    Calls are not traversed. Cross-function branches are left to the isolation
    checker. Unknown/indirect control flow is rejected when proving isolation.
    """
    names = {**mod.publics, **mod.statics}
    result, reachable = {}, {}
    for name, (si, off) in names.items():
        seg = mod.segments[si - 1]
        if seg.cls != 'CODE':
            continue
        end = min([o for _, (s, o) in names.items() if s == si and o > off]
                  or [seg.length])
        decoded = {i.address: i for i in instructions(seg.data[off:end], off)}
        todo, seen = [off], set()
        while todo:
            a = todo.pop()
            if a in seen or not off <= a < end:
                continue
            ins = decoded.get(a)
            if ins is None:
                raise IsolationImpossibleError(f'undecodable function {name} at {a:#x}')
            seen.add(a)
            if ins.group(CS_GRP_RET):
                continue
            if ins.group(CS_GRP_JUMP):
                if ins.operands[0].type == X86_OP_IMM:
                    todo.append(ins.operands[0].imm)
                if ins.mnemonic == 'jmp':
                    continue
            todo.append(a + ins.size)
        if not seen:
            raise IsolationImpossibleError(f'missing entry {name}')
        result[name] = (bases[si] + off,
                        bases[si] + max(a + decoded[a].size for a in seen))
        reachable[name] = frozenset(bases[si] + a for a in seen)
    return (result, reachable) if with_reachability else result


class MultiModule(cemu.CModule):
    """CModule placement with policy-aware EXTDEF/LEXTDEF resolution."""
    def __init__(self, emu, src, verified_names, policy):
        self.verified_names = frozenset(verified_names)
        self.policy = policy
        for name, dep in policy.dependencies.items():
            if name in self.verified_names:
                raise VerificationError('verified_c_redirected_to_orig: ' + name)
            if name != dep.expected_symbol or dep.mechanism not in {
                    'orig_addr_stub', 'symbol_aware_reloc', 'c_entry_hook'}:
                raise VerificationError('invalid dependency declaration: ' + name)
            entry = cemu._by_link().get(name)
            if entry is None or entry['addr'] != dep.orig_addr:
                raise VerificationError('dependency symbol/address mismatch: ' + name)
        mod = compile_fixture(src)
        self.compiled_digest = cemu.omf_module_digest(mod)
        super().__init__(emu, str(src), mod=mod)
        self.function_ranges, self.reachable = function_spans(mod, self.base,
                                                              with_reachability=True)

    def _resolved_target(self, fu):
        dep = self.policy.dependencies.get(fu.target) if fu.target_kind == 'ext' else None
        if dep and dep.mechanism == 'symbol_aware_reloc':
            if fu.target in self.verified_names:
                raise VerificationError('verified_c_redirected_to_orig')
            return dep.orig_addr
        return cemu.CModule._target(self, fu)

    def relocation(self, seg, base, fu):
        if fu.loc != 9:
            raise VerificationError(f'unsupported OMF location {omf.LOC_NAMES.get(fu.loc)}')
        addend = struct.unpack_from('<i', seg.data, fu.offset)[0] + fu.disp
        value = self._resolved_target(fu) + addend
        if fu.self_rel:
            value -= base + fu.offset + 4
        return fu.offset, struct.pack('<I', value & 0xffffffff)

    def _reloc(self, seg, base, fu):
        off, data = self.relocation(seg, base, fu)
        Emu.write(self.emu, base + off, data)

    def expected_code_images(self):
        result = []
        for si, seg in enumerate(self.mod.segments, 1):
            if seg.cls != 'CODE' or not seg.length:
                continue
            base = self.base[si]
            data = bytearray(seg.data)
            for fu in seg.fixups:
                off, value = self.relocation(seg, base, fu)
                data[off:off + len(value)] = value
            result.append((base, bytes(data)))
        return result


def make_boundary(cm, names):
    funcs, _, _ = symbols.load()
    by_name = {f['link_name']: a for a, f in funcs.items()}
    if not hasattr(cm.emu.p, 'functions'):
        cm.emu.p.discover().partition()
    ranges = {f['start']: f['end'] for f in cm.emu.p.functions}
    result = []
    for name in sorted(names):
        a = by_name[name]
        result.append(FunctionRange(name, (a, ranges[a]), cm.function_ranges[name]))
    return VerificationBoundary(tuple(result))


def check_isolation(cm, boundary):
    """Conservative static entry-only proof on *relocated* compiled CODE.

    Direct calls and declared function-address fixups establish reachability.
    Indirect jumps, cross-range interior entries, fallthrough and absent
    sibling references cannot prove isolation and are rejected.
    """
    subs = {n: cm.function_ranges.get(n) for n in cm.policy.dependencies
            if n in cm.local_names}
    for name, dep in cm.policy.dependencies.items():
        if dep.mechanism == 'c_entry_hook' and name not in subs:
            raise IsolationImpossibleError(f'inlined/eliminated sibling {name}: no entry')
    all_ranges = cm.function_ranges
    def owner(a):
        return next((n for n, (lo, hi) in all_ranges.items() if lo <= a < hi), None)
    references, direct_entries = set(), set()
    reachable_bytes = {}
    for base, data in cm.expected_code_images():
        for ins in instructions(data, base):
            source = owner(ins.address)
            if not source or ins.address not in cm.reachable[source]:
                continue
            reachable_bytes.setdefault(source, set()).update(
                range(ins.address, ins.address + ins.size))
            if ins.group(CS_GRP_JUMP) or ins.group(CS_GRP_CALL):
                if ins.operands[0].type != X86_OP_IMM:
                    if ins.group(CS_GRP_JUMP) and subs:
                        raise IsolationImpossibleError('unresolved indirect jump')
                    continue  # indirect callbacks are checked dynamically
                target = ins.operands[0].imm
                dest = owner(target)
                if source != dest and (source in subs or dest in subs):
                    if dest and target != all_ranges[dest][0]:
                        raise IsolationImpossibleError('interior_entry_bypass')
                    if dest in subs and source in boundary.names:
                        references.add(dest)
                        direct_entries.add(dest)
            if not ins.group(CS_GRP_RET) and ins.mnemonic != 'jmp':
                dest = owner(ins.address + ins.size)
                if dest != source and (source in subs or dest in subs) and dest:
                    raise IsolationImpossibleError('cross-function fallthrough')
    for si, seg in enumerate(cm.mod.segments, 1):
        for fu in seg.fixups:
            source = owner(cm.base[si] + fu.offset) if si in cm.base else None
            reachable_field = source and cm.base[si] + fu.offset in reachable_bytes.get(source, ())
            if (reachable_field and source in boundary.names and fu.target_kind == 'ext'
                    and fu.target in subs):
                references.add(fu.target)
    for name in subs:
        dep = cm.policy.dependencies[name]
        if name not in references or (dep.mechanism == 'c_entry_hook' and name not in direct_entries):
            raise IsolationImpossibleError(f'inlined/eliminated callee {name}: no entry reference')


def compare_memory(boundary, orig, compiled, specs=(), callbacks=None):
    """Compare every byte, allowing only exact typed entry-pointer bijections."""
    o, c = dict(orig), dict(compiled)
    if o.keys() != c.keys() or any(len(o[a]) != len(c[a]) for a in o):
        raise VerificationError('watch shape mismatch')
    mutable = {a: bytearray(data) for a, data in c.items()}
    slots, used = [], set()
    for spec in specs:
        a, off = spec.watch_addr, spec.offset
        if a not in o or off < 0 or off + 4 > len(o[a]):
            raise VerificationError('untyped_pointer: slot outside watch')
        addresses = set(range(a + off, a + off + 4))
        if used & addresses:
            raise VerificationError('overlapping_pointer_specs')
        used |= addresses
        op = struct.unpack_from('<I', o[a], off)[0]
        cp = struct.unpack_from('<I', c[a], off)[0]
        on, cn = boundary.logical(op, 'orig'), boundary.logical(cp, 'c')
        if on is None or on != cn or on not in spec.expected_logical_domain:
            raise VerificationError('incorrect_pointer_normalization: logical target mismatch')
        if spec.expected_symbol is not None and on != spec.expected_symbol:
            raise VerificationError('incorrect_pointer_normalization: wrong callback')
        if spec.require_callback and (callbacks is None or
                on not in callbacks['orig'] or on not in callbacks['c']):
            raise VerificationError('callback_behavior_unobserved: ' + on)
        slots.append((op, cp))
        mutable[a][off:off + 4] = o[a][off:off + 4]
    for op, cp in slots:
        for oq, cq in slots:
            if (op == oq) != (cp == cq):
                raise VerificationError('incorrect_pointer_normalization: broken aliasing')
    for a in o:
        if o[a] != mutable[a]:
            raise VerificationError(f'non_pointer_memory_diff: {a:#x}')
    return len(slots)


class MultiRun:
    def __init__(self, emu, cm, boundary, mode):
        if type(emu) is not Emu or type(cm) is not MultiModule or cm.emu is not emu:
            raise VerificationError('untrusted emulator/module')
        self.emu, self.cm, self.boundary = emu, cm, boundary
        self.mode = VerificationMode(mode)
        if cm.verified_names != boundary.names or not boundary.functions:
            raise VerificationError('boundary mismatch')
        if self.mode == VerificationMode.ISOLATED and len(boundary.functions) != 1:
            raise VerificationError('isolated boundary must contain one function')
        expected = make_boundary(cm, boundary.names)
        if expected != boundary:
            raise VerificationError('boundary range mismatch')
        ranges = [r for f in boundary.functions for r in (f.orig, f.c)]
        if any(a < d and c < b for i, (a, b) in enumerate(ranges)
               for c, d in ranges[i + 1:]):
            raise VerificationError('non_bijective_boundary')
        check_isolation(cm, boundary)
        self.side = 'orig'
        self.logs = {'orig': [], 'c': []}
        self.visits = {'orig': {}, 'c': {}}
        self.callback_visits = {'orig': set(), 'c': set()}
        self.callback_events = {'orig': [], 'c': []}
        self.real_callees = {'orig': {}, 'c': {}}
        funcs, _, _ = symbols.load()
        self.orig_symbols = {a: f['link_name'] for a, f in funcs.items()}
        self.pending = None
        self.counts = {'orig': 0, 'c': 0}
        if set(emu.stubs) != {0x31789} or emu.stubs[0x31789] is not _memcpy:
            if any(boundary.contains(a) for a in emu.stubs):
                raise VerificationError('boundary_stubbed')
            raise VerificationError('undeclared_stub: preinstalled substitution')
        self.expected_stubs = dict(emu.stubs)
        self.entry_hooks = {}
        for name, dep in cm.policy.dependencies.items():
            if boundary.contains(dep.orig_addr):
                raise VerificationError('boundary_stubbed')
            wrapper = self._wrapper(name, dep)
            emu.stubs[dep.orig_addr] = wrapper
            emu.stub_pops[dep.orig_addr] = dep.stack_pop
            self.expected_stubs[dep.orig_addr] = wrapper
            if name in cm.local_names:
                if dep.mechanism == 'orig_addr_stub':
                    raise VerificationError('asymmetric_substitution: local sibling needs mechanism')
                self.entry_hooks[cm.local_names[name]] = (name, dep, wrapper)
        self.expected_entry_hooks = dict(self.entry_hooks)
        self.hook = emu.uc.hook_add(UC_HOOK_CODE, self._hook)
        self.initial_digest = cemu.omf_module_digest(cm.mod)
        self.initial_code = tuple(cm.expected_code_images())
        self.initial_policy = dict(cm.policy.dependencies)
        self.orig_ends = {f['start']: f['end'] for f in emu.p.functions}

    def _wrapper(self, name, dep):
        def wrapped(e):
            self.logs[self.side].append(name)
            result = dep.stub_handler(e)
            if inspect.isgenerator(result):
                try:
                    request = next(result)
                except StopIteration as done:
                    return done.value
                self.pending = (result, request)
                e.uc.emu_stop()
                return 0
            return result
        return wrapped

    def _hook(self, uc, addr, size, _):
        self.counts[self.side] += 1
        if self.counts[self.side] > self.emu.max_insns:
            raise VerificationError('instruction_limit')
        if self.emu.trace is not None:
            raise VerificationError('trace_active')
        symbol = self.orig_symbols.get(addr)
        if (symbol is not None and symbol not in self.boundary.names
                and symbol not in self.cm.policy.dependencies
                and addr not in self.cm.policy.trusted_runtime):
            calls = self.real_callees[self.side]
            calls[symbol] = calls.get(symbol, 0) + 1
        for f in self.boundary.functions:
            if self.side == 'c' and f.orig[0] <= addr < f.orig[1]:
                raise VerificationError('verified_c_redirected_to_orig')
            if getattr(f, self.side)[0] <= addr < getattr(f, self.side)[1]:
                visits = self.visits[self.side]
                visits[f.symbol] = visits.get(f.symbol, 0) + 1
        for name, dep in self.cm.policy.dependencies.items():
            cr = self.cm.function_ranges.get(name)
            # Executing any interior byte after an entry substitution is bypass.
            if cr and cr[0] < addr < cr[1]:
                raise IsolationImpossibleError('dynamic interior_entry_bypass: ' + name)
            if dep.orig_addr < addr < self.orig_ends[dep.orig_addr]:
                raise IsolationImpossibleError('dynamic original interior_entry_bypass: ' + name)
        entry = self.entry_hooks.get(addr)
        if entry:
            _, dep, handler = entry
            result = handler(self.emu)
            if result is not None:
                self.emu.reg('eax', result)
            sp = self.emu.reg('esp')
            ret = self.emu.u32(sp)
            self.emu.reg('esp', sp + 4 + dep.stack_pop)
            uc.reg_write(UC_X86_REG_EIP, ret)

    def _execute(self, addr, args=(), sp=STACK_TOP - 0x100):
        for r, value in zip(('eax', 'edx', 'ebx', 'ecx'), args):
            self.emu.reg(r, value)
        sp -= 4
        self.emu.put_u32(sp, SENTINEL)
        self.emu.reg('esp', sp)
        self.emu._error = None
        while True:
            self.emu.uc.emu_start(addr, SENTINEL)
            if self.emu._error:
                raise self.emu._error
            if self.pending is None:
                break
            (generator, callback), self.pending = self.pending, None
            context = self.emu.uc.context_save()
            while True:
                if not isinstance(callback, Callback):
                    raise VerificationError('invalid callback request')
                logical = self.boundary.logical(callback.address, self.side)
                if logical is not None:
                    self.callback_visits[self.side].add(logical)
                value = self._execute(callback.address, callback.args,
                                      self.emu.reg('esp') - 0x4000)
                self.callback_events[self.side].append((logical, value))
                self.emu.uc.context_restore(context)
                try:
                    callback = generator.send(value)
                except StopIteration as done:
                    self.emu.reg('eax', done.value or 0)
                    break
            addr = self.emu.uc.reg_read(UC_X86_REG_EIP)
            if addr == SENTINEL:
                break
        return self.emu.reg('eax')

    def run_pair(self, name, *args, watch=(), out_regs=(), pointer_fields=()):
        if name not in self.boundary.names:
            raise VerificationError('entry outside boundary')
        if pointer_fields and self.mode == VerificationMode.ISOLATED:
            raise VerificationError('pointer correspondence forbidden in Isolated')
        audit_mf_run(self)
        self.side = 'orig'
        self.logs = {'orig': [], 'c': []}
        self.visits = {'orig': {}, 'c': {}}
        self.callback_visits = {'orig': set(), 'c': set()}
        self.callback_events = {'orig': [], 'c': []}
        self.real_callees = {'orig': {}, 'c': {}}
        self.counts = {'orig': 0, 'c': 0}
        saved = [(a, self.emu.read(a, n)) for a, n in watch]
        if any(n <= 0 for _, n in watch) or any(
                a < b + m and b < a + n for i, (a, n) in enumerate(watch)
                for b, m in watch[i + 1:]):
            raise VerificationError('invalid watch ranges')
        f = next(f for f in self.boundary.functions if f.symbol == name)
        observed = {}
        for side in ('orig', 'c'):
            self.side = side
            for a, data in saved:
                self.emu.write(a, data)
            for reg in REGS:
                self.emu.reg(reg, 0)
            self.emu.uc.reg_write(UC_X86_REG_EFLAGS, 0x202)
            self.emu._count = 0
            self._execute(getattr(f, side)[0], args)
            audit_mf_run(self)
            observed[side] = ([(a, self.emu.read(a, n)) for a, n in watch],
                              {r: self.emu.reg(r) for r in out_regs})
        audit_mf_run(self, completed=True, observed=bool(watch or out_regs))
        if observed['orig'][1] != observed['c'][1]:
            raise VerificationError('register_diff')
        if self.logs['orig'] != self.logs['c']:
            raise VerificationError('stub_log_diff')
        normalized = compare_memory(self.boundary, observed['orig'][0], observed['c'][0],
                                    pointer_fields, self.callback_visits)
        if self.callback_visits['orig'] != self.callback_visits['c']:
            raise VerificationError('callback_identity_diff')
        if self.callback_events['orig'] != self.callback_events['c']:
            raise VerificationError('callback_behavior_diff')
        if self.real_callees['orig'] != self.real_callees['c']:
            raise VerificationError('real_callee_path_diff')
        for sym in self.boundary.names:
            if not self.visits['orig'].get(sym) or not self.visits['c'].get(sym):
                raise VerificationError('boundary_function_unexecuted: ' + sym)
        return dict(mode=self.mode.value, entry=name, diffs=[], pointer_slots=normalized,
                    instructions=dict(self.counts), visits=self.visits,
                    callbacks={s: sorted(v) for s, v in self.callback_visits.items()},
                    callback_events=self.callback_events,
                    real_callees=self.real_callees,
                    stub_logs=self.logs,
                    boundary=[dict(symbol=f.symbol, orig=list(f.orig), c=list(f.c))
                              for f in self.boundary.functions])


def audit_mf_run(run, *, completed=False, observed=True):
    e, cm, boundary = run.emu, run.cm, run.boundary
    if e.trace is not None:
        raise VerificationError('trace_active')
    for obj, cls in ((e, Emu), (cm, MultiModule)):
        if any(any(k in vars(base) and callable(vars(base)[k]) for base in cls.__mro__)
               for k in vars(obj)):
            raise VerificationError('method_overridden')
    for f in boundary.functions:
        if cm.fn(f.symbol) != f.c[0] or cemu._addr_in_orig_image(e, cm.fn(f.symbol)):
            raise VerificationError('verified_c_redirected_to_orig')
    if any(boundary.contains(a) for a in e.stubs):
        raise VerificationError('boundary_stubbed')
    if set(e.stubs) - set(run.expected_stubs):
        raise VerificationError('undeclared_stub')
    if run.entry_hooks != run.expected_entry_hooks:
        raise VerificationError('asymmetric_substitution')
    if cm.policy.dependencies != run.initial_policy:
        raise VerificationError('substitution_policy_changed')
    for addr, fn in run.expected_stubs.items():
        if e.stubs.get(addr) is not fn:
            raise VerificationError('asymmetric_substitution')
    for dep in cm.policy.dependencies.values():
        if e.stub_pops.get(dep.orig_addr, 0) != dep.stack_pop:
            raise VerificationError('asymmetric_substitution: stack cleanup')
    if cm.policy.trusted_runtime != frozenset({0x31789}) or e.stubs.get(0x31789) is not _memcpy:
        raise VerificationError('undeclared_stub: untrusted runtime model')
    for name, dep in cm.policy.dependencies.items():
        if name in boundary.names:
            raise VerificationError('verified_c_redirected_to_orig')
        if name in cm.local_names and cm.local_names[name] not in run.entry_hooks:
            raise VerificationError('asymmetric_substitution')
    # Entire original CODE object, not merely the top-level function. No int3 exception.
    for obj in e.p.le.objects:
        if obj.base == 0x10000:
            expected = bytes(e.p.image[obj.index])
            if e.read(obj.base, len(expected)) != expected:
                raise VerificationError('orig_patched')
    if cemu.omf_module_digest(cm.mod) != run.initial_digest:
        raise VerificationError('c_patched: OMF changed')
    if tuple(cm.expected_code_images()) != run.initial_code or any(
            e.read(base, len(data)) != data for base, data in run.initial_code):
        raise VerificationError('c_patched')
    if hashlib.sha256(Path(cm.src).read_bytes()).hexdigest() != cm._src_sha256:
        raise VerificationError('source_changed')
    if completed:
        if not observed:
            raise VerificationError('zero_observations')
        if any(v <= 0 for v in run.counts.values()):
            raise VerificationError('zero_instructions')
        if cemu.omf_module_digest(compile_fixture(cm.src)) != cm.compiled_digest:
            raise VerificationError('fresh_OMF_mismatch')
