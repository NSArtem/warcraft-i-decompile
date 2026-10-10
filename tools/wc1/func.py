"""Print one function (or address range) as symbolic asm, using current
symbol-database names. Safe to run concurrently (writes nothing).

usage: python3 -m wc1.func <addr-hex|name> [--raw]
"""
import sys

from . import analysis, emit, path, symbols


def resolve(p, arg):
    try:
        return int(arg, 16)
    except ValueError:
        funcs, datas, _ = symbols.load(strict=False)
        for t in (funcs, datas):
            for a, e in t.items():
                if arg in (e["name"], e["link_name"]):
                    return a
    raise SystemExit(f"unknown symbol {arg}")


def main():
    p = analysis.run()
    funcs, datas, _ = symbols.load(strict=False)
    names = {e["addr"]: e["link_name"] for t in (datas, funcs) for e in t.values()}
    a = resolve(p, sys.argv[1])
    f = next((f for f in p.functions if f["start"] <= a < f["limit"]), None)
    if f is None:
        raise SystemExit(f"{a:#x} is not inside a discovered function")
    e = emit.Emitter(p, names=names)
    meta = funcs.get(f["start"])
    print(f"; function {f['start']:#x}..{f['limit']:#x} ({f['ninsns']} insns)")
    if meta:
        print(f"; {meta.get('proto', meta['name'])}  [{meta['confidence']}]")
    if f["cross"]:
        print(f"; non-call flow leaves the function to: {[hex(c) for c in f['cross']]}")
    x = f["start"]
    while x < f["limit"]:
        if x in e.labels:
            print(f"{e.labels[x]}:")
        if x in p.insns:
            i = p.insns[x]
            t = e.insn_text(i) or f"{i.mnemonic} {i.op_str}"
            print(f"  {x:05x}  {t}")
            x += i.size
        else:
            if x in p.fix_at:
                print(f"  {x:05x}  dd {e.sym(p.fix_at[x][1])}")
                x += 4
            else:
                y = x
                while y < f["limit"] and y not in p.insns and y not in p.fix_at and (y == x or y not in e.labels):
                    y += 1
                print(f"  {x:05x}  db {p.cbytes[x - p.code.base:y - p.code.base].hex()}")
                x = y


if __name__ == "__main__":
    main()
