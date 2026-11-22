# Audio: Miles AIL 3.x and the game sound layer

Evidence and per-symbol detail live in `analysis/symbols/audio.toml`
(`python3 -m wc1.symbols`); checks in `tests/test_audio_ail.py`.

## Summary

* war.exe statically links **Miles Design's Audio Interface Library 3.x** in
  protected-mode form (code `0x34d83..0x3aac0`, ~6 KB of strings/data
  elsewhere). Drivers are loaded from disk at run time: `drivers\*.dig`
  (digital sound, 7 files) and `drivers\*.mdi` (XMIDI/MIDI, 10 files). The
  driver image is copied to DOS memory and called through **INT 66h** with the
  DPMI "simulate real-mode interrupt" service (`AIL_call_driver` 0x38afa).
* AIL functions use the **C calling convention** (stack arguments, caller pops
  with `add esp,N`). Only the game layer above it (0x263c0..0x27670) is Watcom
  code: the OD objects (`0x26b18..0x27661`) look like *unoptimised* Watcom
  output (callee-saved registers pushed, `ebp` frame, `sub esp,N` with N==0 for
  void functions, short jumps).  OW2 `-od` produces the same shape but with a
  4-byte larger frame, a return-value copy and near jumps, so OW2 cannot
  reproduce these bytes; **Watcom 10.0a can** - 16 of the module's functions are
  now T3 (see "Game sound layer: reconstruction status"), the rest are
  reference C with a T4 difftest.  `src/audio/sound.c` is kept only as the
  codegen-study sample `wc1.codegen_refs` sweeps (its three functions are now
  T3 in their own files).
* The sound **data** (VOC/WAV sound effects, XMIDI music) comes from the
  resource archive; the audio layer only calls the resource loader (callers
  listed below, not named here).

## AIL address ranges (for the modules area)

| Sub-module | Code range | Notes |
|---|---|---|
| core (driver registry, preferences, startup/shutdown) | `0x34d83..0x352ea` | locked with `fn_303a8(0x34d83, 0x352ea)`; `0x352ea` is a lone `ret` (lock end marker) |
| MDI / XMIDI sequencer | `0x352f0..0x38450` | locked pair `(0x352f0, 0x38450)`; `0x38450` one-instruction marker |
| timer services (PIT/INT 8) | `0x38454..0x38e21` | locked pair; ISR at `0x3846e` |
| DIG (digital sample mixer API) | `0x38e50..0x3a580` | locked pair `(0x38e50, 0x3a580)` |
| VOC/WAV file samples | `0x3a5c0..0x3aaab` | locked pair; jump table `cd_3a61c` (0x3a61c) is in this range |

AIL code as a whole: **[0x34d83, 0x3aac0)**. The next function (`0x3aac0`,
a routine with 6 stack-computed arguments calling `fn_400e4`, no audio references) is not AIL. Everything below
`0x34d83` that precedes it (0x34ad0, 0x34c70, ...) has non-AIL callers.

AIL data: strings `0x57f58..0x58345` (error messages, driver magic, IFF/VOC/WAV
tags), initialised data `0x55834..0x55a78` (timer tables, GTL prefix),
`0x56478..0x56508` (ISR private stack and DIG lock block), BSS `0x62960..0x62d6c`
(driver table, preferences, error buffer, descriptors, DIG scratch).

Locking: AIL locks its own code/data with the DPMI "lock linear region" helper
`fn_303a8(start,end)` / `fn_30436(addr,len)` (`mov [esp],0x600`) because the
timer ISR touches them at interrupt time. The *game* layer does the same with
`fn_312f0(addr,len)` for its callbacks (`0x2753c..0x2764c`) and for loaded
sound data; those helpers belong to the clib/DOS-extender area.

### Entry points that discovery did not split (change request)

These are real functions inside "padding-merged" ranges; `wc1.analysis` gave
them no start, so they cannot be named in the symbol DB yet:

