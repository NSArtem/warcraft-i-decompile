#!/usr/bin/env bash
# Recreate original/ from the Redump/DIC dump archive CD_DIC.rar (not in git).
#   CD_DIC.rar -> data track (MODE1/2352) -> ISO9660 files -> LHA .EXA -> war.exe
# Every stage is checked against the hashes in analysis/provenance/.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
RAR="${1:-CD_DIC.rar}"
PROV=analysis/provenance

[ -f "$RAR" ] || { echo "missing $RAR (Warcraft CD v1.22h Redump/DIC dump)" >&2; exit 1; }

mkdir -p original/disc original/cd original/install
if ! (cd original/disc && grep 'Track 1' "$ROOT/$PROV/inputs.sha256" | sha256sum -c --quiet 2>/dev/null); then
  echo "extracting data track from $RAR"
  unar -q -f -o original/disc -D "$RAR" "WAR1 (Track 1).bin" WAR1.cue WAR1.dat "!submissionInfo.txt"
  (cd original/disc && grep 'Track 1' "$ROOT/$PROV/inputs.sha256" | sha256sum -c --quiet)
fi

echo "extracting ISO9660 filesystem"
python3 tools/extract_disc.py "original/disc/WAR1 (Track 1).bin" original/cd
(cd original/cd/files && sha256sum -c --quiet <(awk '{print $1"  "$3}' "$ROOT/$PROV/cd_files.sha256"))

echo "unpacking installer archives (lh5)"
(cd original/install && for f in WAR SETUP WAR_EDIT DOS4GW; do lha xqf "../cd/files/$f.EXA"; done)
(cd original/install && sha256sum -c --quiet "$ROOT/$PROV/installed.sha256")
echo "OK: original/install/war.exe verified"
