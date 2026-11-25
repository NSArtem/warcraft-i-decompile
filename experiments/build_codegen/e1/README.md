# E1: shared epilogues

Run inside the already configured development shell, from the repository root:

```sh
python3 -m experiments.build_codegen.e1.run_e1
pytest -q experiments/build_codegen/e1/test_e1.py
```

The runner compiles every matrix row from scratch with Watcom 10.0a, invokes
E0's strengthened matcher on the unmodified OMF, then attempts an isolated
Build A placement/link for every RegionMatch. Sources, objects, ASM remainder
pieces, link scripts and executables are disposable `build/e1/` artifacts.
The two primary successful links are `build/e1/war_group_a.exe` and
`build/e1/war_group_b.exe`. All other output goes to the permitted E1 results
folder (`--output` can select an alternative results directory).

Every row records the five R1 outcomes independently, including full E0
findings/obligations, raw branch bytes and actual sibling targets. An owner
function normally has `shared_epilogue_reproduced=false`: the bool measures
its outgoing branches, not branches received from other functions. Unattempted
integration has `identical=null` and a reason; attempted placement/assembly
rejections have `identical=false`. Failed exact matches never enter linking.

The four required flag sets are supplemented by `-ot -oa -ol -5r`, which
combines the successful body scheduling and layout controls for Group A.
Common flags are `-q -zl -zld -bt=dos`; 10.0a normalizes `-q` to `-zq`.
`-zld` suppresses dependency timestamp COMENT records, allowing actual,
unmodified OMF SHA-256 hashes to reproduce. It does not patch OMF bytes.
Absolute source paths remain in THEADR, so byte-for-byte object-hash replay
uses the assigned worktree path. A relocation of the checkout changes these
metadata hashes, not necessarily generated code or verdicts.

Fixtures `group_a_current.c` and `group_b_current.c` preserve the supplied
function bodies verbatim. `group_a_interleaved.c` is the primary readable C
revision: stage each coordinate load/add and use one conjunction of the four
inside-rectangle conditions. Other Group A fixtures preserve the bounded
spelling search: combining conditions, staging coordinate loads, introducing
an index or layer pointer, interleaving axes, reversing axis evaluation,
changing declaration order, using a common failure label, and renaming locals.
They are all retained, including unsuccessful and code-identical candidates.
Only the primary revision gets the full flag/order/standalone matrix; the
other spelling probes use `-ot -ol -5r`.

The pytest session repeats the entire matrix and links. It also reopens all
unmodified objects and independently reruns E0, checks the original-body
fixtures, tests standalone/pair/reverse controls, validates the exact R6
branch arithmetic, and compares both saved artifacts byte-for-byte when
present. There are no production-file writes, ASM insertions, or production
verification-target invocations.