| Address | Proposed name | Evidence |
|---|---|---|
| `0x3865c` | (now named `ail_timer_startup`) | |
| `0x3a082` | `AIL_install_DIG_driver_image` | twin of `0x373b0` for DIG |
| `0x3a0c0` | `AIL_uninstall_DIG_driver` | loads `[drv]`, calls AIL_release_driver_handle |
| `0x3a290/0x3a2b0/0x3a2e0/0x3a2f0` | `AIL_sample_playback_rate`, `AIL_sample_volume`, `AIL_sample_pan`, `AIL_set_sample_pan` | read/write `+0x34/+0x38/+0x3c` |
| `0x3a310/0x3a330/0x3a350` | `AIL_sample_position`, `AIL_set_sample_position`, `AIL_sample_loop_count` | `+0x18[cur]`, `+0x28` |
| `0x3a400/0x3a420` | `AIL_stop_sample`, `AIL_resume_sample` | status 4->8 and 8->4 |
| `0x3a490/0x3a4b0` | `AIL_register_EOB_callback`, `AIL_register_EOS_callback` | swap `+0x840` / `+0x844` |
| `0x3a4f0/0x3a510/0x3a530` | `AIL_set_sample_user_data`, `AIL_sample_user_data`, `AIL_load_sample_buffer` | `+0x84c+4*i`, buffers `+8/+0x10` |
| `0x37b60/0x37b80/0x37b90` | `AIL_sequence_loop_count`, ?, `AIL_sequence_volume` | getters on `+0x28`, `+0x44`, `+0x34` |
| `0x37ba0/0x37cde/0x37d20` | MIDI helpers using driver functions `0x504/0x505` | |
| `0x37d60/0x37dc0/0x37e00/0x37e70` | `AIL_active_sequence_count`, `AIL_channel_notes`, `AIL_sequence_position`, `AIL_branch_index` | |

Some of these (`0x3a370`, `0x37d90`) are already named because discovery did
split them.

## Driver files and configuration

`CONFIG.WAR` (0x20 bytes, loaded by `0x1d4c0` into `0x59900` after a
`memset(0xff)`; written by SETUP.EXE) holds, as 16-bit words:

| Address | Field |
|---|---|
| `0x59902` | digital driver index (0xffff = none), `< 7` |
| `0x59904..0x5990a` | digital IO port, IRQ, DMA, second DMA (IO block passed to AIL; port 0 = autodetect) |
| `0x59912` | music driver index (0xffff = none), `< 10` |
| `0x59914..0x5991a` | music IO port, IRQ, DMA, fourth value |

Digital drivers (table `0x533b8`): sblaster, sbpro, sb16, proaudio, ultra,
jammer, rap10 (`.dig`). Music drivers (table `0x533d4`): adlib, adlibg,
sblaster, sbpro1, sbpro2, sbawe32, pas, pasplus, mpu401, ultra (`.mdi`). All
are relative to the executable directory (`_makepath(exe_dir, ...)`). The
general-timbre-library prefix `drivers\warcraft` (0x5341c) is passed to
`AIL_set_GTL_filename_prefix` (files not shipped with the CD image examined, so
the extension is not observed).

`PREFS.WAR` (0x14 bytes, `0x1d574`) fills `0x532b4..0x532c8`; `0x532b8` is
the music volume percent and `0x532bc` the effects volume percent
(`-1` = not set; defaults 78 % / device dependent).

## Game sound layer

Code range `0x26320..0x27670`, two modules: **SND.C** (`0x26320..0x269f0`, the
Insider's Guide name, 15 functions: OPT wrappers, `src/codegen/snd.c`, plus the
DBG-style `SndInit`) and **mod_269f0** (`0x269f0..0x27670`, 23 functions,
candidate `GAMESND.C` - `drivers\warcraft` is only referenced from it).  From
`0x26b18` on the code is "OD" (`-s -od -4r -zp2`, short jumps, `sub esp,0`
frames); `AilInit` at `0x269f0` has the same OD shape.

