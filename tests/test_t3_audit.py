"""wc1.t3_audit (no toolchain, no war.exe): the compiler, the comparison and
the buildability check are faked; the symbol database and the progress rows
are built in the test."""
import copy
import hashlib
import json
import os
import shutil

import pytest

from wc1 import match, permuter, t3_audit as ta

HDR = "/* codegen-compiler: 10.0a */\n/* codegen-flags: -s -ot -oa -4r -zp2 */\n"
DECL = "-s -ot -oa -4r -zp2"
TSIG = "a" * 64
GIT_COMMIT = "c0ffee" * 6 + "c0ff"
BY_LINK = {"Helper_": {"addr": 0x900}, "A_": {"addr": 0x100}}


def presets():
    return [s for cc, s in permuter.FLAG_PRESETS if cc == "10.0a" and s != DECL]


class Mod:
    def __init__(self, short, names):
        self.short = short
        self.publics = {n: (1, i * 16) for i, n in enumerate(names)}

    def seg(self, name):
        return (1, object()) if name == "_TEXT" else (None, None)


class Fake:
    """`funcs`: ref basename -> list of link names in its _TEXT.
    `match`: (link, flags) pairs that match; `data_bad`: flags under which a
    data row differs; `errors` / `timeouts`: flags (or (file, flags)) that
    fail to compile; `score`: (link, flags) -> score tuple; `build`: (ok,
    reason); `extra`: more match_module rows; `gate`: file -> callable run
    before its compile."""

    def __init__(self, files, match=(), data_bad=(), errors=(), timeouts=(), score=None,
                 build=(True, None), build_raises=None, extra=(), gate=None):
        self.files, self.match = files, set(match)
        self.extra, self.gate = list(extra), gate or {}
        self.data_bad, self.errors, self.timeouts = set(data_bad), set(errors), set(timeouts)
        self.score, self.build, self.build_raises = score or {}, build, build_raises
        self.compiles, self.builds = [], []

    def compile_c(self, src, cflags, out, cc=None, includes=(), timeout=None, quiet=False):
        assert cc == "10.0a" and quiet and cflags.startswith(match.BASE_CFLAGS)
        assert includes == (os.path.dirname(src),)
        short = cflags[len(match.BASE_CFLAGS):].strip()
        base = os.path.basename(src)
        self.compiles.append((base, short))
        if base in self.gate:
            self.gate[base]()
        open(out, "w").write("obj")
        open(out + ".log", "w").write("log")
        if short in self.timeouts or (base, short) in self.timeouts:
            raise match.CompileTimeout("error: wcc386 timed out after 180 s")
        if short in self.errors or (base, short) in self.errors:
            raise SystemExit(f"{src}(3): Error! E1009: Expecting ';'")
        return Mod(short, self.files[os.path.basename(src)])

    def match_module(self, p, mod, by_link, verbose=False):
        rows = [(n, "MATCH" if (n, mod.short) in self.match else "MISMATCH",
                 [] if (n, mod.short) in self.match else [f"{n}: insn 3 differs"])
                for n in mod.publics]
        rows += self.extra
        rows.append(("[DATA @ 0x50000, 4 bytes]",
                     "MISMATCH" if mod.short in self.data_bad else "MATCH", []))
        return rows

    def diff_function(self, p, mod, by_link, name=None, orig_addr=None, context=3):
        return {"matched": False, "status": "MISMATCH",
                "score": self.score.get((name, mod.short), (9, 9, 9, 0, 0)),
                "counts": {"orig": 10, "c": 11}, "first_diff": f"{name}@{mod.short}: mov",
                "lines": ["- mov eax,1", "+ mov eax,2"]}

    def check_buildable(self, p, funcs, src, obj, entries):
        assert os.path.isfile(obj)
        self.builds.append((src, sorted(e["link_name"] for e in entries)))
        if self.build_raises:
            raise self.build_raises
        return self.build

    def hook(self, ctx):
        ctx.compile_c, ctx.match_module = self.compile_c, self.match_module
        ctx.diff_function, ctx.check_buildable = self.diff_function, self.check_buildable


@pytest.fixture
def repo(tmp_path, monkeypatch):
    root = tmp_path / "repo"
    for d in ("src/m", "analysis/symbols", "build"):
        (root / d).mkdir(parents=True)
    monkeypatch.setattr(ta, "path", lambda *a: str(root.joinpath(*a)))
    monkeypatch.setattr(ta, "_git", lambda *a: "c0ffee" if a[0] == "rev-parse" else "")
    monkeypatch.setattr(ta, "toolchain_id", lambda: {"compiler": "Watcom 10.0a", "root": "/wc",
                                                     "manifest_sha256": "ab" * 32,
                                                     "manifest_problems": []})
    return root


def entry(addr, name, ref, link=None, **kw):
    e = {"name": name, "link_name": link if link is not None else name, "module": "M.C",
         "ref": ref, "_file": "analysis/symbols/m.toml", "_kind": "func",
         "ref_verified_by": "difftest:tests/test_m.py::t", "t3_blocker": "codegen"}
    e.update(kw)
    return e


def row(addr, c="T4", scope="in"):
    return {"addr": addr, "module": "m", "kind": "game", "scope": scope, "c": c}


def make_inputs(root, spec):
    """`spec`: [(addr, name, ref file under src/m or None, c, scope, extra)]."""
    funcs, rows = {}, []
    for addr, name, ref, c, scope, kw in spec:
        rel = f"src/m/{ref}" if ref else None
        if ref and kw.pop("_write", True) and not (root / rel).exists():
            (root / rel).write_text(HDR + "int f(void) { return 0; }\n")
        e = entry(addr, name, rel, **kw)
        if c == "ref":
            e.pop("ref_verified_by")
        funcs[addr] = e
        if not kw.get("_undiscovered"):
            rows.append(row(addr, c, scope))
    by_link = {e["link_name"]: e for e in funcs.values() if e.get("link_name")}
    return object(), funcs, by_link, rows, []


def args(*argv, out=None):
    return ta.parse_args(list(argv) + (["--output", str(out)] if out else []))


def audit(repo, spec, fake, *argv):
    out = repo / "build" / "t3_audit"
    inp = make_inputs(repo, spec)
    logs = []
    code = ta.run(args(*argv, out=out), list(argv), inputs=inp, log=logs.append, ctx_hook=fake.hook)
    rep = json.loads((out / "report.json").read_text()) if (out / "report.json").exists() else None
    return code, rep, out, logs


def res(rep, addr):
    return next(r for r in rep["results"] if r["addr"] == addr)


# --- discovery / selection -----------------------------------------------------

def test_discovery_selects_in_scope_t4_only(repo):
    _p, funcs, _bl, rows, _ = make_inputs(repo, [
        (0x100, "A", "a.c", "T4", "in", {}),
        (0x200, "B", "b.c", "ref", "in", {}),
        (0x300, "C", "c.c", "T4", "out", {}),
        (0x400, "D", None, "T3", "in", {"src": "src/m/d.c"}),
        (0x500, "E", "e.c", "T4", "in", {"_undiscovered": True}),
    ])
    cands, issues = ta.discover(funcs, rows)
    assert [(c["addr"], c["tier"]) for c in cands] == [(0x100, "T4")]
    c = cands[0]
    assert c["ref"] == "src/m/a.c" and c["toml"] == "analysis/symbols/m.toml"
    assert c["declared_cc"] == "10.0a" and c["declared_cflags"] == DECL
    assert c["t3_blocker"] == "codegen" and c["skip_reason"] is None
    assert any("0x500" in i and "not a discovered function start" in i for i in issues)
    cands, _ = ta.discover(funcs, rows, include_unverified=True)
    assert [(c["addr"], c["tier"], c["diagnostic_only"]) for c in cands] == \
        [(0x100, "T4", False), (0x200, "ref", True)]


