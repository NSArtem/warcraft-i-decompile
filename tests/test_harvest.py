import os
import struct

import pytest

from wc1 import path, t4spec
from wc1.t4spec import T4Case, T4Stub

pytestmark = pytest.mark.skipif(not (os.path.exists(path('original','install','war.exe')) and os.environ.get('WATCOM')), reason='needs original/ and $WATCOM')


RESOURCE_WATCH = ((0x50060, 20), (0x50074, 20), (0x50DC0, 20),
                  (0x50DD4, 20), (0x50E34, 8))
MAP_SLOT = 12 + 19 * 64


def test_harvest_t3():
    t4spec.assert_t3_matches(path('src/harvest'), ['harvest_queue_building_entry.c', 'order_update_harvest_return.c'])


def test_harvest_reference_near_misses():
    t4spec.assert_ref_mismatch(path('src/harvest'), ['harvest_deposit_cargo_reference.c', 'order_update_harvest_enter_building_reference.c', 'order_update_harvest_exit_building_reference.c', 'order_update_harvest_reference.c'])


def _run(file_stem, link, addr, rows, make_stubs, *, extra_watch=(),
         use_map=False, human_arg=False):
    watch = []
    active = {}
    cases = [T4Case(label=label) for label, _ in rows]

    def init_emu(emu):
        worker = emu.alloc(0x60, 16)
        building = emu.alloc(0x60, 16)
        hall = emu.alloc(0x60, 16)
        tile_map = emu.alloc(4096 * 4, 16) if use_map else None
        watch[:] = [(worker, 0x60), (building, 0x60), *extra_watch]
        if use_map:
            watch.append((tile_map + 4 * MAP_SLOT, 4))

        def setup_for(cfg):
            def setup(e):
                active.clear()
                active.update(cfg)
                owner = cfg.get('owner', 2)
                target = 0 if cfg.get('no_target') else building
                u = bytearray(0x60)
                b = bytearray(0x60)
                struct.pack_into('<I', u, 0, 0x11223344)
                struct.pack_into('<I', b, 0, 0xA1B2C3D4)
                struct.pack_into('<hh', u, 0x0A, 12, 19)
                struct.pack_into('<hh', b, 0x0A, 21, 27)
                struct.pack_into('<hhI', u, 0x3E, -31, 33, building)
                struct.pack_into('<hhI', u, 0x4E, -7, 23, target)
                struct.pack_into('<HH', b, 0x0E, cfg.get('building_flags', 0),
                                 cfg.get('state', 0))
                struct.pack_into('<I', b, 0x54, cfg.get('remaining', 0))
                u[0x08] = 3
                u[0x1E] = owner
                u[0x48] = cfg.get('ticks', 0)
                u[0x49] = cfg.get('flags', 0)
                b[0x1B] = cfg.get('type', 0x28)
                b[0x4E] = cfg.get('count', 0)
                e.write(worker, bytes(u))
                e.write(building, bytes(b))
                controllers = bytearray(5)
                controllers[owner] = cfg.get('controller', 0)
                e.write(0x5008C, bytes(controllers))
                halls = [0] * 5
                halls[owner] = hall if cfg.get('hall') else 0
                e.write(0x58DB0, struct.pack('<5I', *halls))
                e.write(0x50E66, struct.pack('<H', 0xA55A))
                e.write(0x50E68, struct.pack('<10h', 10, 20, 11, 21, -12, -22, 13, 23, 14, 24))
                if use_map:
                    e.write(0x58580, struct.pack('<I', tile_map))
                    e.write(tile_map + 4 * MAP_SLOT,
                            struct.pack('<I', worker if cfg.get('own_tile') else 0))
                    e.write(0x50F80, struct.pack('<8b', 0, 1, 1, -1, 0, -1, -1, 1))
                    e.write(0x50F88, struct.pack('<8b', -1, -1, 0, 1, 1, 1, 0, -1))
                for base, size in extra_watch:
                    if (base, size) in RESOURCE_WATCH:
                        if size == 20:
                            e.write(base, struct.pack('<5I', 15, 33, 0xFFFFFFF0, 81, 99))
                        else:
                            e.write(base, struct.pack('<4H', 7, 29, 0xFFFF, 83))
            return setup

        for case, (_, cfg) in zip(cases, rows):
            case.args = (worker, cfg.get('human', 0)) if human_arg else (worker,)
            case.setup = setup_for(cfg)

    t4spec.run_spec(f'src/harvest/{file_stem}_reference.c', link, addr,
                    cases, watch=watch, stubs=make_stubs(active),
                    out_regs=('eax',), init_emu=init_emu,
                    extra={
                        '_player_lumber': 0x50060,
                        '_player_gold': 0x50074,
                        '_dat_5008c': 0x5008C,
                        '_player_home_point_preceding_word': 0x50E66,
                        'HarvestDepositCargo_': 0x1CF94,
                    })


