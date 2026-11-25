"""Signal evaluation against independent CU-boundary ground truth.

Two polarities are reported separately, exactly as RFC §9.3 proposes:

* **split signals** — a *positive* prediction means "CU boundary here"
  (`zero16`, `zero4`, `zero2`, `none16`, `style_transition`,
  `const_window_break`, `data_bss_staircase_break`, `flag_set_S_disjoint`,
  `call_locality_drop`);
* **merge signals** — a *positive* prediction means "both functions belong to
  the same CU" (`non_16_aligned_start`, `shared_epilogue`,
  `shared_const_string_literal`, `exclusive_static_data_sharing`, plus the
  supplementary `call_locality_link`).

Every signal returns True, False or None; None means "not evaluable here"
(e.g. neither function references the string pool).  Those pairs are excluded
from that signal's sample and counted in `unavailable`, so `sample_size` is
the number of pairs the signal could actually speak about.

The zero-gap rules are *the production implementation* (`wc1.modules_scan`),
and the codegen style is *the production survey* (`wc1.codegen_survey.feat`),
so the numbers describe the signals the project actually uses.

Exploratory game analysis lives at the bottom: the same signals applied to the
game range of `war.exe`, where no independent boundary truth exists.  It is
never mixed into precision/recall.
"""
import bisect
from collections import Counter, defaultdict

from wc1 import codegen_survey, modules_scan

SPLIT = "split"
MERGE = "merge"
SIGNALS = [
    ("zero16", SPLIT), ("zero4", SPLIT), ("zero2", SPLIT), ("none16", SPLIT),
    ("style_transition", SPLIT), ("const_window_break", SPLIT),
    ("data_bss_staircase_break", SPLIT), ("flag_set_S_disjoint", SPLIT),
    ("call_locality_drop", SPLIT),
    ("non_16_aligned_start", MERGE), ("shared_epilogue", MERGE),
    ("shared_const_string_literal", MERGE), ("exclusive_static_data_sharing", MERGE),
    ("call_locality_link", MERGE),
    # supplementary merge readings of the monotonic windows (RFC §9.3 lists the
    # staircase/string window as merge evidence; the break is only the complement)
    ("const_window_continues", MERGE), ("data_staircase_continues", MERGE),
]
ROLE = dict(SIGNALS)

# The assumptions behind a "proven" reading of a signal.  Recorded with every
# metric so a constraint is never quoted without its premise.
PROVEN = {
    "shared_epilogue": ("Watcom 10.0a `wcc386` emits cross-function epilogue branches "
                        "inside one object and the 10.0a `wlink` performs no link-time "
                        "tail merging, so two functions sharing an epilogue branch are "
                        "in one CU (RFC §9.2 example; reproduced by E1)."),
    "non_16_aligned_start": ("a C object whose `_TEXT` SEGDEF requests paragraph (16-byte) "
                            "alignment cannot start a contribution at a non-16-aligned "
                            "address; the premise fails for byte/word/dword-aligned "
                            "objects (hand-written asm, `-os`/`-od` and `-5r`/`-3r` CUs) "
                            "and the corpus measures how often it fails."),
    "zero16": ("a zero gap of 1..15 bytes before a 16-aligned start is the linker's "
               "padding between whole object contributions; the premise is that no "
               "in-object data or zero fill happens to precede an aligned interior "
               "function (the corpus measures the exceptions)."),
}

EPILOGUE = {"pop", "ret", "retf", "leave", "nop"}


def _is_epilogue_insn(i):
    if i.mnemonic in EPILOGUE:
        return True
    if i.mnemonic in ("mov", "add", "sub") and i.op_str.replace(" ", "").startswith("esp,"):
        return True
    return False