def test_discovery_invalid_and_ambiguous_entries_are_skipped(repo):
    (repo / "src/m/bad.c").write_text("/* codegen-compiler: 9.9 */\n")
    (repo / "src/m/h.h").write_text("")
    _p, funcs, _bl, rows, _ = make_inputs(repo, [
        (0x100, "Missing", "gone.c", "T4", "in", {"_write": False}),
        (0x110, "NoLink", "a.c", "T4", "in", {"link": ""}),
        (0x120, "BadCC", "bad.c", "T4", "in", {}),
        (0x130, "Hdr", "h.h", "T4", "in", {}),
        (0x140, "Dup1", "d.c", "T4", "in", {"link": "Dup"}),
        (0x150, "Dup2", "d.c", "T4", "in", {"link": "Dup"}),
        (0x160, "Ok", "a.c", "T4", "in", {}),
    ])
    cands, issues = ta.discover(funcs, rows)
    why = {c["name"]: c["skip_reason"] or "" for c in cands}
    assert "does not exist" in why["Missing"]
    assert "no link name" in why["NoLink"]
    assert "unknown codegen-compiler" in why["BadCC"]
    assert "not a repository .c path" in why["Hdr"]
    assert why["Dup1"].startswith("ambiguous mapping") and why["Dup2"] == why["Dup1"]
    assert why["Ok"] == ""
    assert len(issues) == 6           # one per skipped entry (both of the ambiguous pair)
    assert [u["ref"] for u in ta.group_units(cands)] == ["src/m/a.c"]


def test_select_addr_and_limit(repo):
    _p, funcs, _bl, rows, _ = make_inputs(repo, [(a, f"F{a:x}", f"f{a:x}.c", "T4", "in", {})
                                                 for a in (0x300, 0x100, 0x200)])
    cands, _ = ta.discover(funcs, rows)
    assert [c["addr"] for c in cands] == [0x100, 0x200, 0x300]
    assert [c["addr"] for c in ta.select(cands, limit=2)[0]] == [0x100, 0x200]
    sel, errs = ta.select(cands, addrs=[0x300, 0x999])
    assert [c["addr"] for c in sel] == [0x300] and errs and "0x999" in errs[0]


def test_attempt_plan_declared_first_then_presets_without_repeats():
    plan = ta.attempt_plan("-s  -ot -oa -4r  -zp2")
    assert plan[0] == ("declared", DECL)
    assert [s for _l, s in plan[1:]] == presets()
    assert len({s for _l, s in plan}) == len(plan)
    assert all(l == "preset" for l, _s in plan[1:])
    plan = ta.attempt_plan("-s -od -4r -zp2 -d2")      # not a preset: all 8 presets follow
    assert len(plan) == 1 + sum(1 for cc, _ in permuter.FLAG_PRESETS if cc == "10.0a")


def test_cli_arguments():
    a = ta.parse_args([])
    assert a.jobs == 1 and a.limit is None and a.addr == [] and not a.dry_run
    a = ta.parse_args(["--addr", "0x12404", "--addr", "2c4e0", "--limit", "3", "--jobs", "2",
                       "--include-unverified", "--dry-run", "--output", "x"])
    assert a.addr == [0x12404, 0x2c4e0] and a.limit == 3 and a.jobs == 2
    assert a.include_unverified and a.dry_run and a.output == "x"
    for bad in (["--limit", "0"], ["--jobs", "0"], ["--addr", "zz"]):
        with pytest.raises(SystemExit):
            ta.parse_args(bad)


# --- classification --------------------------------------------------------------

def test_declared_flags_match_is_buildable_after_one_compile(repo):
    fake = Fake({"a.c": ["A"]}, match={("A", DECL)})
    code, rep, out, _ = audit(repo, [(0x100, "A", "a.c", "T4", "in", {})], fake)
    assert code == 0
    r = res(rep, 0x100)
    assert r["status"] == "MATCH_BUILDABLE" and r["match_flags"] == DECL
    assert r["match_label"] == "declared" and r["flags_change"] is False
    assert fake.compiles == [("a.c", DECL)]
    assert fake.builds == [("src/m/a.c", ["A"])]
    assert rep["promotion_candidates"][0]["addr_hex"] == "0x100"
    assert rep["meta"]["completion"] == {"status": "complete", "selected": 1, "audited": 1, "note": None}
    assert not (out / "obj").exists()


def test_preset_match_records_every_attempt_and_stops(repo):
    hit = presets()[1]
    fake = Fake({"a.c": ["A"]}, match={("A", hit)})
    _code, rep, _out, _ = audit(repo, [(0x100, "A", "a.c", "T4", "in", {})], fake)
    r = res(rep, 0x100)
    assert r["status"] == "MATCH_BUILDABLE" and r["match_flags"] == hit and r["flags_change"]
    assert [a["result"] for a in r["attempts"]] == ["MISMATCH", "MISMATCH", "MATCH"]
    assert [a["cflags"] for a in r["attempts"]] == [DECL] + presets()[:2]
    assert len(fake.compiles) == 3 and rep["meta"]["compiles"] == 3


def test_unresolved_inventory_is_not_truncated_or_limited_to_best_attempt(repo):
    def diagnostic(*args, **kwargs):
        d = Fake.diff_function(fake, *args, **kwargs)
        mod = args[1]
        names = ["callee_", "_table", "_other", "_fourth"]
        if mod.short != DECL:
            names += ["_non_best_only"]
        return dict(d, unresolved=[{"symbol": n, "offset": i}
                                   for i, n in enumerate(names + ["callee_"])])

    fake = Fake({"a.c": ["A"]}, score={("A", DECL): (0, 0, 0, 0, 0)})
    fake.diff_function = diagnostic
    _, rep, _, _ = audit(repo, [(0x100, "A", "a.c", "T4", "in", {})], fake)
    row = res(rep, 0x100)
    assert row["status"] == "MISMATCH" and len(row["best"]["unresolved"]) == 5
    assert rep["stats"]["T4"]["unresolved_best"] == {"functions": 1, "symbols": 4}
    assert rep["stats"]["T4"]["unresolved_any_attempt"] == {"functions": 1, "symbols": 5}


def test_mismatch_keeps_best_flags_by_score(repo):
    best = presets()[3]
    fake = Fake({"a.c": ["A"]}, score={("A", best): (1, 0, 2, 0, 0)})
    _code, rep, _out, _ = audit(repo, [(0x100, "A", "a.c", "T4", "in", {})], fake)
    r = res(rep, 0x100)
    assert r["status"] == "MISMATCH"
    assert r["best"]["cflags"] == best and r["best"]["score"] == [1, 0, 2, 0, 0]
    assert r["best"]["first_diff"] == f"A@{best}: mov" and r["best"]["counts"]
    assert len(r["attempts"]) == len(ta.attempt_plan(DECL))
    assert rep["near_misses"][0]["best_flags"] == best
    assert rep["ranking_note"] and "not a probability" in rep["ranking_note"]


def test_compile_errors(repo):
    fake = Fake({"a.c": ["A"], "b.c": ["B"]}, match={("B", presets()[0])},
                errors={DECL} | (set(presets()) - {presets()[0]}))
    _code, rep, _out, _ = audit(repo, [(0x100, "A", "a.c", "T4", "in", {}),
                                       (0x200, "B", "b.c", "T4", "in", {})], fake)
    a, b = res(rep, 0x100), res(rep, 0x200)
    assert a["status"] == "MISMATCH"          # presets()[0] compiled, never matched
    fake2 = Fake({"c.c": ["C"]}, errors={s for _l, s in ta.attempt_plan(DECL)})
    _code, rep2, _out, _ = audit(repo, [(0x300, "C", "c.c", "T4", "in", {})], fake2)
    c = res(rep2, 0x300)
    assert c["status"] == "COMPILE_ERROR" and "E1009" in c["reason"]
    assert all(x["result"] == "COMPILE_ERROR" for x in c["attempts"])
    assert b["status"] == "MATCH_BUILDABLE"
    assert [x["result"] for x in b["attempts"]] == ["COMPILE_ERROR", "MATCH"]


