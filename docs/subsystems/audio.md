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
  with `add esp,N`). Only the game layer above it (0x263c0..0x275d0) is Watcom
  register code, and that layer looks like *unoptimised* Watcom output (all six
  callee-saved registers pushed, `ebp` frame, `sub esp,N` with N==0 for void
  functions, short jumps). OW2 `-od` produces the same shape but with a 4-byte
  larger frame and near jumps, so `wc1.match` cannot reproduce these bytes; see
  `src/audio/sound.c` (non-matching reconstruction of three small functions).
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

## Game sound layer (all watcall)

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
* `ail_midi_event` (0x35b50) and the mixer internals (0x39210/0x39400) are only
  characterised, not reconstructed.
* ANALYST_GUIDE says `0x635e4..0x64180` is an interrupt handler's private
  stack; the AIL timer ISR switches to `dat_56478`, not to that region. Which
  handler owns `0x635e4` is not an audio question (probably the input/video area).
* What `0x3aac0` is (first non-AIL function, only skimmed) belongs to another area.
