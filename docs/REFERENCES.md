# External references

## [R1] Warcraft: Orcs & Humans Insider's Guide (The Warcraft Collective)

<https://blizzardarchive.com/pub/Misc/INSIDE.PDF>, sha256
`25a1bd31004095b916610f5b1168e2e6d5c741024d42d80e3a3d05b90ad7ee47`, 70 pages.
Local copy (not committed): `original/refs/INSIDE.PDF`.

Appendix II (pp. 35–36) lists the original C source file names "as generated
by the compiler due to the `__FILE__` macro". These strings are **not present
in war.exe v1.22h** (no `.C` strings at all), so they come from another build;
treat them as names that existed, not as proof of which code they contain.

Main sources: `BULLET.C CMD.C COLLIDE.C DISPATCH.C DLG_SET.C DLGS.C EVENT.C
GAME_EVT.C GAMEDATA.C GAMEDLG.C GAMESND.C GROUP.C HARVEST.C INIT.C maphdr.c
NETWORK.C ORDER.C PACKET.C PANE.C PATH.C PLACEBOX.C PLAYFLIC.C REMOTE.C SAVE.C
SCORE.C SELECT.C SND.C SPELL.C STATUS.C STRAT.C TEXTBOX.C TRAVERSE.C UNIT.C
USEL.C`

Graphics subroutines (`..\src\`): `BMPCOPRE.C BMPCLE.C BMPCOP.C BMPDRABU.C
BMPHFMRE.C BMPMAS.C BMPMASRE.C BMPTIT.C DFLDEC.C DFLDECBI.C DFLDECCU.C
DFLDECFN.C DFLDIS.C DFLOPE.C DFLREG.C EVTGET.C EVTPRO.C FNTPUTS.C FNTSTRLE.C
GRP2BMPX.C GRPTOBMP.C IMGUPD.C LZSDEC.C MNUBUTBL.C MNUBUTSE.C UNCDEC.C
VIDCOPRE.C VIDSETFA.C VIDSETPA.C VIDTRANS.C`

The guide also states: the case of `maphdr.c` is as found; game maps are built
from an assembler file; `GRP2BMPX.C`/`GRPTOBMP.C` are command-line dev tools,
not game code. The rest of the guide (unit statistics, spell mechanics, AI
behaviour, "program cycles" timing) is behavioural reference material for T5
tests.

Observed consistency with war.exe strings (supporting, not proof):
`EVT*` ↔ `evt lock`/`evt unlock`; `VID*` ↔ `VGA required`, `vidinicy:1`;
`DFL*` (FLIC) ↔ `PLAYFLIC.C`, `flic overrun`; `LZSDEC` ↔ compressed `.WAR`
entries.

## [R2] Module names embedded in sibling executables

`war_edit.exe` (bundled editor) and `setup.exe` carry `__FILE__` strings of a
shared UI library: war_edit — `CHECKSUM.C CHOOSE.C COMPLETE.C ERROR.C FSTR.C
GRAPH.C HELP.C KEYS.C MENU.C MMGR.C RIP.C SPREAD.C WIN.C`; setup — `ERROR.C
GRAPHX.C KEYS.C MENU.C OTHER.C WIN.C`. Whether any of this library is linked
into war.exe is an open question.

## [R3] Toolchain identification

war.exe embeds `WATCOM C/C++32 Run-Time system. (c) Copyright by WATCOM
International Corp. 1988-1994` and a 1988-1993 clib notice; DOS/4GW 1.97 is
the extender. Game code compiled with Open Watcom 2 `wcc386 -s -ot` has
matched byte-for-byte (see `src/init.c`).

## [R4] Audio Interface Library

Strings `AIL3DIG`, `AIL3MDI`, `Invalid driver type`, `.DIG driver required`
and the `DRIVERS\*.DIG/*.MDI` files identify Miles Design's Audio Interface
Library v3 (statically linked).