def test_unbuildable_reasons(repo):
    spec = [(0x100, "A", "a.c", "T4", "in", {})]
    fake = Fake({"a.c": ["A"]}, match={("A", DECL)}, build=(False, "legacy layout: offset"))
    _c, rep, _o, _ = audit(repo, spec, fake)
    r = res(rep, 0x100)
    assert r["status"] == "MATCH_UNBUILDABLE" and "legacy layout" in r["reason"]
    assert rep["unbuildable_matches"][0]["addr_hex"] == "0x100" and not rep["promotion_candidates"]
    # a crashing check is a "no", not a crash of the audit
    fake = Fake({"a.c": ["A"]}, match={("A", DECL)}, build_raises=RuntimeError("boom"))
    _c, rep, _o, _ = audit(repo, spec, fake)
    assert res(rep, 0x100)["status"] == "MATCH_UNBUILDABLE"
    assert "check failed: boom" in res(rep, 0x100)["reason"]
    # the function matches but a data row of the object never does
    plan = [s for _l, s in ta.attempt_plan(DECL)]
    fake = Fake({"a.c": ["A"]}, match={("A", DECL)}, data_bad=set(plan))
    _c, rep, _o, _ = audit(repo, spec, fake)
    r = res(rep, 0x100)
    assert r["status"] == "MATCH_UNBUILDABLE" and "DATA" in r["reason"]
    assert fake.builds == [] and len(fake.compiles) == 1


def test_shared_file_needs_one_flag_set_for_the_whole_object(repo):
    p0, p1 = presets()[0], presets()[1]
    spec = [(0x100, "A", "s.c", "T4", "in", {}), (0x200, "B", "s.c", "T4", "in", {})]
    # A matches under the declared flags and p1, B only under p1: p1 builds both
    fake = Fake({"s.c": ["A", "B"]}, match={("A", DECL), ("B", p1), ("A", p1)})
    _c, rep, _o, _ = audit(repo, spec, fake)
    assert [res(rep, a)["status"] for a in (0x100, 0x200)] == ["MATCH_BUILDABLE"] * 2
    assert {res(rep, a)["match_flags"] for a in (0x100, 0x200)} == {p1}
    assert fake.compiles == [("s.c", DECL), ("s.c", p0), ("s.c", p1)]
    assert fake.builds == [("src/m/s.c", ["A", "B"])]
    # never under one set: both are exact matches that do not build
    fake = Fake({"s.c": ["A", "B"]}, match={("A", DECL), ("B", p1)})
    _c, rep, _o, _ = audit(repo, spec, fake)
    assert [res(rep, a)["status"] for a in (0x100, 0x200)] == ["MATCH_UNBUILDABLE"] * 2
    assert res(rep, 0x100)["match_flags"] == DECL and res(rep, 0x200)["match_flags"] == p1
    assert "no flag set matches the whole object" in res(rep, 0x200)["reason"]
    # a non-candidate function of the file differs: never whole
    fake = Fake({"s.c": ["A", "B", "Other"]}, match={("A", DECL), ("B", DECL)})
    _c, rep, _o, _ = audit(repo, spec, fake)
    assert res(rep, 0x100)["status"] == "MATCH_UNBUILDABLE" and "Other" in res(rep, 0x100)["reason"]
    assert len(fake.compiles) == 1


def test_link_name_not_in_object_is_skipped(repo):
    fake = Fake({"a.c": ["Something"]})
    _c, rep, _o, _ = audit(repo, [(0x100, "A", "a.c", "T4", "in", {})], fake)
    r = res(rep, 0x100)
    assert r["status"] == "SKIPPED" and r["reason"].startswith("link name not in object")
    assert "Something" in r["reason"] and len(r["attempts"]) == len(presets()) + 1


# --- run control -------------------------------------------------------------------

def test_timeout_is_a_toolchain_error_and_stops_the_run(repo):
    spec = [(0x100, "A", "a.c", "T4", "in", {}), (0x200, "B", "b.c", "T4", "in", {}),
            (0x300, "C", "c.c", "T4", "in", {})]
    fake = Fake({"a.c": ["A"], "b.c": ["B"], "c.c": ["C"]}, match={("A", DECL)})
    orig = fake.compile_c

    def compile_c(src, cflags, out, **kw):
        if src.endswith("b.c"):
            fake.timeouts.add(cflags[len(match.BASE_CFLAGS):].strip())
        return orig(src, cflags, out, **kw)

    fake.compile_c = compile_c
    code, rep, out, logs = audit(repo, spec, fake)
    assert code == ta.EXIT_TOOLCHAIN
    assert [res(rep, a)["status"] for a in (0x100, 0x200, 0x300)] == \
        ["MATCH_BUILDABLE", "TOOLCHAIN_ERROR", "SKIPPED"]
    assert res(rep, 0x300)["reason"] == ta.NOT_REACHED
    assert ("c.c", DECL) not in fake.compiles
    comp = rep["meta"]["completion"]
    assert comp["status"] == "aborted" and comp["audited"] == 1 and "[TOOLCHAIN ERROR]" in comp["note"]
    md = (out / "report.md").read_text()
    assert "INCOMPLETE RUN (aborted)" in md
    assert any("[TOOLCHAIN ERROR]" in l for l in logs)
    assert not (out / "obj").exists()


def test_interrupt_is_reported_partial(repo):
    spec = [(0x100, "A", "a.c", "T4", "in", {}), (0x200, "B", "b.c", "T4", "in", {})]
    fake = Fake({"a.c": ["A"], "b.c": ["B"]}, match={("A", DECL)})
    orig = fake.compile_c

    def compile_c(src, *a, **kw):
        if src.endswith("b.c"):
            raise KeyboardInterrupt
        return orig(src, *a, **kw)

    fake.compile_c = compile_c
    code, rep, out, _ = audit(repo, spec, fake)
    assert code == ta.EXIT_INTERRUPTED
    assert rep["meta"]["completion"]["status"] == "interrupted"
    assert res(rep, 0x200)["status"] == "SKIPPED" and res(rep, 0x100)["status"] == "MATCH_BUILDABLE"


def test_parallel_jobs_give_the_same_report(repo):
    spec = [(a, f"F{a:x}", f"f{a:x}.c", "T4", "in", {}) for a in range(0x100, 0x700, 0x100)]
    files = {f"f{a:x}.c": [f"F{a:x}"] for a in range(0x100, 0x700, 0x100)}
    m = {(f"F{a:x}", DECL) for a in (0x200, 0x500)}
    _c, r1, _o, _ = audit(repo, spec, Fake(files, match=m))
    _c, r2, _o, _ = audit(repo, spec, Fake(files, match=m), "--jobs", "3")
    assert r1["results"] == r2["results"] and r1["stats"] == r2["stats"]
    assert r1["stats"]["T4"]["MATCH_BUILDABLE"] == 2 and r1["stats"]["T4"]["MISMATCH"] == 4


def test_reports_are_deterministic_and_replace_stale_ones(repo):
    spec = [(0x200, "B", "b.c", "T4", "in", {}), (0x100, "A", "a.c", "T4", "in", {}),
            (0x300, "R", "r.c", "ref", "in", {})]
    files = {"a.c": ["A"], "b.c": ["B"], "r.c": ["R"]}
    out = repo / "build" / "t3_audit"
    out.mkdir(parents=True)
    (out / "report.csv").write_text("stale")
    (out / "report.md").write_text("stale")
    _c, r1, _o, _ = audit(repo, spec, Fake(files, match={("A", DECL), ("R", DECL)}))
    t1 = {f: (out / f).read_text() for f in ta.REPORT_FILES}
    _c, r2, _o, _ = audit(repo, spec, Fake(files, match={("A", DECL), ("R", DECL)}))
    t2 = {f: (out / f).read_text() for f in ta.REPORT_FILES}
    for r in (r1, r2):
        r["meta"].pop("started"), r["meta"].pop("finished")
    assert r1 == r2
    assert t1["report.csv"] == t2["report.csv"] and "stale" not in t1["report.csv"]
    assert [r["addr"] for r in r1["results"]] == [0x100, 0x200]       # ref-only not selected
    lines = t1["report.csv"].splitlines()
    assert lines[0].startswith("addr,name") and len(lines) == 3
    assert "INCOMPLETE" not in t1["report.md"] and "SUBSET" not in t1["report.md"]
    assert r1["meta"]["scope"]["full_scope"] and r1["meta"]["git_commit"] == "c0ffee"
    # ref-only entries are diagnostics: counted apart, never promoted
    _c, r3, _o, _ = audit(repo, spec, Fake(files, match={("A", DECL), ("R", DECL)}),
                          "--include-unverified")
    assert res(r3, 0x300)["status"] == "MATCH_BUILDABLE" and res(r3, 0x300)["tier"] == "ref"
    assert [p["addr_hex"] for p in r3["promotion_candidates"]] == ["0x100"]
    assert r3["stats"]["ref"]["MATCH_BUILDABLE"] == 1 and r3["stats"]["T4"]["total"] == 2
    assert "diagnostics only" in (out / "report.md").read_text()


