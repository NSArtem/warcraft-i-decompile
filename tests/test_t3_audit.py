"""wc1.t3_audit (no toolchain, no war.exe): the compiler, the comparison and
the buildability check are faked; the symbol database and the progress rows
are built in the test."""
import json
import os

import pytest

from wc1 import match, permuter, t3_audit as ta

HDR = "/* codegen-compiler: 10.0a */\n/* codegen-flags: -s -ot -oa -4r -zp2 */\n"
DECL = "-s -ot -oa -4r -zp2"


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