def _controlled(addr, regs, cfg, key, default=0):
    def handler(e, log):
        log(*(e.reg(reg) for reg in regs))
        return cfg.get(key, default)
    return T4Stub(addr, log_regs=regs, fn=handler)


def _order_target():
    regs = ('eax', 'edx', 'ebx', 'ecx')

    def handler(e, log):
        callback, = struct.unpack('<I', e.read(e.reg('esp') + 4, 4))
        log(*(e.reg(reg) for reg in regs), callback)
        return 0

    return T4Stub(0x2E100, log_regs=regs, fn=handler, stack_pop=4)


def test_order_update_harvest():
    def stubs(cfg):
        def find_tile(e, log):
            # The pointer is to a caller local, so compare its contents instead.
            a = e.reg('eax')
            log(*struct.unpack('<hh', e.read(a, 4)))
            if cfg.get('find'):
                e.write(a, struct.pack('<hh', 17, 29))
                return 1
            return 0

        def fatal(e, log):
            a, = struct.unpack('<I', e.read(e.reg('esp') + 4, 4))
            message = e.cstr(a, 64)
            if isinstance(message, str):
                message = message.encode('ascii')
            log(*message)
            return 0

        return (
            _controlled(0x10D34, ('eax', 'edx'), cfg, 'retaliate'),
            _controlled(0x222D8, ('eax',), cfg, 'arrived'),
            T4Stub(0x1CD50, log_regs=('eax',)),
            T4Stub(0x2EEAC, log_regs=('eax', 'edx')),
            _order_target(),
            _controlled(0x2BB7C, ('eax',), cfg, 'clear'),
            T4Stub(0x2BBE4, log_regs=('eax',), fn=find_tile),
            T4Stub(0x1DE60, ret=6, log_regs=('eax', 'edx')),
            T4Stub(0x1BC0C, log_regs=('eax',)),
            T4Stub(0x26360, log_regs=('eax', 'edx')),
            T4Stub(0x2BB38, log_regs=('eax',)),
            T4Stub(0x1C9C0, log_regs=('eax',)),
            T4Stub(0x30BF0, log_regs=(), fn=fatal),
        )

    _run('order_update_harvest', 'OrderUpdateHarvest_', 0x1CD90, [
        ('retaliation short-circuits', dict(human=1, retaliate=1)),
        ('missing mine', dict(flags=0x80, no_target=True)),
        ('blocked mine state', dict(flags=0x80, state=0x200)),
        ('gold wins over lumber; approach mine', dict(flags=0xC0, retaliate=0x10000)),
        ('arrived at mine', dict(flags=0x80, arrived=1)),
        ('invalid harvest flags', dict(flags=0x08)),
        ('approach lumber tile', dict(flags=0x40)),
        ('blocked tile, no alternative', dict(flags=0x40, arrived=1)),
        ('blocked tile, alternate coordinates', dict(flags=0x40, arrived=1, find=True)),
        ('first work tick turns worker', dict(flags=0x40, arrived=1, clear=1)),
        ('last work tick before completion', dict(flags=0x40, arrived=1, clear=1, ticks=49)),
        ('completion with hall', dict(flags=0x40, arrived=1, clear=1, ticks=50, hall=True)),
        ('completion without hall and tick wraps', dict(flags=0x40, arrived=1, clear=1, ticks=255)),
    ], stubs, human_arg=True)