def test_subset_is_marked(repo):
    spec = [(0x100, "A", "a.c", "T4", "in", {}), (0x200, "B", "b.c", "T4", "in", {})]
    _c, rep, out, _ = audit(repo, spec, Fake({"a.c": ["A"], "b.c": ["B"]}), "--limit", "1")
    assert rep["meta"]["scope"]["full_scope"] is False
    assert rep["meta"]["scope"]["filters"] == {"limit": 1}
    assert rep["meta"]["scope"]["in_scope_t4"] == 2 and rep["stats"]["T4"]["total"] == 1
    assert "SUBSET" in (out / "report.md").read_text()


def test_unknown_addr_is_an_error_and_writes_nothing(repo):
    code, rep, out, logs = audit(repo, [(0x100, "A", "a.c", "T4", "in", {})],
                                 Fake({"a.c": ["A"]}), "--addr", "0x999")
    assert code == ta.EXIT_USAGE and rep is None and any("0x999" in l for l in logs)


def test_dry_run_compiles_and_writes_nothing(repo):
    fake = Fake({"a.c": ["A"]})
    code, rep, out, logs = audit(repo, [(0x100, "A", "a.c", "T4", "in", {})], fake, "--dry-run")
    assert code == 0 and rep is None and not out.exists() and fake.compiles == []
    assert "plan:" in logs[0] and "dry run" in logs[-1]


def _tree(d):
    return {str(p.relative_to(d)): p.read_bytes() for p in sorted(d.rglob("*")) if p.is_file()}


def test_read_only_for_src_and_analysis(repo):
    spec = [(0x100, "A", "a.c", "T4", "in", {}), (0x200, "B", "b.c", "T4", "in", {})]
    make_inputs(repo, spec)
    (repo / "analysis/symbols/m.toml").write_text("[[func]]\n")
    before = {d: _tree(repo / d) for d in ("src", "analysis")}
    audit(repo, spec, Fake({"a.c": ["A"], "b.c": ["B"]}, match={("A", presets()[2])}))
    assert {d: _tree(repo / d) for d in ("src", "analysis")} == before
    for bad in ("src", "src/m", "analysis/symbols", "tools", "."):
        with pytest.raises(SystemExit):
            ta.check_output(str(repo / bad))
    ta.check_output(str(repo / "build" / "x"))


def test_main_stops_without_the_toolchain(monkeypatch, capsys):
    from wc1 import oldcc

    def missing():
        raise oldcc.OldCCError("Watcom 10.0a not installed")

    monkeypatch.setattr(oldcc, "require", missing)
    assert ta.main(["--addr", "0x12404"]) == ta.EXIT_TOOLCHAIN
    assert "[TOOLCHAIN ERROR]" in capsys.readouterr().err


# --- review follow-ups ----------------------------------------------------------------

def test_link_name_used_by_two_entries_is_ambiguous(repo):
    _p, funcs, _bl, rows, _ = make_inputs(repo, [
        (0x100, "A", "a.c", "T4", "in", {"link": "Shared_"}),
        (0x200, "B", "b.c", "T4", "in", {"link": "Shared_"}),
        (0x300, "C", "c.c", "T4", "in", {})])
    cands, issues = ta.discover(funcs, rows)
    why = {c["name"]: c["skip_reason"] or "" for c in cands}
    assert why["A"].startswith("ambiguous mapping: link name Shared_ is used by 0x100, 0x200")
    assert why["B"] == why["A"] and why["C"] == ""
    assert len(issues) == 2


def test_unknown_row_blocks_the_whole_object(repo):
    fake = Fake({"a.c": ["A"]}, match={("A", DECL)},
                extra=[("static_helper", "UNKNOWN", ["no original for static_helper"])])
    _c, rep, _o, _ = audit(repo, [(0x100, "A", "a.c", "T4", "in", {})], fake)
    r = res(rep, 0x100)
    assert r["status"] == "MATCH_UNBUILDABLE" and "static_helper: UNKNOWN" in r["reason"]
    assert fake.builds == []          # never asked check_t3_buildable


def test_buildability_timeout_is_a_toolchain_error(repo):
    spec = [(0x100, "A", "a.c", "T4", "in", {}), (0x200, "B", "b.c", "T4", "in", {})]
    fake = Fake({"a.c": ["A"], "b.c": ["B"]}, match={("A", DECL), ("B", DECL)},
                build_raises=match.CompileTimeout("error: wcc386 timed out after 180 s"))
    code, rep, out, logs = audit(repo, spec, fake)
    assert code == ta.EXIT_TOOLCHAIN and rep["meta"]["completion"]["status"] == "aborted"
    a, b = res(rep, 0x100), res(rep, 0x200)
    assert a["status"] == "TOOLCHAIN_ERROR" and "buildability check" in a["reason"]
    assert b["status"] == "SKIPPED" and b["reason"] == ta.NOT_REACHED
    assert [c[0] for c in fake.compiles] == ["a.c"]
    assert any("[TOOLCHAIN ERROR]" in l for l in logs)


def test_parallel_timeout_discards_compile_errors_beside_it(repo):
    """b.c's compile fails while a.c's times out (the wineserver kill): b's
    result is no evidence and must not be reported as COMPILE_ERROR."""
    import threading
    b_saved = threading.Event()
    spec = [(0x100, "A", "a.c", "T4", "in", {}), (0x200, "B", "b.c", "T4", "in", {}),
            (0x300, "C", "c.c", "T4", "in", {})]
    fake = Fake({"a.c": ["A"], "b.c": ["B"], "c.c": ["C"]},
                match={("B", presets()[0]), ("C", DECL)},
                errors={("b.c", DECL)}, timeouts={("a.c", DECL)},
                gate={"a.c": lambda: b_saved.wait(10)})
    out = repo / "build" / "t3_audit"

    def log(s):
        if " B " in s:
            b_saved.set()
    code = ta.run(args("--jobs", "3", out=out), ["--jobs", "3"],
                  inputs=make_inputs(repo, spec), log=log, ctx_hook=fake.hook)
    rep = json.loads((out / "report.json").read_text())
    assert b_saved.is_set() and code == ta.EXIT_TOOLCHAIN
    assert res(rep, 0x100)["status"] == "TOOLCHAIN_ERROR"
    b = res(rep, 0x200)
    assert b["status"] == "SKIPPED" and b["reason"] == ta.DISCARDED and b["attempts"] == []
    assert res(rep, 0x300)["status"] in ("MATCH_BUILDABLE", "SKIPPED")   # no compile error: kept
    assert rep["meta"]["completion"]["status"] == "aborted"


def test_sequential_compile_error_is_kept_on_abort(repo):
    spec = [(0x100, "A", "a.c", "T4", "in", {}), (0x200, "B", "b.c", "T4", "in", {})]
    fake = Fake({"a.c": ["A"], "b.c": ["B"]}, match={("A", presets()[0])},
                errors={("a.c", DECL)}, timeouts={("b.c", DECL)})
    code, rep, _o, _ = audit(repo, spec, fake)
    assert code == ta.EXIT_TOOLCHAIN
    a = res(rep, 0x100)              # --jobs 1: nothing ran beside a.c's failed compile
    assert a["status"] == "MATCH_BUILDABLE" and a["attempts"][0]["result"] == "COMPILE_ERROR"


# --- E7 preset provenance ------------------------------------------------------