Initialisation (`SndInit` 0x263c0, called once from the program init 0x1da34):

1. default volumes, `AilInit(sfx*127/100, music*127/100)` (0x269f0): AIL_startup,
   GTL prefix, preferences `7=0` (mono), `1=0x2b11` (11025 Hz), `8=0` (8-bit),
   `4=4`, `5=sfx volume`, `0xc=music volume`, lock callback range.
2. digital driver -> `SndInstallDigital` (0x26f1c) -> `AIL_install_DIG_driver_file`;
   four channel slots `snd_channels` (`0x5a220`, {HSAMPLE,data}).
3. music driver -> 30000-byte buffer (`0x5a210`) -> `SndInstallMidi` (0x26b3c)
   -> `AIL_install_MDI_driver_file` + one `AIL_allocate_sequence_handle`.
4. Failure messages: `Digitized sound card not found.` / `Music card not found.`
   + `Run 'SETUP.EXE' to reconfigure your sound card settings`, then exit(1).
   `SndShutdown` (0x26654) is registered with the atexit helper.

Sound effects:

* `SndLoadTable(ids)` (0x267fc) loads a 0-terminated list of resource ids into
  `snd_data_ptrs` (`0x532c8`)/`snd_data_sizes` (`0x5a120`), locking each block
  (bit 15 of an id = alias of an earlier identical id). 16 callers (screen and
  level transitions) pass static lists (`0x51758`, `0x517b0`, `0x517b6`,
  `0x517c2`, `0x52580`, `0x52c6c`, `0x5535a`, ...).
* `SndPlay(id)` (0x26958, 11 callers), `SndPlayLooped(id)` (0x26988, caller
  0x189db), `SndStop(id)` (0x269b8, caller 0x2fbc5). All three do nothing
  when there is no digital driver or the effects volume is 0.
* `SndPlayData(voc)` (0x26fd4): `AIL_allocate_file_sample(hdig, voc, -1)`
  (VOC "Creative" or RIFF WAVE image), pick a free one of 4 channel slots (if
  none: evict round-robin with `AIL_end_sample`), install the end hook
  `SndSampleEndedCallback` (0x27554) via `ail_set_file_sample_end_hook`, start.
  File samples release themselves at the end of data (`ail_file_sample_done`).
* Volumes: `SndSetSfxVolume(0..127)` (0x27384, pref 5 + all active samples),
  `SndToggleSfx` (0x266e4, mutes and releases channels), `SndApplyOptions`
  (0x2674c, percent -> 0..127).

Music:

* `MusicStart(track)` (0x26784, 7 callers): loads resource
  `mdi_music_res_base[mdi_idx] - 2 + track` (`0x533fc`: 0x11 for the FM
  drivers, 0x20 for SB/PAS MIDI, 2 for MPU-401/Ultra...) into the buffer,
  `MusicSetData` + `MusicPlayTrack(0)`; same track again is a no-op.
  Observed track numbers: 0xc, 0xd (0x188b4), 0xe (level load 0x23ae0),
  0xf (0x1c300), 0x10 (0x162b0), 0 (0x19998, 0x2fcfc). `MusicClear` 0x267e0
  stops and forgets.
* `SndSetMusicVolume` (0x27460: pref 0xc + `AIL_set_sequence_volume`; 0 stops
  the track, going up from 0 restarts it), `SndToggleMusic` (0x26684),
  `SndFadeOut(ms)` / `SndFadeOutAndStopAll(ms)` (volume ramp to 0, then a
  one-shot AIL timer calls `MusicFadeTimerCallback` 0x275a8 which ends the
  sequence; the second variant also releases every sample; caller 0x19ad0).

### Game-layer state (addresses in audio.toml)

