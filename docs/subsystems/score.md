# SCORE.C (0x24e50..0x25820) - score accounting and score panel

Header: `src/include/save_score.h`. Source dir: `src/score/`.

## Functions

| Addr | Name | Status |
|---|---|---|
| 0x25428 | ScorePageMen | T3 byte-match (`score_page_men.c`) |
| 0x2553c | ScorePageHarvest | T3 byte-match (`score_page_harvest.c`) |
| 0x25600 | ScorePageScore | T3 byte-match (`score_page_score.c`) |
| 0x25684 | ScoreUpdate | reference C, T4 difftest |
| 0x25718 | ScoreInit | reference C, T4 difftest |

## Data layouts

- `score_page_fns[4]` is a table of dwords. Each entry is a page callback `short fn(short page_changed)`. The page callbacks are 0x25428, 0x2553c and 0x25600.
- `score_page` and `score_page_shown` are words.
- `dat_5abb0` (0x5abb0) and `dat_5abc2` (0x5abc2) are words. ScoreUpdate sets them to (0,1) when page is 0, and to (1,0) otherwise.
- `score_panel_rect` and `dirty_x1` are 12-byte rects (3 dwords). ScoreUpdate saves `dirty_x1`, replaces it with the panel rect, calls `ScreenUpdate`, then restores it.
- `score_cap_tbl[12]` and `score_rate_tbl[12]` are word tables. ScoreInit indexes them with `i = (scenario_number - 0x77) / 2`, and `i` is clamped to 11 if it is outside 0..11.
- ScoreInit also sets `score_pool` to 0x9c4. It calls `LayerAdd(&score_panel_bm, &score_panel_rect, 0x10, scenario_race + 0xe6, BitmapBlit)` and `BitmapCloneAlloc(&score_panel_clean, &score_panel_bm)`.

## Why the reference files do not byte-match

`dat_5abb0` and `dat_5abc2` have no symbol-DB name, and `fn_1eba0` is a placeholder. The reference C therefore links to a different address. The first differing instruction is at 0x256c8 for ScoreUpdate and at 0x2572b for ScoreInit. The instruction streams are otherwise identical.

## Tests (`tests/test_score.py`)

- T3: the three page functions must still match.
- Near-miss guard: both reference files must still fail to match.
- T4: `run_spec` compares the compiled reference against the original code. Callees are stubbed and their call logs are compared.
  - ScoreUpdate stubs the page callbacks and `ScreenUpdate`.
  - ScoreInit stubs `fn_1eba0`, `LayerAdd` (5 arguments, 4 bytes popped) and `BitmapCloneAlloc`. It covers `scenario_number` from below range to above range.
- Buffers are allocated only in `init_emu`.