def test_current_presets_match_permuter_10_0a_order_without_repeats():
    got = ta.current_presets()
    assert got[0] == "-s -ot -ol -4r -zp2"
    assert "-s -ot -ol -5r -zp2" in got and "-s -ot -oa -ol -5r -zp2" in got
    assert "-s -ot -ol -5r -d1+ -zp2" in got
    assert got.index("-s -ot -ol -5r -zp2") < got.index("-s -ot -oa -ol -5r -zp2")
    assert len(got) == len(set(got))
    assert got.count("-s -ot -ol -4r -zp2") == 1               # deduplicated
    assert " ".join(got) == " ".join(ta.current_presets())     # stable, canonical


def test_report_records_preset_and_base_flag_provenance(repo):
    fake = Fake({"a.c": ["A"]}, match={("A", DECL)})
    _c, rep, _out, _ = audit(repo, [(0x100, "A", "a.c", "T4", "in", {})], fake)
    opts = rep["meta"]["options"]
    assert opts["presets"] == ta.current_presets()
    assert opts["presets"][0] == "-s -ot -ol -4r -zp2"
    assert opts["base_flags"] == match.BASE_CFLAGS
    assert "tool_sig" in rep["meta"]["toolchain"]            # None when unavailable
    r = res(rep, 0x100)
    assert "source_digest" in r                              # None when unreadable

def test_report_source_digest_is_recorded_per_row(repo, monkeypatch):
    monkeypatch.setattr(ta, "_source_digest", lambda ref: "d" * 64)
    fake = Fake({"a.c": ["A"]}, match={("A", DECL)})
    _c, rep, _out, _ = audit(repo, [(0x100, "A", "a.c", "T4", "in", {})], fake)
    assert res(rep, 0x100)["source_digest"] == "d" * 64


# --- improved-T4 provenance snapshot (Wave 4B input) ---------------------------

def _improved_row(ref, dig, **over):
    row = {
        "addr": 0x100, "addr_hex": "0x100", "name": "A", "link_name": "A_",
        "module": "M.C", "ref": ref, "toml": "analysis/symbols/m.toml", "tier": "T4",
        "status": "MISMATCH", "declared_cc": "10.0a", "declared_cflags": DECL,
        "source_digest": dig,
        "attempts": [{"label": "declared", "cflags": DECL, "result": "MISMATCH",
                      "score": [5, 1, 0, 0, 0]}],
        "best": {"label": "preset", "cflags": "-s -ot -ol -5r -zp2", "result": "MISMATCH",
                 "score": [2, 0, 0, 0, 0], "first_diff": "A@-5r: mov", "unresolved": []},
        "omf_deps": {"complete": True, "external_symbols": ["Helper_"], "text_symbols": ["A_"],
                     "external_relocs": [{"symbol": "Helper_", "self_relative": True,
                                          "loc": 9, "addend": 0}],
                     "has_data_anchors": False},
    }
    row.update(over)
    return row


def _improved_report(repo, ref="src/m/a.c"):
    if not (repo / ref).exists():
        (repo / ref).write_text(HDR + "int f(void) { return 0; }\n")
    dig = ta.portable_source_digest(ref, repo_root=str(repo))
    assert dig
    return {"meta": {"git_commit": GIT_COMMIT, "git_dirty": False,
                     "completion": {"status": "complete"},
                     "toolchain": {"compiler": "Watcom 10.0a", "manifest_sha256": "ab" * 32,
                                   "tool_sig": TSIG},
                     "options": {"presets": ta.current_presets(),
                                 "base_flags": match.BASE_CFLAGS}},
            "results": [_improved_row(ref, dig),
                        _improved_row(ref, dig, addr=0x200, addr_hex="0x200",
                                      best={"label": "preset", "cflags": DECL,
                                            "score": [1, 0, 0, 0, 0], "unresolved": []}),
                        _improved_row(ref, dig, addr=0x300, addr_hex="0x300", tier="ref"),
                        _improved_row(ref, dig, addr=0x400, addr_hex="0x400",
                                      best={"label": "preset", "cflags": "-s -ot -ol -5r -zp2",
                                            "score": [9, 9, 9, 9, 9], "unresolved": []})]}


def test_improved_t4_records_only_keep_strictly_better_residual_mismatches(repo):
    ref = "src/m/a.c"
    recs = ta.improved_t4_records(_improved_report(repo, ref),
                                  by_link={"Helper_": {"addr": 0x900}, "A_": {"addr": 0x100}})
    assert [r["addr"] for r in recs] == [0x100]        # declared flags, ref tier, no gain: dropped
    rec = recs[0]
    assert rec["declared_cflags"] == DECL and rec["declared_score"] == [5, 1, 0, 0, 0]
    assert rec["best_flags"] == "-s -ot -ol -5r -zp2" and rec["best_score"] == [2, 0, 0, 0, 0]
    assert rec["first_diff"] == "A@-5r: mov" and rec["unresolved_count"] == 0
    assert rec["dependency_clean"] is True
    assert rec["symbols"] == {"Helper_": 0x900, "A_": 0x100}
    assert rec["omf_deps_sha256"] and rec["source_digest"] and rec["tool_sig"] == TSIG
    assert rec["compiler"] == "Watcom 10.0a" and rec["manifest_sha256"] == "ab" * 32
    assert rec["base_flags"] == match.BASE_CFLAGS and rec["presets"] == ta.current_presets()
    assert rec["git_commit"] == GIT_COMMIT
    assert not any(k.startswith("/") for v in (rec["ref"], rec["toml"]) for k in (v,))

def test_improved_record_freshness_rejects_every_stale_dimension(repo, monkeypatch):
    ref = "src/m/a.c"
    rec = ta.improved_t4_records(_improved_report(repo, ref),
                                 by_link={"Helper_": {"addr": 0x900}, "A_": {"addr": 0x100}})[0]
    (repo / "src/m/inc.h").write_text("/* v1 */\n")
    (repo / "src/m/a.c").write_text(
        HDR + '#include "inc.h"\nint f(void) { return 0; }\n')
    dig = ta.portable_source_digest(ref, repo_root=str(repo))
    rec = dict(rec, source_digest=dig)
    by_link = {"Helper_": {"addr": 0x900}, "A_": {"addr": 0x100}}
    kw = dict(repo_root=str(repo), tool_sig=TSIG, by_link=by_link)
    assert ta.is_improved_record_fresh(rec, **kw) is True
    # without by_link the symbols are unverifiable: partial, never fresh
    assert ta.is_improved_record_fresh(rec, **dict(kw, by_link=None)) is False
    assert ta.check_improved_record(rec, **dict(kw, by_link=None))["status"] == "partial"

    (repo / "src/m/inc.h").write_text("/* v2 */\n")                  # include edit
    assert ta.is_improved_record_fresh(rec, **kw) is False
    (repo / "src/m/inc.h").write_text("/* v1 */\n")
    assert ta.is_improved_record_fresh(rec, **kw) is True

    (repo / "src/m/a.c").write_text(                                  # source edit
        HDR + '#include "inc.h"\nint f(void) { return 1; }\n')
    assert ta.is_improved_record_fresh(rec, **kw) is False
    (repo / "src/m/a.c").write_text(HDR + '#include "inc.h"\nint f(void) { return 0; }\n')
    assert ta.is_improved_record_fresh(rec, **kw) is True

    assert ta.is_improved_record_fresh(rec, **dict(kw, tool_sig="b" * 64)) is False
    assert ta.is_improved_record_fresh(rec, **dict(kw, current_presets=["-s -ot -ol -4r -zp2"])) is False
    monkeypatch.setattr(ta.permuter, "FLAG_PRESETS",
                        [("10.0a", "-s -ot -ol -4r -zp2"), ("ow2", "-s -ot -ol -4r -zp2")])
    assert ta.is_improved_record_fresh(rec, **dict(kw, current_presets=None)) is False
    monkeypatch.undo()

    assert ta.is_improved_record_fresh(rec, **dict(kw, by_link={"Helper_": {"addr": 0x908}})) is False
    assert ta.is_improved_record_fresh(rec, **dict(kw, by_link={})) is False
    assert ta.is_improved_record_fresh(rec, **dict(kw, by_link={
        "Helper_": {"addr": 0x900}, "A_": {"addr": 0x100}, "Appeared_": {"addr": 0x500}})) is True

    (repo / "src/m/a.c").write_text(                                  # declared_cflags change
        "/* codegen-compiler: 10.0a */\n/* codegen-flags: -s -ot -ol -4r -zp2 */\n"
        '#include "inc.h"\nint f(void) { return 0; }\n')
    assert ta.is_improved_record_fresh(rec, **kw) is False