def _epilogue_starts(insns, max_len=8):
    """Addresses from which the rest of the function is a short exit block.

    Watcom's shared epilogues are not just `pop; ret`: E1's original pair
    branches to `mov eax,edx; pop edx; ret`, and the 10.0a pattern in this
    corpus branches to `xor eax,eax; ret`.  An exit block is therefore the
    final run (<= `max_len` instructions) that ends in `ret`, contains no
    `call`, and contains no control flow -- value setup plus stack teardown.
    """
    if not insns or insns[-1].mnemonic not in ("ret", "retf"):
        return set()
    out = set()
    for k in range(len(insns) - 1, max(-1, len(insns) - 1 - max_len), -1):
        i = insns[k]
        if i.mnemonic in ("call", "jmp") or (i.mnemonic.startswith("j")
                                             and i.mnemonic not in ("jmp",)):
            break
        if i.mnemonic == "ret" or i.mnemonic == "retf":
            out.add(i.address)
            continue
        if i.mnemonic in ("pop", "leave", "nop"):
            out.add(i.address)
            continue
        if i.mnemonic in ("mov", "add", "sub", "xor", "or", "and", "lea", "inc", "dec",
                          "neg", "not", "movzx", "movsx", "cdq", "shl", "shr", "sar"):
            out.add(i.address)
            continue
        break
    return out


class View:
    """Per-function facts shared by all signals (one pass over the image)."""

    def __init__(self, prog, functions, ranges):
        self.p = prog
        self.functions = functions
        self.const = [tuple(r) for r in ranges.get("const", ())]
        self.data = [tuple(r) for r in ranges.get("data", ())]
        self.fix = sorted(prog.fix_at.items())
        self.fix_src = [a for a, _ in self.fix]
        self.insn_addrs = sorted(prog.insns)
        self.facts = [self._facts(f) for f in functions]
        by_ref = defaultdict(set)
        for k, fa in enumerate(self.facts):
            for t in fa["data_refs"]:
                by_ref[t].add(k)
        self.data_ref_functions = by_ref

    def _in(self, ranges, addr):
        for lo, hi in ranges:
            if lo <= addr < hi:
                return True
        return False

    def _insns(self, f):
        lo = bisect.bisect_left(self.insn_addrs, f["start"])
        hi = bisect.bisect_left(self.insn_addrs, f["body_end"])
        return [self.p.insns[a] for a in self.insn_addrs[lo:hi]]

    def _facts(self, f):
        lo = bisect.bisect_left(self.fix_src, f["start"])
        hi = bisect.bisect_left(self.fix_src, f["body_end"])
        data_refs = set()
        for a, (_fx, target) in self.fix[lo:hi]:
            data_refs.add(target)
        const_refs = {t for t in data_refs if self._in(self.const, t)}
        private = {t for t in data_refs if self._in(self.data, t)}
        insns = self._insns(f)
        callees = set()
        for i in insns:
            if i.mnemonic != "call" or not i.operands:
                continue
            if i.operands[0].type == 2:                     # X86_OP_IMM
                callees.add(i.operands[0].imm & 0xFFFFFFFF)
        style = codegen_survey.feat(self.p, {"start": f["start"], "end": f["body_end"],
                                             "limit": f["limit"]})["style"]
        return {"start": f["start"], "body_end": f["body_end"], "insns": insns,
                "data_refs": data_refs, "const_refs": const_refs, "private_refs": private,
                "callees": callees, "style": style,
                "epilogue": _epilogue_starts(insns)}

    # -- individual signals -------------------------------------------------
    def _cross_branch(self, a, b):
        """A branch from a into b's exit sequence (shared epilogue)."""
        targets = b["epilogue"]
        if not targets:
            return False
        for i in a["insns"]:
            if i.mnemonic != "jmp" and not i.mnemonic.startswith("j"):
                continue
            if i.mnemonic.startswith("call") or not i.operands:
                continue
            if i.operands[0].type != 2:
                continue
            if (i.operands[0].imm & 0xFFFFFFFF) in targets:
                return True
        return False

    def pair(self, i, sf=None):
        a, b = self.facts[i - 1], self.facts[i]
        gap, glen = modules_scan.gap_kind(self.p, a["body_end"], b["start"])
        rule = modules_scan.rule_of(b["start"], gap, glen)
        sig = {
            "zero16": rule == "zero16",
            "zero4": rule == "zero4",
            "zero2": rule == "zero2",
            "none16": rule == "none16",
            "style_transition": a["style"] != b["style"],
        }
        if a["const_refs"] and b["const_refs"]:
            sig["const_window_break"] = max(a["const_refs"]) > min(b["const_refs"])
            sig["const_window_continues"] = not sig["const_window_break"]
        else:
            sig["const_window_break"] = None
            sig["const_window_continues"] = None
        if a["private_refs"] and b["private_refs"]:
            sig["data_bss_staircase_break"] = min(b["private_refs"]) < max(a["private_refs"])
            sig["data_staircase_continues"] = not sig["data_bss_staircase_break"]
        else:
            sig["data_bss_staircase_break"] = None
            sig["data_staircase_continues"] = None
        sa = set((sf or {}).get(str(a["start"])) or ())
        sb = set((sf or {}).get(str(b["start"])) or ())
        sig["flag_set_S_disjoint"] = (not (sa & sb)) if sa and sb else None
        direct = (b["start"] in a["callees"]) or (a["start"] in b["callees"])
        linked = direct or bool(a["callees"] & b["callees"])
        sig["call_locality_drop"] = not linked
        sig["call_locality_link"] = linked
        sig["non_16_aligned_start"] = b["start"] % 16 != 0
        sig["shared_epilogue"] = self._cross_branch(a, b) or self._cross_branch(b, a)
        shared_const = a["const_refs"] & b["const_refs"]
        sig["shared_const_string_literal"] = bool(shared_const)
        shared_data = a["private_refs"] & b["private_refs"]
        sig["exclusive_static_data_sharing"] = any(
            self.data_ref_functions[t] == {i - 1, i} for t in shared_data)
        facts = {
            "prev": a["start"], "cur": b["start"], "gap": gap, "gap_len": glen,
            "rule": rule, "style_prev": a["style"], "style_cur": b["style"],
            "prev_cu": self.functions[i - 1].get("cu"),
            "cur_cu": self.functions[i].get("cu"),
            "prev_name": self.functions[i - 1].get("name"),
            "cur_name": self.functions[i].get("name"),
            "const_refs_prev": len(a["const_refs"]), "const_refs_cur": len(b["const_refs"]),
            "data_refs_prev": len(a["private_refs"]), "data_refs_cur": len(b["private_refs"]),
            "shared_const": len(shared_const),
            "shared_data_exclusive": sorted(t for t in shared_data
                                            if self.data_ref_functions[t] == {i - 1, i}),
            "call_prev_to_cur": b["start"] in a["callees"],
            "call_cur_to_prev": a["start"] in b["callees"],
            "S_prev": sorted(sa), "S_cur": sorted(sb),
        }
        return sig, facts


