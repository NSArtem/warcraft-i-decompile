# Warcraft: Orcs & Humans (DOS, CD v1.22h) reconstruction.
# Run inside `nix develop`. The original files are never committed: put the
# Redump/DIC dump CD_DIC.rar in the repo root and run `make extract`.

PY      := python3
ORIG    := original/install/war.exe
EXE     := build/war.exe

.PHONY: help extract analyze roundtrip build verify run symbols test match-all clean

help:
	@echo "make extract    CD_DIC.rar -> original/ (hash-verified)"
	@echo "make roundtrip  prove the generated asm reassembles to the identical image"
	@echo "make build      asm + reconstructed C -> $(EXE) (wlink, DOS/4GW)"
	@echo "make verify     symbols check + roundtrip + per-function C matches + tests"
	@echo "make run        boot $(EXE) headless in DOSBox-X, take screenshots"
	@echo "make symbols    validate analysis/symbols/*.toml"

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
	@set -e; for f in src/*.c; do echo "== $$f"; $(PY) -m wc1.match $$f; done

test: $(ORIG)
	$(PY) -m pytest -q tests

verify: symbols roundtrip match-all build test

run: build
	$(PY) -m wc1.run $(EXE) --at 10,20

clean:
	rm -rf build