def test_improved_record_freshness_fails_closed_on_missing_provenance(repo):
    rec = ta.improved_t4_records(_improved_report(repo), by_link=BY_LINK)[0]
    kw = dict(repo_root=str(repo), tool_sig=TSIG, by_link=BY_LINK)
    assert ta.is_improved_record_fresh(rec, **kw) is True
    assert ta.is_improved_record_fresh(dict(rec, source_digest=None), **kw) is False
    assert ta.is_improved_record_fresh(dict(rec, tool_sig=None), **kw) is False
    assert ta.is_improved_record_fresh(dict(rec, ref="src/m/gone.c"), **kw) is False


def test_portable_source_digest_is_checkout_independent(repo, tmp_path):
    ref = "src/m/a.c"
    (repo / ref).write_text(HDR + '#include "inc.h"\nint f(void) { return 0; }\n')
    (repo / "src/m/inc.h").write_text("/* v1 */\n")
    checkout_b = tmp_path / "checkout_b"
    shutil.copytree(repo, checkout_b)
    dig_a = ta.portable_source_digest(ref, repo_root=str(repo))
    dig_b = ta.portable_source_digest(ref, repo_root=str(checkout_b))
    assert dig_a and dig_a == dig_b
    rec = ta.improved_t4_records(_improved_report(repo, ref), by_link=BY_LINK)[0]
    assert rec["source_digest"] == dig_a
    kw = dict(tool_sig=TSIG, by_link=BY_LINK)
    assert ta.is_improved_record_fresh(rec, repo_root=str(repo), **kw) is True
    assert ta.is_improved_record_fresh(rec, repo_root=str(checkout_b), **kw) is True
    (checkout_b / "src/m/inc.h").write_text("/* v2 */\n")
    assert ta.is_improved_record_fresh(rec, repo_root=str(checkout_b), **kw) is False
    (checkout_b / "src/m/inc.h").write_text("/* v1 */\n")
    # a dependency outside the repository and the compiler tree fails closed
    outside = tmp_path / "outside.c"
    outside.write_text("int g(void) { return 0; }\n")
    (checkout_b / ref).write_text(HDR + f'#include "{outside}"\nint f(void) {{ return 0; }}\n')
    assert ta.portable_source_digest(ref, repo_root=str(checkout_b)) is None


def test_portable_source_digest_system_headers_real_and_symlinked_original(tmp_path):
    ref = "src/m/a.c"
    body = HDR + "#include <sys.h>\nint f(void) { return 0; }\n"
    main_orig = tmp_path / "main" / "original"
    (main_orig / "watcom/10.0a/h").mkdir(parents=True)
    (main_orig / "watcom/10.0a/h/sys.h").write_text("/* sys v1 */\n")

    real_repo = tmp_path / "real_repo"                 # original/ is a real directory
    (real_repo / "src/m").mkdir(parents=True)
    (real_repo / ref).write_text(body)
    shutil.copytree(main_orig, real_repo / "original")
    real_h = real_repo / "original/watcom/10.0a/h"

    link_repo = tmp_path / "link_repo"                 # original/ symlinks the main checkout
    (link_repo / "src/m").mkdir(parents=True)
    (link_repo / ref).write_text(body)
    (link_repo / "original").symlink_to(main_orig, target_is_directory=True)
    link_h = link_repo / "original/watcom/10.0a/h"

    dig_real = ta.portable_source_digest(ref, repo_root=str(real_repo), system_headers=str(real_h))
    dig_link = ta.portable_source_digest(ref, repo_root=str(link_repo), system_headers=str(link_h))
    assert dig_real and dig_real == dig_link
    (real_h / "sys.h").write_text("/* sys v2 */\n")
    assert ta.portable_source_digest(ref, repo_root=str(real_repo),
                                     system_headers=str(real_h)) != dig_real


@pytest.mark.parametrize("path, value", [
    (("git_dirty",), True),
    (("completion", "status"), "aborted"),
    (("completion", "status"), "interrupted"),
])
def test_improved_t4_records_refuse_dirty_or_incomplete_reports(repo, path, value):
    report = _improved_report(repo)
    assert ta.improved_t4_records(report)
    target = report["meta"]
    for key in path[:-1]:
        target = target[key]
    target[path[-1]] = value
    assert ta.improved_t4_records(report) == []


@pytest.mark.parametrize("mutate", [
    lambda m: m.pop("git_dirty"),
    lambda m: m.pop("completion"),
    lambda m: m.pop("options"),
    lambda m: m["options"].pop("presets"),
    lambda m: m["options"].pop("base_flags"),
    lambda m: m["options"].__setitem__("presets", []),
    lambda m: m["options"].__setitem__("presets", "not-a-list"),
    lambda m: m["options"].__setitem__("base_flags", ""),
])
def test_improved_t4_records_require_valid_report_options(repo, mutate):
    report = _improved_report(repo)
    assert ta.improved_t4_records(report)
    mutate(report["meta"])
    assert ta.improved_t4_records(report) == []


def test_improved_t4_records_stamp_report_presets_and_never_launder(repo):
    old_presets = ["-s -ot -ol -4r -zp2"]
    old_base = "-q -zl -bt=dos -old"
    report = _improved_report(repo)
    report["meta"]["options"]["presets"] = old_presets
    report["meta"]["options"]["base_flags"] = old_base
    recs = ta.improved_t4_records(report)
    assert recs
    assert all(r["presets"] == old_presets and r["base_flags"] == old_base for r in recs)
    kw = dict(repo_root=str(repo), tool_sig=TSIG)
    assert ta.is_improved_record_fresh(recs[0], **kw) is False

    report = _improved_report(repo)
    report["meta"]["options"]["presets"] = old_presets     # only the presets differ
    rec = ta.improved_t4_records(report)[0]
    assert rec["presets"] == old_presets and rec["base_flags"] == match.BASE_CFLAGS
    assert ta.is_improved_record_fresh(rec, **kw) is False


def test_improved_record_freshness_checks_omf_dependency_digest(repo):
    report = _improved_report(repo)
    rec = ta.improved_t4_records(report, by_link=BY_LINK)[0]
    omf = report["results"][0]["omf_deps"]
    kw = dict(repo_root=str(repo), tool_sig=TSIG, by_link=BY_LINK)
    assert ta.is_improved_record_fresh(rec, omf_deps=omf, **kw) is True
    assert ta.is_improved_record_fresh(
        rec, omf_deps=dict(omf, external_symbols=["Other_"]), **kw) is False
    assert ta.is_improved_record_fresh(dict(rec, omf_deps_sha256=None), **kw) is False
    assert ta.is_improved_record_fresh(dict(rec, omf_deps_sha256="xyz"), **kw) is False
    assert ta.is_improved_record_fresh(dict(rec, omf_deps_sha256="A" * 64), **kw) is False
    missing = {k: v for k, v in rec.items() if k != "omf_deps_sha256"}
    assert ta.is_improved_record_fresh(missing, **kw) is False