def evaluate(prog, corpus):
    """Confusion data for every labelled adjacent pair of one corpus."""
    view = View(prog, corpus["functions"], corpus["ranges"])
    sf = corpus.get("sf")
    rows = []
    for lab in corpus["labels"]:
        i = lab["i"]
        sig, facts = view.pair(i, sf)
        rows.append({"i": i, "truth": lab["truth"], "signals": sig, "facts": facts,
                     "evidence": lab.get("evidence")})
    return {"corpus": corpus["id"], "kind": corpus["kind"], "rows": rows}


def _confusion(rows, name, role):
    tp = fp = tn = fn = unavailable = 0
    for row in rows:
        v = row["signals"][name]
        if v is None:
            unavailable += 1
            continue
        positive = bool(v)
        same = row["truth"] == "same_cu"
        if role == SPLIT:
            tp += positive and not same
            fp += positive and same
            tn += not positive and same
            fn += not positive and not same
        else:
            tp += positive and same
            fp += positive and not same
            tn += not positive and not same
            fn += not positive and same
    sample = tp + fp + tn + fn
    has_same = any(r["truth"] == "same_cu" for r in rows)
    has_boundary = any(r["truth"] == "boundary" for r in rows)
    # A ratio needs the truth class it is computed over to have been sampled.
    precision_ok = has_same and has_boundary if role == MERGE else has_same
    recall_ok = has_boundary if role == SPLIT else has_same
    precision = tp / (tp + fp) if (tp + fp) and precision_ok else None
    recall = tp / (tp + fn) if (tp + fn) and recall_ok else None
    f1 = (2 * precision * recall / (precision + recall)
          if precision is not None and recall is not None and precision + recall else None)
    return {"signal": name, "role": role, "TP": tp, "FP": fp, "TN": tn, "FN": fn,
            "precision": precision, "recall": recall, "F1": f1,
            "precision_measurable": precision_ok, "recall_measurable": recall_ok,
            "sample_size": sample, "unavailable": unavailable}


