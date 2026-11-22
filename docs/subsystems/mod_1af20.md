# mod_1af20: map setup and game-screen input

This module covers map-buffer lifetime, map centering and target orders, input restoration, and the in-game chat editor. The table gives disassembly evidence for the five reference implementations covered here.

| Function | Entry | Evidence |
| --- | --- | --- |
| `MapFindStartTile` | `0x1b12c` | `0x1b13b` sets a 200-record scan; `0x1b142–0x1b167` checks status, owner, and preferred types; `0x1b180–0x1b18e` writes signed coordinates only when a unit was selected. |
| `MapInitBuffers` | `0x1b198` | `0x1b1af–0x1b1b9` installs default mouse handlers; `0x1b1d1–0x1b27a` allocates buffers; `0x1b348–0x1b418` selects save restore or fresh-map initialization; `0x1b433` returns the stream cursor. |
| `GameScreenRestoreInput` | `0x1b43c` | `0x1b43c–0x1b443` calls `0x25b80` with zero, then tail-jumps to `GameScreenInputInit` at `0x1a328`. |
| `GameScreenScheduleInputRestore` | `0x1b560` | `0x1b560–0x1b565` calls the same helper with one; `0x1b56a` stores `0x1b43c` in the status-frame callback at `0x59414`. |
| `GameScreenHandleChatKey` | `0x1b690` | Called by `GameHotkeyDispatch` (`0x19fd8`); `0x1b724–0x1b74d` dispatches submitted text as cheat flags or network chat; `0x1b7ab–0x1b7d2` terminates the edit buffer and builds the `msg: ` prompt. |

## Data layouts and branch behavior

- **Units:** `unit_array` (`0x59640`) points to 200 records of stride `0x5c` (`0x1b136–0x1b13b`, `0x1b173–0x1b17a`). Eligibility requires `(word[+0x10] & 0x0207) == 0` and byte `+0x1e` equal to zero. The first eligible type `0x28` or `0x29` wins; otherwise the first eligible record wins. The signed coordinate words are at `+0x0a` and `+0x0c`, extracted with dword loads and arithmetic shifts at `0x1b180–0x1b18e`. No eligible record leaves both outputs untouched.
- **Map state:** `0x1b1db–0x1b244` stores the map and terrain pointers at `0x58570–0x5858c`. Tile, flag, and fog maps each occupy `0x2000` bytes, and the object map and fog-cell table each occupy `0x4000`. `0x1b309–0x1b33f` initializes the packed viewport state at `0x5ac1c–0x5ac2d`. Restore reads tile, flags, object map, then fog, relocating the object entries before the final read (`0x1b34c–0x1b39b`). Fresh setup clears object map and fog, halves the scroll words, and obscures fog only outside demo mode (`0x1b3da–0x1b418`). Both paths pass signed scroll coordinates at `0x1b41d–0x1b42e`.
- **Chat state:** The word at `0x59650` is zero when inactive; when editing it counts the visible text including the trailing underscore in the buffer at `0x59652` (`0x1b69b`, `0x1b6d7–0x1b6e3`). The event scan code is at `+8`, the character at `+0x0a`, and the insertion gate at `+0x0b`. `0x1b756–0x1b7a3` handles Backspace and permits insertion for character bytes `0x20–0x7f` when the gate is zero and the length is below 30. The indexed stores based at `0x59651` replace the character at `chat_input_text[len - 1]`; they do not update the length word. Enter either opens the editor or submits and clears it.

## T3 and T4

The T3 guard covers `GameScreenCancelOrPlace`, `MapCenterOnTile`, `MapCenterOnUnit`, `MapFreeBuffers`, and `MapIssueTargetOrder`. A separate guard requires the five reference files to remain non-matches: the scan differs in branch layout, the init and restore routines differ at the call to `0x25b80`, and the chat editor differs in register allocation and the folded zero test at `0x1b6a2–0x1b6a4`.

T4 compares the five reference implementations against the executable. The fixtures cover scan precedence and bounds, both fresh-map modes and save restore, callback installation and dispatch order, and chat editing and submission. Stubs compare callee arguments and order; stack-backed chat arguments are compared by contents. The tests do not establish correctness inside stubbed callees. These checks were not run during generation.