def test_build_improved_audit_snapshot_is_reproducible_and_portable(repo, tmp_path):
    ref = "src/m/a.c"
    report = _improved_report(repo, ref)
    snap = ta.build_improved_audit_snapshot(report, by_link=BY_LINK, campaign="test-campaign",
                                            repo_root=str(repo), tool_sig=TSIG)
    assert snap["kind"] == "t4_improved_audit" and snap["campaign"] == "test-campaign"
    assert snap["presets"] == ta.current_presets() and snap["base_flags"] == match.BASE_CFLAGS
    assert snap["summary"] == {"improved_total": 1, "improved_dependency_clean": 1,
                               "verified_fresh": 1}
    assert snap["records"][0]["source_digest"]
    text = json.dumps(snap)
    assert not any(p in text for p in ("/mnt/", "/home/", "/tmp/"))
    checkout_b = tmp_path / "checkout_b"
    shutil.copytree(repo, checkout_b)
    dig_a = snap["records"][0]["source_digest"]
    assert dig_a == ta.portable_source_digest(ref, repo_root=str(checkout_b))
    # the snapshot builder refuses an incomplete/dirty report instead of minting records
    bad = copy.deepcopy(report)
    bad["meta"]["git_dirty"] = True
    with pytest.raises(ValueError):
        ta.build_improved_audit_snapshot(bad, by_link=BY_LINK, repo_root=str(repo),
                                         tool_sig=TSIG)


# --- E7 provenance hardening (A4-A6) -------------------------------------------

def fake_checkout(root, war=b"war-v1", compiler=b"cc-v1", headers=True):
    """A checkout with `original/install/war.exe` and the 10.0a compiler tree."""
    (root / "original/install").mkdir(parents=True, exist_ok=True)
    (root / "original/install/war.exe").write_bytes(war)
    for sub in ("binnt", "binb"):
        d = root / f"original/watcom/10.0a/{sub}"
        d.mkdir(parents=True, exist_ok=True)
        (d / "wcc386.exe").write_bytes(compiler)
    if headers:
        h = root / "original/watcom/10.0a/h"
        h.mkdir(parents=True, exist_ok=True)
        (h / "sys.h").write_text("/* sys v1 */\n")
    return root


def test_compiler_root_honours_the_checkout_and_the_env_override(tmp_path, monkeypatch):
    monkeypatch.delenv("WC1_WATCOM10A", raising=False)
    from wc1 import oldcc
    root = tmp_path / "repo"
    assert ta.compiler_root(str(root)) == os.path.abspath(str(root / "original/watcom/10.0a"))
    assert ta._default_system_headers(str(root)) == root / "original/watcom/10.0a/h"
    assert ta.compiler_root() == oldcc.root()
    override = tmp_path / "explicit-cc"
    monkeypatch.setenv("WC1_WATCOM10A", str(override))
    assert ta.compiler_root(str(root)) == os.path.abspath(str(override))
    assert ta.compiler_root() == oldcc.root() == os.path.abspath(str(override))


def test_portable_source_digest_uses_only_the_checkouts_own_compiler_tree(tmp_path, monkeypatch):
    monkeypatch.delenv("WC1_WATCOM10A", raising=False)
    ref = "src/m/a.c"
    body = HDR + "#include <sys.h>\nint f(void) { return 0; }\n"
    main_orig = fake_checkout(tmp_path / "main") / "original"

    real = tmp_path / "real"
    (real / "src/m").mkdir(parents=True)
    (real / ref).write_text(body)
    shutil.copytree(main_orig, real / "original")

    link = tmp_path / "link"
    (link / "src/m").mkdir(parents=True)
    (link / ref).write_text(body)
    (link / "original").symlink_to(main_orig, target_is_directory=True)

    relocated = tmp_path / "relocated"
    (relocated / "src/m").mkdir(parents=True)
    (relocated / ref).write_text(body)
    shutil.copytree(real / "original", relocated / "original")

    dig_real = ta.portable_source_digest(ref, repo_root=str(real))
    assert dig_real
    assert ta.portable_source_digest(ref, repo_root=str(link)) == dig_real
    assert ta.portable_source_digest(ref, repo_root=str(relocated)) == dig_real

    bare = tmp_path / "bare"                   # no original/, the active checkout has headers
    (bare / "src/m").mkdir(parents=True)
    (bare / ref).write_text(body)
    assert ta.portable_source_digest(ref, repo_root=str(bare)) is None


@pytest.mark.parametrize("ref", [None, 5, "", "/etc/passwd", "../outside.c", "src/../m/a.c"])
def test_portable_source_digest_rejects_non_portable_refs(repo, ref):
    assert ta.portable_source_digest(ref, repo_root=str(repo)) is None


def test_tool_sig_is_rooted_at_the_checkout(tmp_path, monkeypatch):
    monkeypatch.delenv("WC1_WATCOM10A", raising=False)
    a = fake_checkout(tmp_path / "a")
    b = fake_checkout(tmp_path / "b")
    sig_a = ta._tool_sig(str(a))
    assert sig_a and ta._is_sha256_hex(sig_a)
    assert ta._tool_sig(str(b)) == sig_a
    (b / "original/install/war.exe").write_bytes(b"war-v2")
    assert ta._tool_sig(str(b)) != sig_a
    (b / "original/watcom/10.0a/binnt/wcc386.exe").write_bytes(b"cc-v2")
    assert ta._tool_sig(str(b)) != sig_a
    half = fake_checkout(tmp_path / "half")
    shutil.rmtree(half / "original/watcom")
    assert ta._tool_sig(str(half)) is None
    assert ta._tool_sig(str(tmp_path / "nowhere")) is None


def test_missing_live_toolchain_is_an_explicit_stale_reason(repo):
    rec = ta.improved_t4_records(_improved_report(repo), by_link=BY_LINK)[0]
    chk = ta.check_improved_record(rec, repo_root=str(repo), by_link=BY_LINK)
    assert chk["status"] == "stale" and chk["fresh"] is False
    assert "tool_sig: live toolchain identity unavailable" in chk["reasons"]


def test_build_improved_snapshot_requires_by_link_and_the_live_identity(repo):
    report = _improved_report(repo)
    for bad in (None, {}):
        with pytest.raises(ValueError):
            ta.build_improved_audit_snapshot(report, by_link=bad, repo_root=str(repo),
                                             tool_sig=TSIG)
    with pytest.raises(ValueError, match="live toolchain identity unavailable"):
        ta.build_improved_audit_snapshot(report, by_link=BY_LINK, repo_root=str(repo))
    with pytest.raises(ValueError, match="does not match the live toolchain identity"):
        ta.build_improved_audit_snapshot(report, by_link=BY_LINK, repo_root=str(repo),
                                         tool_sig="b" * 64)
    stale = copy.deepcopy(report)
    stale["results"][0]["source_digest"] = "b" * 64
    with pytest.raises(ValueError, match="stale/non-portable"):
        ta.build_improved_audit_snapshot(stale, by_link=BY_LINK, repo_root=str(repo),
                                         tool_sig=TSIG)
    outside = copy.deepcopy(report)
    outside["results"][0]["ref"] = "/etc/passwd.c"
    with pytest.raises(ValueError, match="stale/non-portable"):
        ta.build_improved_audit_snapshot(outside, by_link=BY_LINK, repo_root=str(repo),
                                         tool_sig=TSIG)


def test_check_improved_record_by_link_none_is_partial(repo):
    rec = ta.improved_t4_records(_improved_report(repo), by_link=BY_LINK)[0]
    for by_link in (None, ["A_"]):
        chk = ta.check_improved_record(rec, repo_root=str(repo), tool_sig=TSIG,
                                       by_link=by_link)
        assert chk == {"status": "partial", "fresh": False, "reasons": [],
                       "unchecked": ["symbols"]}


def test_record_minted_without_symbol_addresses_is_malformed(repo):
    rec = ta.improved_t4_records(_improved_report(repo))[0]       # by_link=None
    assert set(rec["symbols"].values()) == {None}
    chk = ta.check_improved_record(rec, repo_root=str(repo), tool_sig=TSIG, by_link=BY_LINK)
    assert chk["status"] == "malformed" and chk["fresh"] is False
    assert any("symbols" in r for r in chk["reasons"])