def test_harvest_deposit_cargo():
    def stubs(_):
        return (T4Stub(0x1C9C0, log_regs=('eax',)),)

    _run('harvest_deposit_cargo', 'HarvestDepositCargo_', 0x1CF94, [
        ('below first range', dict(type=0x27, flags=0xE0)),
        ('first hall, gold and lumber bits', dict(type=0x28, flags=0xE8)),
        ('second hall, lumber', dict(type=0x29, flags=0x60, owner=1)),
        ('above first range', dict(type=0x2A, flags=0x60)),
        ('below second range', dict(type=0x2F, flags=0xA0)),
        ('first alternate hall, no cargo kind', dict(type=0x30, flags=0x28)),
        ('second alternate hall, lumber', dict(type=0x31, flags=0x60, owner=3)),
        ('above second range', dict(type=0x32, flags=0xA0)),
        ('unsigned type maximum', dict(type=0xFF, flags=0xA0)),
    ], stubs, extra_watch=RESOURCE_WATCH)


def test_order_update_harvest_enter_building():
    def stubs(cfg):
        return (
            T4Stub(0x2207C, log_regs=('eax',)),
            T4Stub(0x13954, log_regs=('eax',)),
            T4Stub(0x25E58, log_regs=('eax',)),
            T4Stub(0x2E9C4, log_regs=('eax', 'edx', 'ebx')),
            T4Stub(0x2EE50, log_regs=('eax', 'edx')),
            T4Stub(0x2EEAC, log_regs=('eax', 'edx')),
            _controlled(0x1CF94, ('eax',), cfg, 'deposit'),
            T4Stub(0x1C9C0, log_regs=('eax',)),
            T4Stub(0x2E384, log_regs=('eax',)),
        )

    _run('order_update_harvest_enter_building', 'OrderUpdateHarvestEnterBuilding_', 0x1D034, [
        ('missing building', dict(no_target=True)),
        ('worker owns tile and steps off', dict(own_tile=True)),
        ('worker is off-map; claim empty entry slot', dict()),
        ('already stepped off; entry slot busy', dict(flags=0x10, count=2, own_tile=True)),
        ('successful deposit skips extraction', dict(flags=0xA0, state=0x80, deposit=1, remaining=101)),
        ('empty resource', dict(flags=0x08, state=0x80, type=0x20)),
        ('small resource exhausted', dict(flags=0x08, state=0x80, remaining=4, type=0x20)),
        ('exactly 100 exhausted', dict(flags=0x08, state=0x80, remaining=100, type=0x20)),
        ('100 cap leaves resource', dict(state=0x80, remaining=101, type=0x20)),
        ('unsigned resource count', dict(state=0x80, remaining=0xFFFFFFFF, type=0x20)),
        ('controller alone does not cap to five', dict(state=0x80, controller=1, remaining=9, type=0x20)),
        ('building flag alone does not cap to five', dict(state=0x80, building_flags=0x100, remaining=9, type=0x20)),
        ('controller and building flag cap to five', dict(state=0x80, controller=1, building_flags=0x100, remaining=101, type=0x20)),
        ('five cap does not increase small yield', dict(state=0x80, controller=1, building_flags=0x100, remaining=4, type=0x20)),
    ], stubs, use_map=True)


def test_order_update_harvest_exit_building():
    def stubs(cfg):
        return (
            _controlled(0x2E5C8, ('eax', 'edx'), cfg, 'exit_result', 1),
            _controlled(0x2B064, ('eax',), cfg, 'ai_result'),
            _order_target(),
        )

    _run('order_update_harvest_exit_building', 'OrderUpdateHarvestExitBuilding_', 0x1D1E0, [
        ('blocked exit still clears size-selector bit', dict(flags=0x2C, exit_result=0)),
        ('zero low word returns full stub result', dict(flags=0x08, exit_result=0x12340000)),
        ('cargo routes to hall at signed home coordinates', dict(flags=0x2C, hall=True, controller=1)),
        ('cargo dispatch with null hall', dict(flags=0x20, owner=0)),
        ('AI takes over before resume', dict(flags=0x08, controller=1, ai_result=1)),
        ('AI declines on zero low word, resume saved target', dict(flags=0x08, controller=1, ai_result=0x10000)),
        ('other controller resumes without AI call', dict(flags=0x0C, controller=2)),
        ('no saved-order bit', dict(flags=0)),
    ], stubs)