| Address | Symbol | Meaning |
|---|---|---|
| 0x53414 | `snd_dig_active` | digital driver installed (guards every SFX path) |
| 0x53415 | `snd_mdi_active` | MIDI driver installed (guards every music path) |
| 0x53418 | `snd_fade_timer` | AIL timer handle of the fade callback, init -1 |
| 0x5341c | `gtl_prefix_name` | `drivers\warcraft` + NUL (17 bytes) |
| 0x5342e | `snd_evict_next` | round-robin eviction counter, 4 digital channels |
| 0x53430 | `snd_evict_next_looped` | same for `SndPlayDataLooped` |
| 0x5a220 | `snd_channels[4]` | digital channels, 8 bytes `{HSAMPLE hsample; void *data;}` |
| 0x5a240 | `snd_hdig` | AIL digital driver handle |
| 0x5a244 | `snd_music_data` | XMIDI image pointer set by `MusicSetData` |
| 0x5a248 | `snd_hmdi` | AIL MIDI driver handle |
| 0x5a24c | `snd_sequences[1]` | `{void *hseq; short state;}` (stride 6; state 0xffff = invalid) |
| 0x5a252 | `snd_sfx_volume127` | effects volume 0..127 (percent volumes live at 0x532b8/0x532bc) |
| 0x5a254 | `snd_music_volume127` | music volume 0..127 |
| 0x5a256 | `snd_fade_stop_all` | the fade timer also releases every sample |

## Game sound layer: reconstruction status (mod_269f0)

Built from C (T3, `python3 -m wc1.match src/audio/<file>` MATCH, one function
per file because the neighbours are reference C).  `src =` entries are added by
the session owner, not by the area analyst:

| Address | Function | File | Notes |
|---|---|---|---|
| 0x26b18 | SndShutdownAil | snd_shutdown_ail.c | wired earlier (verified) |
| 0x26c10 | MusicSetData | music_set_data.c | `snd_sequences[0].state = 0xffff` |
| 0x26c70 | MusicIsPlaying | music_is_playing.c | two return paths (`-4` slot, `-8` temp) |
| 0x26cc8 | MusicPlayTrack | music_play_track.c | int parameter used as `(short)` |
| 0x26d60 | MusicStop | music_stop.c | volatile handle read |
| 0x26d98 | SndFadeOut | snd_fade_out.c | `(unsigned short)ms`, non-volatile timer |
| 0x26e3c | SndFadeOutAndStopAll | snd_fade_out_stop_all.c | loop index is also the volume |
| 0x271f4 | SndReleaseAll | snd_release_all.c | volatile loop index |
| 0x27320 | SndActiveCount | snd_active_count.c | |
| 0x27360 | SndGetSfxVolume | snd_get_sfx_volume.c | `short` return type matters |
| 0x27384 | SndSetSfxVolume | snd_set_sfx_volume.c | dword view of the volume word |
| 0x2743c | SndGetMusicVolume | snd_get_music_volume.c | |
| 0x27460 | SndSetMusicVolume | snd_set_music_volume.c | restart/stop on the 0 crossing |
| 0x2753c | SndLockStart | snd_lock_start.c | empty, DPMI range marker |
| 0x275a8 | MusicFadeTimerCallback | music_fade_timer.c | **cdecl**, volatile handle read |
| 0x2764c | SndLockEnd | snd_lock_end.c | empty, DPMI range marker |
| 0x269f0 | AilInit | ail_init.c | `-d1+` (header flags): without it 10.0a swaps the return slot (-4) and the parameters (-8/-0xc) |

Reference C with a T4 difftest (`tests/test_audio_snd.py`, AIL stubbed):