@pytest.mark.parametrize("field, value", [
    ("schema", 2),
    ("git_commit", None),
    ("git_commit", "zz"),
    ("compiler", None),
    ("manifest_sha256", "x"),
    ("source_digest", "x"),
    ("omf_deps_sha256", "x"),
    ("tool_sig", "x"),
    ("presets", []),
    ("presets", [""]),
    ("base_flags", 1),
    ("declared_cflags", None),
    ("link_name", ""),
    ("link_name", "Gone_"),
    ("ref", "<absolute>"),
    ("ref", 5),
    ("symbols", {}),
    ("symbols", ["x"]),
])
def test_check_improved_record_malformed_fields_never_raise(repo, field, value):
    rec = ta.improved_t4_records(_improved_report(repo), by_link=BY_LINK)[0]
    if value == "<absolute>":
        value = str(repo / "src/m/a.c")
    bad = dict(rec, **{field: value})
    chk = ta.check_improved_record(bad, repo_root=str(repo), tool_sig=TSIG, by_link=BY_LINK)
    assert chk["status"] == "malformed" and chk["fresh"] is False and chk["reasons"]


def test_check_improved_record_missing_symbols_is_malformed(repo):
    rec = ta.improved_t4_records(_improved_report(repo), by_link=BY_LINK)[0]
    bad = {k: v for k, v in rec.items() if k != "symbols"}
    chk = ta.check_improved_record(bad, repo_root=str(repo), tool_sig=TSIG, by_link=BY_LINK)
    assert chk["status"] == "malformed" and any("symbols" in r for r in chk["reasons"])


def test_check_improved_record_lists_every_stale_dimension(repo):
    ref = "src/m/a.c"
    rec = ta.improved_t4_records(_improved_report(repo), by_link=BY_LINK)[0]
    rec = dict(rec, base_flags="-x")
    (repo / ref).write_text(
        "/* codegen-compiler: 10.0a */\n/* codegen-flags: -s -ot -ol -4r -zp2 */\n"
        "int f(void) { return 1; }\n")
    chk = ta.check_improved_record(rec, repo_root=str(repo), tool_sig="b" * 64,
                                   current_presets=["-s -ot -ol -4r -zp2"],
                                   by_link={"Helper_": {"addr": 0x900},
                                            "A_": {"addr": 0x999}},
                                   omf_deps={})
    assert chk["status"] == "stale" and chk["fresh"] is False
    cats = {r.split(":", 1)[0] for r in chk["reasons"]}
    assert cats == {"presets", "base_flags", "source_digest", "tool_sig",
                    "declared_cflags", "omf_deps", "symbols"}
    assert any("A_" in r for r in chk["reasons"] if r.startswith("symbols:"))


def test_omf_deps_digest_fails_closed_and_keeps_the_legacy_digest():
    valid = {"complete": True, "external_symbols": ["Helper_"], "text_symbols": ["A_"],
             "external_relocs": [{"symbol": "Helper_", "self_relative": True,
                                  "loc": 9, "addend": 0}],
             "has_data_anchors": False}
    legacy = hashlib.sha256(json.dumps(
        {k: valid.get(k) for k in ("complete", "external_symbols", "text_symbols",
                                   "external_relocs", "has_data_anchors")},
        sort_keys=True).encode()).hexdigest()
    assert ta._omf_deps_digest(valid) == legacy
    for bad in ({}, dict(valid, complete=False), dict(valid, complete="yes"),
                {k: v for k, v in valid.items() if k != "text_symbols"},
                {k: v for k, v in valid.items() if k != "has_data_anchors"},
                dict(valid, text_symbols=[]), dict(valid, external_symbols="Helper_"),
                dict(valid, external_symbols={"Helper_"}), dict(valid, text_symbols=b"A_"),
                dict(valid, external_relocs={"x"}), dict(valid, has_data_anchors=0),
                {"text_symbols": {1, 2}}):
        assert ta._omf_deps_digest(bad) is None


def test_improved_t4_records_never_raises_on_malformed_omf_deps(repo):
    report = _improved_report(repo)
    report["results"][0]["omf_deps"] = {"complete": True, "external_symbols": {1, 2},
                                        "text_symbols": b"A_", "external_relocs": "x"}
    recs = ta.improved_t4_records(report, by_link=BY_LINK)
    assert recs and recs[0]["omf_deps_sha256"] is None
    report["results"][0]["omf_deps"] = None
    assert ta.improved_t4_records(report, by_link=BY_LINK)


def test_check_improved_snapshot_counts_reasons_and_header_disagreement(repo):
    snap = ta.build_improved_audit_snapshot(_improved_report(repo), by_link=BY_LINK,
                                            repo_root=str(repo), tool_sig=TSIG,
                                            campaign="c")
    ok = ta.check_improved_snapshot(snap, by_link=BY_LINK, repo_root=str(repo), tool_sig=TSIG)
    assert ok["snapshot"] == {"schema": 1, "campaign": "c", "git_commit": GIT_COMMIT,
                              "records": 1}
    assert ok["counts"] == {"total": 1, "fresh": 1, "stale": 0, "partial": 0, "malformed": 0}
    assert ok["reason_counts"] == {} and ok["snapshot_problems"] == []
    assert ok["live"] == {"tool_sig": TSIG, "presets": ta.current_presets(),
                          "base_flags": match.BASE_CFLAGS}

    stale = copy.deepcopy(snap["records"][0])
    stale.update(addr=0x200, addr_hex="0x200", source_digest="b" * 64)
    two = copy.deepcopy(snap)
    two["records"] = [snap["records"][0], stale]
    res = ta.check_improved_snapshot(two, by_link=BY_LINK, repo_root=str(repo), tool_sig=TSIG)
    assert res["counts"] == {"total": 2, "fresh": 1, "stale": 1,
                             "partial": 0, "malformed": 0}
    assert res["reason_counts"] == {"source_digest": 1}
    assert [r["addr_hex"] for r in res["records"]] == ["0x100", "0x200"]
    text = json.dumps(res)
    assert str(repo) not in text and "/tmp/" not in text and "/mnt/" not in text

    hdr = copy.deepcopy(two)
    hdr["records"][0]["presets"] = ["-x"]
    hrs = ta.check_improved_snapshot(hdr, by_link=BY_LINK, repo_root=str(repo), tool_sig=TSIG)
    assert hrs["counts"]["malformed"] == 1
    assert hrs["reason_counts"].get("malformed") == 1
    assert "presets" in hrs["records"][0]["reasons"][0]

    dirty = copy.deepcopy(snap)
    dirty["git_dirty"] = True
    drs = ta.check_improved_snapshot(dirty, by_link=BY_LINK, repo_root=str(repo), tool_sig=TSIG)
    assert drs["snapshot_problems"] and drs["counts"]["fresh"] == 1


def test_check_improved_cli_exit_codes(repo, tmp_path, monkeypatch, capsys):
    snap = ta.build_improved_audit_snapshot(_improved_report(repo), by_link=BY_LINK,
                                            repo_root=str(repo), tool_sig=TSIG)
    fn = tmp_path / "snapshot.json"
    fn.write_text(json.dumps(snap))
    monkeypatch.setattr(ta, "_tool_sig", lambda repo_root=None: TSIG)
    monkeypatch.setattr(ta.symbols, "load", lambda *a, **k: (
        {"A_": {"link_name": "A_", "addr": 0x100},
         "Helper_": {"link_name": "Helper_", "addr": 0x900}}, {}, []))
    assert ta.main(["--check-improved", str(fn)]) == 0
    out = json.loads(capsys.readouterr().out)
    assert out["counts"] == {"total": 1, "fresh": 1, "stale": 0, "partial": 0, "malformed": 0}

    bad = copy.deepcopy(snap)
    bad["records"][0]["source_digest"] = "b" * 64
    fn.write_text(json.dumps(bad))
    assert ta.main(["--check-improved", str(fn)]) == 1
    assert json.loads(capsys.readouterr().out)["counts"]["stale"] == 1

    broken = copy.deepcopy(snap)
    broken["git_dirty"] = True
    fn.write_text(json.dumps(broken))
    assert ta.main(["--check-improved", str(fn)]) == 1
    assert json.loads(capsys.readouterr().out)["snapshot_problems"]

    assert ta.main(["--check-improved", str(tmp_path / "missing.json")]) == 1
    assert "[CHECK IMPROVED ERROR]" in capsys.readouterr().err