def metrics(result):
    return [_confusion(result["rows"], name, role) for name, role in SIGNALS]


def examples(result, limit=3):
    """Concrete false positives and false negatives for every signal."""
    out = {}
    for name, role in SIGNALS:
        fps, fns = [], []
        for row in result["rows"]:
            v = row["signals"][name]
            if v is None:
                continue
            same = row["truth"] == "same_cu"
            wrong_positive = bool(v) and ((role == SPLIT and same) or (role == MERGE and not same))
            wrong_negative = (not v) and ((role == SPLIT and not same) or (role == MERGE and same))
            fact = dict(row["facts"], signals=row["signals"], evidence=row["evidence"])
            if wrong_positive and len(fps) < limit:
                fps.append(fact)
            if wrong_negative and len(fns) < limit:
                fns.append(fact)
        out[name] = {"false_positives": fps, "false_negatives": fns}
    return out


def classify(metric):
    """Epistemic label from the measured numbers (rubric documented in the report).

    Proven constraints are *not* derived from metrics: `PROVEN` states the
    assumption, and the report discusses it next to the measured failure modes.
    """
    p, tp = metric["precision"], metric["TP"]
    if metric["sample_size"] < 5 or p is None:
        return "unknown"
    if p >= 0.95 and tp >= 5:
        return "strong_evidence"
    if p >= 0.6:
        return "weak_ambiguous"
    return "unreliable_noisy"


# ---------------------------------------------------------------------------
# exploratory game analysis (never ground truth)
# ---------------------------------------------------------------------------
GAME_LO, GAME_HI = 0x104b0, 0x3024e