| Address | Function | File | T3 blocker |
|---|---|---|---|
| 0x26b3c | SndInstallMidi | snd_install_midi_reference.c | frame slots (the original's return slot is at -4, 10.0a swaps it with the parameters; the IO block and loop already match) |
| 0x26f1c | SndInstallDigital | snd_install_digital_reference.c | same |
| 0x26fd4 | SndPlayData | snd_play_data_reference.c | `lea edx,[eax*8+base]` (original) vs `shl` + displacement (10.0a) |
| 0x270dc | SndPlayDataLooped | snd_play_data_looped_reference.c | same |
| 0x27278 | SndStopData | snd_stop_data_reference.c | same |
| 0x27554 | SndSampleEndedCallback | snd_sample_ended_reference.c | same; **cdecl** (see below) |

What the bytes of this module teach about the source (each point is *needed*
for the matches above, so it is evidence, not style):

* **Volatile state.** `snd_sequences[0].hseq` is read as
  `mov eax,[0x5a24c]; push eax` (0x26d82, 0x26c2a, 0x26d3e, 0x275ca) - a
  volatile lvalue; a plain struct member compiles to `push dword [...]`.
  `AilInit` DPMI-locks exactly that state (`snd_dig_active`, `snd_mdi_active`,
  `snd_fade_stop_all`, `snd_sequences[1]` 6 bytes, `snd_channels` 0x20 bytes,
  `snd_fade_timer`) because the AIL timer callbacks run at interrupt time.
  The *loop* accesses of the same array are plain pushes
  (`push dword [eax+0x5a24c]`, 0x26e95, 0x27605), so those files declare the
  array non-volatile and cast (audio.h `struct snd_seq` / `struct snd_seq_v`).
  `snd_fade_timer` and `snd_hdig` are *not* volatile (`push dword [0x53418]`,
  `push dword [0x5a240]`).
* **Word variables with a dword view.** Several 16-bit values are read as the
  high half of a dword (`mov eax,[A-2]; sar eax,0x10`): `snd_sfx_volume127`
  (0x5a252, reads at 0x273ab/0x273d4/0x27411) and the two round-robin counters
  `snd_evict_next` (0x5342e, read at 0x27056) and `snd_evict_next_looped`
  (0x53430, read at 0x2715e) - the same idiom the save/score area documents for
  `game_mode` (0x59616).  Writes stay plain word stores (`mov word [...],ax`,
  `inc word [...]`), so the source had both views; the C spells the read as
  `*(int *)((char *)&sym - 2) >> 16` (or `*(int *)&snd_evict_next >> 16` for
  the looped counter, whose dword starts at the *other* counter).
* **cdecl callbacks.** `SndSampleEndedCallback` and `MusicFadeTimerCallback`
  have Watcom's cdecl prologue (`push esi; push edi; push ebp`) and the sample
  hook reads its argument at `[ebp+0x10]`, i.e. from the stack - AIL calls it
  as `push esi; call [hsample+0x86c]; add esp,4` (0x3a604).  Their link names
  are `_SndSampleEndedCallback` / `_MusicFadeTimerCallback`, not the `name_`
  form the rest of the layer uses.
* **Volatile loop counters.** Every loop index in the module is incremented as
  `mov eax,[ebp-4]; inc dword [ebp-4]` - the value-preserving form - so the
  locals are `volatile short`; a plain `short` gives a bare `inc dword [...]+`
  and shifts every jump target (2-3 bytes per function).
* **Argument promotions.** `MusicPlayTrack`'s track and the fade durations are
  int parameters *used* as `(short)`/`(unsigned short)` (the original promotes
  with `movsx eax, word [...]` or `xor eax,eax; mov ax, word [...]`); the
  `SndInstall*` arguments are `unsigned short` in the prototype (word compares,
  `ret 4` for the fifth argument).
* **The two module-local blocks.** `SndInstallMidi/Digital` build a 24-byte IO
  block on the stack and pass it to `AIL_install_MDI/DIG_driver_file`; AIL's
  `ail_mdi_default_io` (0x36b40) reads four 16-bit values then four longs and
  copies 6 dwords into the driver description (`+0x16`).  The game only sets
  the four words - the rest of the block is whatever the stack held.

`drivers\warcraft` (0x5341c, 17 bytes with the NUL) is `AilInit`'s GTL prefix:
`_makepath(path, NULL, exe_dir, gtl_prefix_name, NULL)` then
`AIL_set_GTL_filename_prefix(path)`.

## AIL internals worth knowing

* Handles: driver descriptor 0x28 bytes (16 slots at `0x62960`; type word `+0x10`
  0=DIG, 1=MDI from the image magic `AIL3DIG`/`AIL3MDI`); DIG context 0x88 with
  0x88c-byte sample structures (`+0x5c` array, `+0x60` count; fields: status
  `+4` 1/2/4/8 = free/done/playing/stopped, buffers `+8..`, loop `+0x28`, rate
  `+0x34`, volume `+0x38`, pan `+0x3c`, callbacks `+0x840..+0x848`, file hooks
  `+0x86c..+0x880`); MDI context 0x1d0 with 0x6d4-byte sequence structures
  (`+0x18` array, `+0x1c` count).
* Driver call codes seen: 0x300 init, 0x301 detect (fills description),
  0x302 service, 0x303 describe, 0x305/0x306 (open/close), 0x401/0x402 start/stop
  DMA, 0x405, 0x502..0x505 MIDI queue/timbre/channel. Names are tentative.
* Timer module: 15 usable slots (`0x558d0`..), status 0/1/2, shared 8253 PIT
  programming (`ail_set_pit_divisor`), ISR `0x3846e` on IRQ 0 with private stack.
  The DIG mixer (`ail_dig_timer_service` 0x39210) and the sequencer
  (`ail_mdi_timer_service` 0x36410) are timer callbacks; the game's fade timer is a third.
* Errors: every failure copies a message into `ail_last_error` (0x629b8) and
  returns NULL/0; the game never reads it.

## Open questions

* Exact meaning of driver call codes and the 24-byte IO/description blocks.
  The game's `SndInstall*` IO block only initialises the first four words
  (`io, irq, dma, drq`); AIL then reads 24 bytes from it, i.e. the remaining
  bytes are uninitialised stack - kept as-is (the reference C declares a
  24-byte struct that is only partly written).
* Why Watcom 10.0a orders the frame slots differently in four functions
  (`AilInit` 0x269f0, `SndInstallMidi` 0x26b3c, `SndInstallDigital` 0x26f1c
  return-value slot/parameter order).  The original puts the return slot at
  -4; every source spelling tried (short/int parameters, short/long/unsigned
  returns, K&R definitions, nested scopes, `register`, every `-o` flag,
  `-zW/-zw/-4s/-zp*`) keeps 10.0a's order.  Same class of difference as the
  `lea edx,[eax*8]` channel addressing in `SndPlayData`/`SndStopData` (the
  original folds the array base into a `lea`, 10.0a uses `shl` plus a
  displacement).
* The two AIL callbacks are cdecl, so their link names are
  `_SndSampleEndedCallback` / `_MusicFadeTimerCallback` while `build/war.asm`
  labels them `SndSampleEndedCallback_` / `MusicFadeTimerCallback_`.  A
  `#pragma aux ... "name_"` cannot be used: it replaces the calling convention
  too and the prologue becomes the six-register watcall one (first difference
  at +0x0), so the match is lost.  Every asm reference to those two labels is
  inside functions this area also builds from C (`SndFadeOut`,
  `SndFadeOutAndStopAll`, `SndPlayData`, `SndPlayDataLooped`), so once those
  are wired in the labels are unreferenced - the build owner should place the
  cdecl names (see the report's change requests).
* `ail_midi_event` (0x35b50) and the mixer internals (0x39210/0x39400) are only
  characterised, not reconstructed.
* ANALYST_GUIDE says `0x635e4..0x64180` is an interrupt handler's private
  stack; the AIL timer ISR switches to `dat_56478`, not to that region. Which
  handler owns `0x635e4` is not an audio question (probably the input/video area).
* What `0x3aac0` is (first non-AIL function, only skimmed) belongs to another area.
