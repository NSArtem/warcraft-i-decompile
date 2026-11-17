# Warcraft: Orcs & Humans (DOS, CD v1.22h) reconstruction.
# Run inside `nix develop`. The original files are never committed: put the
# Redump/DIC dump CD_DIC.rar in the repo root and run `make extract`.

PY      := python3
ORIG    := original/install/war.exe
EXE     := build/war.exe

.PHONY: help extract analyze roundtrip build verify run symbols test match-all progress goal clean

help:
	@echo "make extract    CD_DIC.rar -> original/ (hash-verified)"
	@echo "make roundtrip  prove the generated asm reassembles to the identical image"
	@echo "make build      asm + reconstructed C -> $(EXE) (wlink, DOS/4GW)"
	@echo "make verify     symbols check + roundtrip + per-function C matches + tests"
	@echo "make run        boot $(EXE) headless in DOSBox-X, take screenshots"
	@echo "make symbols    validate analysis/symbols/*.toml"
	@echo "make progress   progress towards docs/GOAL.md (wc1.progress; --check fails until done)"
	@echo "make goal       all gates of docs/GOAL.md section 4; passes only when the project is done"

extract: $(ORIG)
$(ORIG):
	tools/bootstrap.sh

analyze: $(ORIG)
	$(PY) -m wc1.analysis

roundtrip: $(ORIG)
	$(PY) -m wc1.roundtrip

build: $(ORIG)
	$(PY) -m wc1.build --out $(EXE)

symbols:
	$(PY) -m wc1.symbols

# Every C file must match its original functions exactly.
match-all: $(ORIG)
	@set -e; for f in $$(ls src/*.c; $(PY) -m wc1.symbols --srcs) ; do echo "$$f"; done | sort -u | \
	  while read f; do echo "== $$f"; $(PY) -m wc1.match $$f; done

test: $(ORIG)
	$(PY) -m pytest -q tests

verify: symbols roundtrip match-all build test

progress: $(ORIG)
	$(PY) -m wc1.progress --todo 20

# The project goal (docs/GOAL.md section 4). Runs every gate and reports each.
goal: $(ORIG)
	@g1=PASS; g2=PASS; g3=FAIL; \
	$(PY) -m wc1.progress --check || g1=FAIL; \
	$(MAKE) --no-print-directory verify || g2=FAIL; \
	echo; echo "gate 1 (every in-scope function done, wc1.progress --check): $$g1"; \
	echo "gate 2 (make verify green):                                 $$g2"; \
	echo "gate 3 (all-C build passes T5): $$g3 - not defined yet, docs/GOAL.md M3"; \
	[ $$g1 = PASS ] && [ $$g2 = PASS ] && [ $$g3 = PASS ]

run: build
	$(PY) -m wc1.run $(EXE) --at 10,20

clean:
	rm -rf build