def game_analysis(prog, functions, modules, sf=None, ranges=None):
    """Apply the signals + E7 S(f) to the game range; label everything inferred."""
    ranges = ranges or {"const": [[0x569d0, 0x58440]], "data": [[0x50000, 0x569d0], [0x58440, 0x60000]]}
    inrange = [f for f in functions if GAME_LO <= f["start"] < GAME_HI]
    if len(inrange) < 2:
        return {"caveat": "no game-range functions", "chunks": []}
    view = View(prog, inrange, ranges)
    starts = [f["start"] for f in inrange]
    mod_start = sorted(modules)
    chunk_of = {}
    for f in inrange:
        k = bisect.bisect_right(mod_start, f["start"]) - 1
        chunk_of[f["start"]] = modules[mod_start[k]]["name"] if k >= 0 else "?"
    chunks = defaultdict(lambda: {"functions": 0, "pairs": 0, "rule_counts": Counter(),
                                   "padding": [], "all_candidates": 0})
    for k, f in enumerate(inrange):
        chunks[chunk_of[f["start"]]]["functions"] += 1
    fires = Counter()
    agree = Counter()
    candidates = []
    padding_rules = {"zero16", "zero4", "zero2", "none16", "data16"}
    for i in range(1, len(inrange)):
        a, b = inrange[i - 1], inrange[i]
        if not (GAME_LO <= b["start"] < GAME_HI):
            continue
        sig, facts = view.pair(i, sf)
        name = chunk_of[b["start"]]
        chunks[name]["pairs"] += 1
        chunks[name]["rule_counts"][facts["rule"] or "none"] += 1
        split_fires = [n for n, r in SIGNALS if r == SPLIT and sig[n] is True]
        merge_fires = [n for n, r in SIGNALS if r == MERGE and sig[n] is True]
        strong = [n for n in split_fires if n in ("zero16", "zero4", "zero2")]
        padding = [n for n in split_fires if n in padding_rules]
        # Merge evidence that is *independent of the alignment premise*.
        merge_strong = [n for n in merge_fires
                        if n in ("shared_epilogue", "shared_const_string_literal",
                                 "exclusive_static_data_sharing")]
        for n in split_fires:
            fires[n] += 1
        if sig["none16"]:
            kind = "hidden_none16_candidate"
        elif sig["zero16"]:
            kind = "zero16_aligned"
        elif padding:
            kind = "other_padding"
        elif sig["style_transition"]:
            kind = "style_only"
        elif merge_strong:
            kind = "merge_evidence_only"
        else:
            kind = "no_signal"
        if padding and merge_strong:
            agree["padding_vs_merge_conflict"] += 1
        elif padding and sig["style_transition"]:
            agree["padding_and_style_agree"] += 1
        elif padding:
            agree["padding_only"] += 1
        elif sig["style_transition"]:
            agree["style_only"] += 1
        elif merge_strong:
            agree["merge_evidence_only"] += 1
        else:
            agree["no_signal"] += 1
        if merge_fires:
            agree["non_16_aligned_merge_claim"] += 1
        if sig["flag_set_S_disjoint"]:
            agree["S_disjoint"] += 1
        cand = {
            "addr": b["start"], "prev": a["start"], "chunk": name,
            "prev_name": a.get("name"), "cur_name": b.get("name"),
            "kind": kind, "gap": facts["gap"], "gap_len": facts["gap_len"],
            "rule": facts["rule"], "styles": [facts["style_prev"], facts["style_cur"]],
            "split_signals": split_fires, "merge_signals": merge_fires,
            "flags_disjoint": sig["flag_set_S_disjoint"],
            "S_prev": facts["S_prev"], "S_cur": facts["S_cur"],
        }
        candidates.append(cand)
        if split_fires:
            chunks[name]["all_candidates"] += 1
        if padding or sig["style_transition"]:
            chunks[name]["padding"].append(cand)
    out_chunks = []
    for name in sorted(chunks, key=lambda n: (-len(chunks[n]["padding"]), n)):
        c = chunks[name]
        mod_start = next((s for s, m in modules.items() if m["name"] == name), None)
        row = {"chunk": name, "start": mod_start,
               "kind": modules[mod_start]["kind"] if mod_start is not None else None,
               "functions": c["functions"], "pairs": c["pairs"],
               "padding_candidates": len(c["padding"]),
               "all_signal_candidates": c["all_candidates"],
               "rule_counts": dict(sorted(c["rule_counts"].items())),
               "candidate_addrs": [x["addr"] for x in c["padding"][:40]]}
        if sf is not None:
            fs = [f for f in inrange if chunk_of[f["start"]] == name]
            sets = [set(sf.get(str(f["start"])) or ()) for f in fs]
            nonempty = [s for s in sets if s]
            row["functions_with_S"] = len(nonempty)
            row["S_intersection"] = sorted(set.intersection(*nonempty)) if nonempty else []
            support = Counter()
            for s in nonempty:
                for cid in s:
                    support[cid] += 1
            row["S_support"] = dict(sorted(support.items()))
        out_chunks.append(row)
    top = [c for c in candidates if c["kind"] != "no_signal"]
    highlighted = [c for c in out_chunks
                   if c.get("start") in (0x1f050,)
                   or any(c["chunk"].startswith(t) or t in c["chunk"]
                          for t in ("mod_13f60", "mod_16390", "mod_1f050", "STATUS.C",
                                    "mod_1eba0", "mod_104b0"))]
    return {
        "caveat": ("EXPLORATORY / INFERRED — no independent ground truth exists for these "
                   "addresses; nothing here enters the precision/recall tables."),
        "range": [GAME_LO, GAME_HI],
        "functions_in_range": len(inrange),
        "pairs": len(candidates),
        "signal_fires": dict(sorted(fires.items())),
        "agreement": dict(sorted(agree.items())),
        "chunks": out_chunks,
        "alignment_candidates": [c for c in candidates
                                 if c["rule"] in ("zero16", "zero4", "zero2", "none16", "data16")],
        "large_chunk_candidates": top[:300],
        "highlighted_chunks": highlighted,
        "candidate_none16_splits": [c for c in candidates
                                    if c["kind"] == "hidden_none16_candidate"],
    }
