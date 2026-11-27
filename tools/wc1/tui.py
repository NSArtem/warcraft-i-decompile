"""btop-style interactive Textual + Rich TUI dashboard & launcher for wc1.overnight.

Standalone attach/detach client reading atomic snapshots from `build/live/`:
  - `state.json`:          runner state, progress, active/completed workers, queue, commits
  - `rate_limits.json`:    live 5h / 7d Claude quota windows
  - `workers/<id>.jsonl`:  auto-updating thinking/text/tool/perm/match/verify/commit stream
  - `control.json`:        IPC commands (`pause`, `resume`, `wake`, `graceful_stop`, `kill`)

Detaching (`q`) exits ONLY the UI and never stops the background runner.

Usage:
    nix develop -c python3 -m wc1.tui              # attach to live/last runner
    nix develop -c python3 -m wc1.tui --launcher   # open interactive preset/flag launcher
    nix develop -c python3 -m wc1.overnight        # opens launcher when run on a TTY
"""
import argparse
from collections import OrderedDict
import datetime
import glob
import os
import subprocess
import sys
import threading
import time

from rich.text import Text
from textual import events
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Grid, Horizontal, Vertical, VerticalScroll
from textual.message import Message
from textual.screen import ModalScreen
from textual.widget import Widget
from textual.widgets import (
    Button,
    DataTable,
    Footer,
    Input,
    Label,
    RichLog,
    Select,
    Sparkline,
    Static,
    Switch,
)

from . import analysis, live, overnight, path, progress, symbols


# ---- Visual constants & presets ---------------------------------------------

STREAM_HISTORY_LIMIT = 1500
STREAM_RENDER_LIMIT = 800
STREAM_POLL_MAX_EVENTS = 1000
STREAM_MAX_LINES = 8000

HEATMAP_STYLES = {
    "active":    ("◆", "#d2a8ff", "active"),
    "failed":    ("✕", "#f85149", "failed"),
    "t3":        ("█", "#3fb950", "T3"),
    "t4":        ("■", "#39c5cf", "T4"),
    "ref":       ("▓", "#d29922", "ref"),
    "named":     ("▒", "#58a6ff", "named"),
    "untouched": ("░", "#3b4252", "todo"),
    "oos":       ("·", "#484f58", "oos"),
}

STATE_COLORS = {
    "RUNNING":    ("#3fb950", "bold #0d1117 on #3fb950"),
    "THINKING":   ("#d2a8ff", "bold #0d1117 on #d2a8ff"),
    "PERMUTING":  ("#58a6ff", "bold #0d1117 on #58a6ff"),
    "VERIFYING":  ("#39c5cf", "bold #0d1117 on #39c5cf"),
    "REPAIRING":  ("#d29922", "bold #0d1117 on #d29922"),
    "COMMITTING": ("#3fb950", "bold #0d1117 on #3fb950"),
    "SLEEPING":   ("#e3b341", "bold #0d1117 on #e3b341"),
    "PAUSED":     ("#f0883e", "bold #0d1117 on #f0883e"),
    "STOPPING":   ("#f85149", "bold #ffffff on #da3633"),
    "FAILED":     ("#f85149", "bold #ffffff on #f85149"),
    "KILLED":     ("#f85149", "bold #ffffff on #8b1a1a"),
    "DONE":       ("#3fb950", "bold #3fb950"),
    "DETACHED":   ("#8b949e", "bold #8b949e"),
}

PRESETS = OrderedDict([
    ("overnight_full", {
        "label": "Overnight Full (100%, auto-sleep)",
        "window_budget": 1.0,
        "window_capacity": 35.0,
        "max_modules": 0,
        "wave": "all",
        "chunk_size": 12,
        "module_budget": 1.10,
        "module_calls": 10,
        "repair_budget": 0.45,
        "skip": list(overnight.DEFAULT_SKIP),
        "only": [],
        "sleep_on_limit": True,
        "rate_limit_sleep": 900,
    }),
    ("safe_80", {
        "label": "Safe 80% Window (auto-sleep)",
        "window_budget": 0.8,
        "window_capacity": 35.0,
        "max_modules": 0,
        "wave": "all",
        "chunk_size": 12,
        "module_budget": 1.10,
        "module_calls": 10,
        "repair_budget": 0.45,
        "skip": list(overnight.DEFAULT_SKIP),
        "only": [],
        "sleep_on_limit": True,
        "rate_limit_sleep": 900,
    }),
    ("daytime_sprint", {
        "label": "Daytime Sprint (5 modules, no-sleep)",
        "window_budget": 0.8,
        "window_capacity": 35.0,
        "max_modules": 5,
        "wave": "all",
        "chunk_size": 12,
        "module_budget": 1.10,
        "module_calls": 10,
        "repair_budget": 0.45,
        "skip": list(overnight.DEFAULT_SKIP),
        "only": [],
        "sleep_on_limit": False,
        "rate_limit_sleep": 900,
    }),
    ("wave3_unnamed", {
        "label": "Wave 3 Unnamed Only (100%, auto-sleep)",
        "window_budget": 1.0,
        "window_capacity": 35.0,
        "max_modules": 0,
        "wave": "wave3",
        "chunk_size": 12,
        "module_budget": 1.10,
        "module_calls": 10,
        "repair_budget": 0.45,
        "skip": list(overnight.DEFAULT_SKIP),
        "only": [],
        "sleep_on_limit": True,
        "rate_limit_sleep": 900,
    }),
])


def preset_config(name):
    base = PRESETS.get(name) or PRESETS["overnight_full"]
    cfg = dict(base)
    cfg.pop("label", None)
    return cfg


def is_runner_alive(root=None):
    st = live.read_json(live.state_path(root=root), None)
    if not isinstance(st, dict):
        return False
    return live.pid_alive(st.get("pid"))


def spawn_runner(cfg, root=None):
    """Spawn detached `wc1.overnight --headless ...` in a new session (survives TUI quit)."""
    cli_args = overnight.build_cli_args(cfg)
    cmd = [sys.executable, "-m", "wc1.overnight", *cli_args]
    cwd = root or path()
    log_dir = os.path.join(cwd, "build")
    os.makedirs(log_dir, exist_ok=True)
    log_fh = open(os.path.join(log_dir, "overnight_spawn.log"), "ab")
    try:
        proc = subprocess.Popen(
            cmd,
            cwd=cwd,
            stdin=subprocess.DEVNULL,
            stdout=log_fh,
            stderr=subprocess.STDOUT,
            start_new_session=True,
            close_fds=True,
        )
    finally:
        log_fh.close()
    return proc


# ---- Pure data / formatting helpers (easily unit-tested) --------------------

def classify_heatmap_cell(row, active_addrs=(), failed_addrs=()):
    """Map one progress row to `(key, glyph, color, tier_label)`."""
    addr = row["addr"]
    if addr in active_addrs:
        k = "active"
    elif addr in failed_addrs:
        k = "failed"
    elif row.get("scope") != "in":
        k = "oos"
    elif row.get("c") == "T3":
        k = "t3"
    elif row.get("c") == "T4":
        k = "t4"
    elif row.get("c") == "ref":
        k = "ref"
    elif row.get("named"):
        k = "named"
    else:
        k = "untouched"
    glyph, color, label = HEATMAP_STYLES[k]
    return k, glyph, color, label


def build_module_cells(fn_cells, active_modules=(), failed_modules=()):
    """Aggregate function-level cells into module-level cells in address order."""
    by_mod = OrderedDict()
    for c in fn_cells:
        if c["scope"] != "in":
            continue
        m = c["module"]
        if m not in by_mod:
            by_mod[m] = {
                "module": m,
                "start_addr": c["addr"],
                "end_addr": c["addr"],
                "total": 0, "done": 0, "t3": 0, "t4": 0, "ref": 0, "named": 0,
            }
        agg = by_mod[m]
        agg["end_addr"] = max(agg["end_addr"], c["addr"])
        agg["total"] += 1
        if c["done"]:
            agg["done"] += 1
        if c["c"] == "T3":
            agg["t3"] += 1
        elif c["c"] == "T4":
            agg["t4"] += 1
        elif c["c"] == "ref":
            agg["ref"] += 1
        if c["named"]:
            agg["named"] += 1

    out = []
    for m, agg in by_mod.items():
        if m in active_modules:
            k = "active"
        elif m in failed_modules:
            k = "failed"
        elif agg["total"] > 0 and agg["t3"] == agg["total"]:
            k = "t3"
        elif agg["total"] > 0 and agg["done"] == agg["total"]:
            k = "t4"
        elif agg["ref"] > 0 or agg["done"] > 0:
            k = "ref"
        elif agg["named"] > 0:
            k = "named"
        else:
            k = "untouched"
        glyph, color, label = HEATMAP_STYLES[k]
        agg["key"] = k
        agg["glyph"] = glyph
        agg["color"] = color
        agg["tier"] = label
        out.append(agg)
    return out


def format_inspector(cell, mode):
    """Format the single-line inspector footer under the Heatmap."""
    if not cell:
        return "Hover or move cursor over a cell to inspect"
    if mode == "modules":
        pct = 100.0 * cell["done"] / max(1, cell["total"])
        return (
            f"{cell['module']}  {cell['done']}/{cell['total']} ({pct:.0f}%)  "
            f"T3={cell['t3']} T4={cell['t4']} ref={cell['ref']} named={cell['named']}  "
            f"{cell['start_addr']:#x}..{cell['end_addr']:#x}"
        )
    src = cell.get("src") or "-"
    return (
        f"{cell['addr']:#x}  {cell['name']}  [{cell['module']}]  "
        f"tier={cell['tier']}  src={src}"
    )


def filter_stream_event(ev, filter_mode):
    """Return True if an NDJSON worker event matches the active stream filter."""
    if not isinstance(ev, dict):
        return False
    if filter_mode == "all":
        return True
    k = str(ev.get("kind") or "info").lower()
    if filter_mode == "thinking":
        return k in ("think", "out", "tool")
    if filter_mode == "verify":
        return k in ("perm", "match", "verify", "commit", "error", "stage")
    return True


def _safe_float(val, default=None):
    if val is None:
        return default
    try:
        return float(val)
    except (TypeError, ValueError):
        return default


def format_duration(seconds):
    if seconds is None:
        return "—"
    s = max(0, int(seconds))
    h, rem = divmod(s, 3600)
    m, sec = divmod(rem, 60)
    if h > 0:
        return f"{h}h{m:02d}m"
    if m > 0:
        return f"{m}m{sec:02d}s"
    return f"{sec}s"


def render_bar(pct, width=22, cap_pct=None):
    """Build a crisp btop-style Rich progress bar with optional budget cap marker."""
    pct_clamped = max(0.0, min(100.0, float(pct or 0.0)))
    filled = int(round(width * pct_clamped / 100.0))
    cap_idx = None
    if cap_pct is not None and 0.0 < cap_pct < 100.0:
        cap_idx = max(0, min(width - 1, int(round(width * cap_pct / 100.0)) - 1))

    color = "#3fb950"
    if pct_clamped >= 90.0:
        color = "#f85149"
    elif pct_clamped >= 70.0:
        color = "#d29922"
    elif pct_clamped >= 45.0:
        color = "#58a6ff"

    t = Text()
    for i in range(width):
        if cap_idx is not None and i == cap_idx:
            t.append("┃", style="bold #f0883e")
        elif i < filled:
            t.append("━", style=f"bold {color}")
        else:
            t.append("─", style="#30363d")
    return t


# ---- Cached Heatmap Data Loader ---------------------------------------------

class HeatmapDataLoader:
    """Caches immutable war.exe analysis and reloads symbol TOMLs only on change."""

    def __init__(self):
        self._program = None
        self._mods = None
        self._last_sig = None
        self._rows_cache = []
        self._lock = threading.Lock()

    def _toml_signature(self):
        sym_dir = path("analysis", "symbols")
        if not os.path.isdir(sym_dir):
            return ()
        sig = []
        for f in sorted(glob.glob(os.path.join(sym_dir, "*.toml"))):
            try:
                st = os.stat(f)
                sig.append((f, st.st_mtime_ns, st.st_size))
            except OSError:
                pass
        return tuple(sig)

    def load_rows(self, force=False):
        with self._lock:
            if not os.path.exists(path("original", "install", "war.exe")):
                return []
            sig = self._toml_signature()
            if not force and self._rows_cache and sig == self._last_sig:
                return self._rows_cache
            if self._program is None:
                self._program = analysis.run()
                self._mods = progress.load_modules()
            funcs_db, _, _ = symbols.load(strict=False)
            rows = progress.classify([f["start"] for f in self._program.functions], funcs_db, self._mods)
            enriched = []
            for r in rows:
                e = funcs_db.get(r["addr"]) or {}
                enriched.append({
                    "addr": r["addr"],
                    "name": e.get("name") or f"fn_{r['addr']:05x}",
                    "module": r["module"],
                    "scope": r["scope"],
                    "named": r["named"],
                    "c": r["c"],
                    "done": r["done"],
                    "src": e.get("src") or e.get("ref") or "",
                })
            self._rows_cache = enriched
            self._last_sig = sig
            return enriched


# ---- Custom Heatmap Widget --------------------------------------------------

class HeatmapWidget(Widget):
    """Interactive btop-style function/module heatmap with keyboard & mouse inspector."""

    can_focus = True

    class CellSelected(Message):
        def __init__(self, cell, mode):
            super().__init__()
            self.cell = cell
            self.mode = mode

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.mode = "functions"  # "functions" | "modules"
        self.show_oos = False
        self.fn_rows = []
        self.active_addrs = set()
        self.failed_addrs = set()
        self.active_modules = set()
        self.failed_modules = set()
        self.cells = []
        self.cursor_idx = 0
        self._cols = 64

    def set_data(self, fn_rows, active_addrs=(), failed_addrs=(),
                 active_modules=(), failed_modules=()):
        self.fn_rows = list(fn_rows)
        self.active_addrs = set(active_addrs)
        self.failed_addrs = set(failed_addrs)
        self.active_modules = set(active_modules)
        self.failed_modules = set(failed_modules)
        self._rebuild_cells()
        self.refresh()

    def set_mode(self, mode):
        if mode != self.mode:
            self.mode = mode
            self.cursor_idx = 0
            self._rebuild_cells()
            self.refresh()
            self._emit_selected()

    def set_show_oos(self, show_oos):
        if show_oos != self.show_oos:
            self.show_oos = show_oos
            self._rebuild_cells()
            self.refresh()
            self._emit_selected()

    def _rebuild_cells(self):
        fn_cells = []
        for r in self.fn_rows:
            if not self.show_oos and r.get("scope") != "in":
                continue
            k, glyph, color, label = classify_heatmap_cell(r, self.active_addrs, self.failed_addrs)
            fn_cells.append({
                "addr": r["addr"],
                "name": r["name"],
                "module": r["module"],
                "scope": r["scope"],
                "named": r["named"],
                "c": r["c"],
                "done": r["done"],
                "src": r.get("src", ""),
                "key": k,
                "glyph": glyph,
                "color": color,
                "tier": label,
            })
        if self.mode == "modules":
            self.cells = build_module_cells(fn_cells, self.active_modules, self.failed_modules)
        else:
            self.cells = fn_cells
        if self.cells:
            self.cursor_idx = max(0, min(self.cursor_idx, len(self.cells) - 1))
        else:
            self.cursor_idx = 0

    def current_cell(self):
        if 0 <= self.cursor_idx < len(self.cells):
            return self.cells[self.cursor_idx]
        return None

    def _emit_selected(self):
        self.post_message(self.CellSelected(self.current_cell(), self.mode))

    def _stride(self):
        return 2 if self.mode == "modules" else 1

    def render(self):
        w = max(16, self.size.width)
        stride = self._stride()
        self._cols = max(8, w // stride)
        if not self.cells:
            return Text("No heatmap data available (needs original/install/war.exe)", style="#8b949e")

        out = Text()
        cols = self._cols
        max_rows = max(1, self.size.height)
        total_cells = len(self.cells)
        # Keep cursor row visible if terminal is very short
        cur_row = self.cursor_idx // cols
        start_row = max(0, cur_row - max_rows + 1) if cur_row >= max_rows else 0
        start_idx = start_row * cols
        end_idx = min(total_cells, start_idx + max_rows * cols)

        for idx in range(start_idx, end_idx):
            c = self.cells[idx]
            style = f"reverse bold {c['color']}" if idx == self.cursor_idx else c["color"]
            out.append(c["glyph"], style=style)
            if stride == 2:
                out.append(" ")
            if ((idx - start_idx + 1) % cols == 0) and (idx + 1 < end_idx):
                out.append("\n")
        return out

    def _index_at(self, x, y):
        stride = self._stride()
        col = x // stride
        if col < 0 or col >= self._cols or y < 0:
            return None
        max_rows = max(1, self.size.height)
        cur_row = self.cursor_idx // self._cols
        start_row = max(0, cur_row - max_rows + 1) if cur_row >= max_rows else 0
        idx = (start_row + y) * self._cols + col
        if 0 <= idx < len(self.cells):
            return idx
        return None

    def on_mouse_move(self, event: events.MouseMove):
        idx = self._index_at(event.x, event.y)
        if idx is not None and idx != self.cursor_idx:
            self.cursor_idx = idx
            self.refresh()
            self._emit_selected()

    def on_click(self, event: events.Click):
        self.focus()
        idx = self._index_at(event.x, event.y)
        if idx is not None:
            self.cursor_idx = idx
            self.refresh()
            self._emit_selected()

    def on_key(self, event: events.Key):
        if not self.cells:
            return
        delta = 0
        if event.key == "left":
            delta = -1
        elif event.key == "right":
            delta = 1
        elif event.key == "up":
            delta = -self._cols
        elif event.key == "down":
            delta = self._cols
        else:
            return
        event.stop()
        nxt = max(0, min(len(self.cells) - 1, self.cursor_idx + delta))
        if nxt != self.cursor_idx:
            self.cursor_idx = nxt
            self.refresh()
            self._emit_selected()


class StreamLog(RichLog):
    """RichLog that disables auto-follow on manual scroll up and resumes on End."""

    class ManualScrollUp(Message):
        pass

    class ResumeFollow(Message):
        pass

    def on_mouse_scroll_up(self, _event: events.MouseScrollUp):
        self.post_message(self.ManualScrollUp())

    def on_key(self, event: events.Key):
        if event.key in ("up", "pageup", "home", "ctrl+home"):
            self.post_message(self.ManualScrollUp())
        elif event.key in ("end", "ctrl+end"):
            self.post_message(self.ResumeFollow())


# ---- Modals: Kill Confirm, Recent Commits, Interactive Launcher -------------

class KillConfirmScreen(ModalScreen[bool]):
    """Confirmation dialog required before immediate process-tree kill."""

    BINDINGS = [
        Binding("escape", "cancel", "Cancel"),
        Binding("n", "cancel", "Cancel"),
        Binding("y", "confirm", "Kill Now"),
    ]

    DEFAULT_CSS = """
    KillConfirmScreen {
        align: center middle;
        background: rgba(13, 17, 23, 0.80);
    }
    #kill-dialog {
        width: 68;
        height: auto;
        border: heavy #f85149;
        background: #161b22;
        padding: 1 2;
    }
    #kill-title {
        color: #f85149;
        text-style: bold;
        margin-bottom: 1;
    }
    #kill-body {
        color: #c9d1d9;
        margin-bottom: 1;
    }
    #kill-buttons {
        height: 3;
        align: right middle;
    }
    #kill-buttons Button {
        margin-left: 2;
    }
    """

    def compose(self) -> ComposeResult:
        with Vertical(id="kill-dialog"):
            yield Static("⚠ IMMEDIATE KILL CONFIRMATION", id="kill-title")
            yield Static(
                "This will immediately terminate the active batch_driver / Claude child tree,\n"
                "archive and roll back ONLY the current module's changes, and preserve all\n"
                "pre-existing untracked WIP files.\n\n"
                "Use [x] Graceful Stop instead if you want to finish and commit the active module.",
                id="kill-body",
            )
            with Horizontal(id="kill-buttons"):
                yield Button("Cancel [Esc]", id="btn-kill-cancel", variant="default")
                yield Button("KILL NOW [y]", id="btn-kill-confirm", variant="error")

    def on_button_pressed(self, event: Button.Pressed):
        self.dismiss(event.button.id == "btn-kill-confirm")

    def action_cancel(self):
        self.dismiss(False)

    def action_confirm(self):
        self.dismiss(True)


class CommitsScreen(ModalScreen[None]):
    """Modal displaying recent commits landed by the current overnight run."""

    BINDINGS = [
        Binding("escape", "close", "Close"),
        Binding("q", "close", "Close"),
        Binding("g", "close", "Close"),
    ]

    DEFAULT_CSS = """
    CommitsScreen {
        align: center middle;
        background: rgba(13, 17, 23, 0.80);
    }
    #commits-dialog {
        width: 92;
        height: 24;
        border: heavy #58a6ff;
        background: #161b22;
        padding: 1 2;
    }
    #commits-title {
        color: #58a6ff;
        text-style: bold;
        margin-bottom: 1;
    }
    #commits-table {
        height: 1fr;
        margin-bottom: 1;
    }
    #commits-footer {
        height: 3;
        align: right middle;
    }
    """

    def __init__(self, commits, root=None):
        super().__init__()
        self._commits = list(commits or [])
        self._root = root

    def compose(self) -> ComposeResult:
        with Vertical(id="commits-dialog"):
            yield Static(f"Recent Run Commits ({len(self._commits)} in current run)", id="commits-title")
            yield DataTable(id="commits-table", cursor_type="row")
            with Horizontal(id="commits-footer"):
                yield Button("Close [Esc]", id="btn-commits-close", variant="primary")

    def on_mount(self):
        tbl = self.query_one("#commits-table", DataTable)
        tbl.add_columns("Rev", "Time", "Module", "Delta", "Cost", "Message")
        if self._commits:
            for c in reversed(self._commits):
                tbl.add_row(
                    str(c.get("rev", "")),
                    str(c.get("time", ""))[-8:],
                    str(c.get("module", "")),
                    f"+{int(c.get('delta') or 0)}",
                    f"${float(c.get('cost') or 0.0):.2f}",
                    str(c.get("message", "")),
                )
        else:
            # Fallback to recent repo git log
            added = 0
            try:
                r = subprocess.run(
                    ["git", "log", "-n", "12", "--pretty=format:%h\t%ad\t%s", "--date=format:%m-%d %H:%M"],
                    capture_output=True, text=True, cwd=self._root or path(), timeout=3,
                )
                for line in (r.stdout or "").splitlines():
                    parts = line.split("\t", 2)
                    if len(parts) == 3:
                        tbl.add_row(parts[0], parts[1], "(git log)", "", "", parts[2])
                        added += 1
            except Exception:
                pass
            if added == 0:
                tbl.add_row("-", "-", "-", "-", "-", "No commits recorded yet")

    def on_button_pressed(self, _event: Button.Pressed):
        self.dismiss(None)

    def action_close(self):
        self.dismiss(None)


class LauncherScreen(ModalScreen[dict | None]):
    """Interactive preset + flag launcher for starting `wc1.overnight` via `wc1.tui`."""

    BINDINGS = [
        Binding("escape", "attach_only", "Attach Only"),
    ]

    DEFAULT_CSS = """
    LauncherScreen {
        align: center middle;
        background: rgba(13, 17, 23, 0.85);
    }
    #launcher-box {
        width: 96;
        height: 32;
        border: heavy #39c5cf;
        background: #161b22;
        padding: 1 2;
    }
    #launcher-title {
        color: #39c5cf;
        text-style: bold;
        margin-bottom: 1;
    }
    #preset-row {
        height: 3;
        margin-bottom: 1;
    }
    #preset-row Button {
        margin-right: 1;
    }
    #form-grid {
        grid-size: 4;
        grid-gutter: 0 2;
        height: auto;
        margin-bottom: 1;
    }
    #form-grid Label {
        color: #8b949e;
        padding-top: 1;
    }
    #form-grid Input, #form-grid Select {
        height: 3;
    }
    #launcher-preview {
        color: #58a6ff;
        background: #0d1117;
        padding: 0 1;
        height: 3;
        margin-bottom: 1;
        border: solid #30363d;
    }
    #launcher-error {
        color: #f85149;
        height: 1;
    }
    #launcher-actions {
        height: 3;
        align: right middle;
    }
    #launcher-actions Button {
        margin-left: 1;
    }
    """

    def __init__(self, initial_config=None, runner_alive=False):
        super().__init__()
        base = preset_config("overnight_full")
        if initial_config:
            base.update({k: v for k, v in initial_config.items() if v is not None})
        self._cfg = base
        self._runner_alive = runner_alive

    def compose(self) -> ComposeResult:
        skip_s = ",".join(self._cfg.get("skip") or ()) if isinstance(self._cfg.get("skip"), (list, tuple)) else str(self._cfg.get("skip") or "")
        only_s = ",".join(self._cfg.get("only") or ()) if isinstance(self._cfg.get("only"), (list, tuple)) else str(self._cfg.get("only") or "")
        title = "⚔ wc1.overnight Interactive Launcher"
        if self._runner_alive:
            title += "  (active runner detected — you can Attach Only)"
        with Vertical(id="launcher-box"):
            yield Static(title, id="launcher-title")
            with Horizontal(id="preset-row"):
                yield Button("Overnight 100%", id="preset-overnight_full", variant="success")
                yield Button("Safe 80%", id="preset-safe_80", variant="primary")
                yield Button("Daytime Sprint (5)", id="preset-daytime_sprint", variant="default")
                yield Button("Wave 3 Only", id="preset-wave3_unnamed", variant="default")
            with VerticalScroll():
                with Grid(id="form-grid"):
                    yield Label("Window Budget (0..1)")
                    yield Input(str(self._cfg.get("window_budget", 1.0)), id="inp-window_budget")
                    yield Label("Max Modules (0=all)")
                    yield Input(str(self._cfg.get("max_modules", 0)), id="inp-max_modules")

                    yield Label("Backlog Wave")
                    yield Select(
                        [("All (Wave2 -> Wave3)", "all"), ("Wave 2 (c-only)", "wave2"), ("Wave 3 (full)", "wave3"),
                         ("Wave 4 (4A reconcile -> 4B codegen)", "wave4"),
                         ("Wave 4A (Symbol reconciliation)", "wave4a"),
                         ("Wave 4B (Codegen recovery)", "wave4b")],
                        value=str(self._cfg.get("wave", "all")),
                        id="sel-wave",
                    )
                    yield Label("Chunk Size (fn)")
                    yield Input(str(self._cfg.get("chunk_size", 12)), id="inp-chunk_size")

                    yield Label("Module Budget ($)")
                    yield Input(str(self._cfg.get("module_budget", 1.10)), id="inp-module_budget")
                    yield Label("Module Max Calls")
                    yield Input(str(self._cfg.get("module_calls", 10)), id="inp-module_calls")

                    yield Label("Repair Budget ($)")
                    yield Input(str(self._cfg.get("repair_budget", 0.45)), id="inp-repair_budget")
                    yield Label("Sleep on Limit")
                    yield Switch(value=bool(self._cfg.get("sleep_on_limit", True)), id="sw-sleep_on_limit")

                    yield Label("Skip Modules")
                    yield Input(skip_s, id="inp-skip")
                    yield Label("Only Modules (opt)")
                    yield Input(only_s, id="inp-only")

            yield Static("", id="launcher-preview")
            yield Static("", id="launcher-error")
            with Horizontal(id="launcher-actions"):
                yield Button("Quit", id="btn-launch-quit", variant="default")
                yield Button("Attach / Monitor Only [Esc]", id="btn-launch-attach", variant="primary")
                yield Button(
                    "▶ Runner Already Active" if self._runner_alive else "▶ Start Run & Monitor",
                    id="btn-launch-start",
                    variant="success",
                    disabled=self._runner_alive,
                )

    def on_mount(self):
        self._refresh_preview()

    def _collect_config(self):
        wb = float(self.query_one("#inp-window_budget", Input).value.strip())
        if not (0.0 < wb <= 1.0):
            raise ValueError("window_budget must be in (0.0, 1.0]")
        mm = int(self.query_one("#inp-max_modules", Input).value.strip())
        cs = int(self.query_one("#inp-chunk_size", Input).value.strip())
        mb = float(self.query_one("#inp-module_budget", Input).value.strip())
        mc = int(self.query_one("#inp-module_calls", Input).value.strip())
        rb = float(self.query_one("#inp-repair_budget", Input).value.strip())
        if mm < 0 or cs <= 0 or mb <= 0 or mc <= 0 or rb < 0:
            raise ValueError("numeric limits must be positive (max_modules/repair >= 0)")
        wave_val = self.query_one("#sel-wave", Select).value
        wave = str(wave_val) if wave_val in ("all", "wave2", "wave3", "wave4", "wave4a", "wave4b") else "all"
        skip_raw = self.query_one("#inp-skip", Input).value.strip()
        only_raw = self.query_one("#inp-only", Input).value.strip()
        return {
            "window_budget": wb,
            "window_capacity": float(self._cfg.get("window_capacity", 35.0)),
            "max_modules": mm,
            "wave": wave,
            "chunk_size": cs,
            "module_budget": mb,
            "module_calls": mc,
            "repair_budget": rb,
            "skip": [s.strip() for s in skip_raw.split(",") if s.strip()],
            "only": [s.strip() for s in only_raw.split(",") if s.strip()],
            "sleep_on_limit": bool(self.query_one("#sw-sleep_on_limit", Switch).value),
            "rate_limit_sleep": int(self._cfg.get("rate_limit_sleep", 900)),
            "wave4_max_calls": self._cfg.get("wave4_max_calls"),
            "wave4a_max_calls": self._cfg.get("wave4a_max_calls"),
            "wave4_retry": bool(self._cfg.get("wave4_retry", False)),
            "wave4_include_unresolved": bool(self._cfg.get("wave4_include_unresolved", False)),
        }

    def _apply_preset(self, preset_key):
        cfg = preset_config(preset_key)
        self._cfg = cfg
        self.query_one("#inp-window_budget", Input).value = str(cfg["window_budget"])
        self.query_one("#inp-max_modules", Input).value = str(cfg["max_modules"])
        self.query_one("#sel-wave", Select).value = cfg["wave"]
        self.query_one("#inp-chunk_size", Input).value = str(cfg["chunk_size"])
        self.query_one("#inp-module_budget", Input).value = str(cfg["module_budget"])
        self.query_one("#inp-module_calls", Input).value = str(cfg["module_calls"])
        self.query_one("#inp-repair_budget", Input).value = str(cfg["repair_budget"])
        self.query_one("#sw-sleep_on_limit", Switch).value = bool(cfg["sleep_on_limit"])
        self.query_one("#inp-skip", Input).value = ",".join(cfg["skip"])
        self.query_one("#inp-only", Input).value = ",".join(cfg["only"])
        self._refresh_preview()

    def _refresh_preview(self):
        err = self.query_one("#launcher-error", Static)
        prev = self.query_one("#launcher-preview", Static)
        try:
            cfg = self._collect_config()
            args = " ".join(overnight.build_cli_args(cfg))
            prev.update(f"CLI: python3 -m wc1.overnight {args}")
            err.update("")
        except Exception as ex:
            prev.update("CLI: (invalid settings)")
            err.update(f"Invalid setting: {ex}")

    def on_input_changed(self, _event: Input.Changed):
        self._refresh_preview()

    def on_select_changed(self, _event: Select.Changed):
        self._refresh_preview()

    def on_switch_changed(self, _event: Switch.Changed):
        self._refresh_preview()

    def on_button_pressed(self, event: Button.Pressed):
        bid = event.button.id or ""
        if bid.startswith("preset-"):
            self._apply_preset(bid.split("preset-", 1)[1])
            return
        if bid == "btn-launch-quit":
            self.dismiss({"action": "quit"})
            return
        if bid == "btn-launch-attach":
            self.dismiss({"action": "attach"})
            return
        if bid == "btn-launch-start":
            if self._runner_alive:
                self.query_one("#launcher-error", Static).update(
                    "Cannot start: an overnight runner is already active"
                )
                return
            try:
                cfg = self._collect_config()
            except Exception as ex:
                self.query_one("#launcher-error", Static).update(f"Cannot start: {ex}")
                return
            self.dismiss({"action": "start", "config": cfg})

    def action_attach_only(self):
        self.dismiss({"action": "attach"})


# ---- Main btop-style Dashboard App ------------------------------------------

class WC1DashboardApp(App):
    """btop-style live monitor & controller for wc1.overnight."""

    TITLE = "Warcraft I Decompilation Monitor"

    CSS = """
    Screen {
        background: #0d1117;
        color: #c9d1d9;
    }
    #header-bar {
        height: 1;
        background: #161b22;
        color: #c9d1d9;
        padding: 0 1;
    }
    #top-row {
        height: 16;
        margin: 0 0 0 0;
    }
    #bottom-row {
        height: 1fr;
    }
    .panel {
        background: #161b22;
        border: round #30363d;
        border-title-color: #58a6ff;
        border-title-style: bold;
        padding: 0 1;
    }
    .panel:focus-within {
        border: round #58a6ff;
    }
    #quota-panel {
        width: 44%;
    }
    #heatmap-panel {
        width: 56%;
    }
    #agents-panel {
        width: 44%;
    }
    #stream-panel {
        width: 56%;
    }
    #quota-bars {
        height: 5;
    }
    #burn-label {
        height: 1;
        color: #8b949e;
    }
    #burn-spark {
        height: 2;
        margin: 0 0 0 0;
    }
    #burn-spark > .sparkline--max-color {
        color: #39c5cf;
    }
    #burn-spark > .sparkline--min-color {
        color: #21262d;
    }
    #quota-stats {
        height: 4;
    }
    #heatmap-legend {
        height: 1;
        color: #8b949e;
    }
    #heatmap-grid {
        height: 1fr;
    }
    #heatmap-inspector {
        height: 1;
        background: #0d1117;
        color: #e6edf3;
        padding: 0 1;
    }
    #workers-table {
        height: 1fr;
        background: #161b22;
    }
    #stream-log {
        height: 1fr;
        background: #0d1117;
        scrollbar-size: 1 1;
    }
    Footer {
        background: #161b22;
    }
    """

    BINDINGS = [
        Binding("q", "detach", "Detach"),
        Binding("m", "toggle_heatmap_mode", "Fn/Mod"),
        Binding("o", "toggle_oos", "OOS"),
        Binding("a", "filter_all", "All"),
        Binding("t", "filter_thinking", "Think"),
        Binding("v", "filter_verify", "Verify"),
        Binding("f", "enable_follow", "Follow"),
        Binding("end", "enable_follow", "Follow", show=False),
        Binding("p", "toggle_pause", "Pause"),
        Binding("w", "wake_runner", "Wake"),
        Binding("x", "graceful_stop", "Stop"),
        Binding("K", "kill_prompt", "KILL"),
        Binding("g", "show_commits", "Commits"),
        Binding("l", "open_launcher", "Launch"),
    ]

    DASHBOARD_ACTIONS = frozenset({
        "detach",
        "toggle_heatmap_mode",
        "toggle_oos",
        "filter_all",
        "filter_thinking",
        "filter_verify",
        "enable_follow",
        "toggle_pause",
        "wake_runner",
        "graceful_stop",
        "kill_prompt",
        "show_commits",
        "open_launcher",
    })

    def __init__(self, live_root=None, open_launcher=False, initial_config=None,
                 autostart=False, heatmap_loader=None):
        super().__init__()
        self.live_root = live_root
        self._open_launcher_on_mount = open_launcher
        self._initial_config = initial_config
        self._autostart = autostart
        self._heatmap_loader = heatmap_loader or HeatmapDataLoader()

        self._state = {}
        self._rate_limits = {}
        self._runner_alive = False
        self._spawned_proc = None
        self._selected_worker = None
        self._user_pinned_worker = False
        self._stream_offset = 0
        self._stream_inode = None
        self._stream_events = []
        self._stream_filter = "all"
        self._stream_follow = True
        self._last_table_sig = None
        self._table_row_keys = []
        self._table_col_keys = []
        self._table_prev_cells = {}
        self._last_heatmap_overlay_sig = None
        self._heatmap_src_rows = None
        self._heatmap_loading = False
        self._pending_highlight_wid = None
        self._highlight_timer = None
        self._ledger_fallback_cache = (0.0, None)
        self._last_poll_err = {}
        self._last_run_id = None
        self._row_worker_map = {}

    def check_action(self, action: str, parameters: tuple[object, ...]) -> bool | None:
        if action in self.DASHBOARD_ACTIONS and isinstance(self.screen, ModalScreen):
            return False
        return True

    def compose(self) -> ComposeResult:
        yield Static("", id="header-bar")
        with Horizontal(id="top-row"):
            with Vertical(id="quota-panel", classes="panel"):
                yield Static("", id="quota-bars")
                yield Static("5h Burn Rate (24 buckets)", id="burn-label")
                yield Sparkline([0.0] * 24, id="burn-spark")
                yield Static("", id="quota-stats")
            with Vertical(id="heatmap-panel", classes="panel"):
                yield Static("", id="heatmap-legend")
                yield HeatmapWidget(id="heatmap-grid")
                yield Static("Hover or focus heatmap to inspect", id="heatmap-inspector")
        with Horizontal(id="bottom-row"):
            with Vertical(id="agents-panel", classes="panel"):
                yield DataTable(id="workers-table", cursor_type="row")
            with Vertical(id="stream-panel", classes="panel"):
                yield StreamLog(
                    id="stream-log",
                    wrap=True,
                    highlight=False,
                    markup=False,
                    auto_scroll=True,
                    min_width=1,
                    max_lines=STREAM_MAX_LINES,
                )
        yield Footer()

    def on_mount(self):
        self.query_one("#quota-panel").border_title = "Quota & Pace"
        self.query_one("#heatmap-panel").border_title = "Heatmap [Functions]"
        self.query_one("#agents-panel").border_title = "Agents & Queue"
        self.query_one("#stream-panel").border_title = "Live Stream"

        tbl = self.query_one("#workers-table", DataTable)
        self._table_col_keys = tbl.add_columns("St", "Prov", "Module / Area", "Stage", "Result")

        self._update_legend()
        if getattr(self._heatmap_loader, "_rows_cache", None):
            self._sync_heatmap_overlays(rows=self._heatmap_loader._rows_cache, force=True)
        else:
            self._refresh_heatmap(force=True)
        self._poll_live_state()

        self.set_interval(0.35, self._poll_live_state)
        self.set_interval(0.25, self._poll_stream)
        self.set_interval(2.5, self._refresh_heatmap)

        if self._autostart and self._initial_config:
            self._start_runner(self._initial_config)
        elif self._open_launcher_on_mount:
            self.action_open_launcher()

    def _report_poll_error(self, key, exc):
        now = time.time()
        msg = f"{type(exc).__name__}: {exc}"
        prev_ts, prev_msg = self._last_poll_err.get(key, (0.0, None))
        if prev_msg != msg or (now - prev_ts) >= 30.0:
            self._last_poll_err[key] = (now, msg)
            try:
                self.notify(f"TUI {key} error: {msg}", severity="warning")
            except Exception:
                pass

    def _has_active_runner(self):
        if self._spawned_proc is not None:
            if self._spawned_proc.poll() is None:
                return True
            self._spawned_proc = None
        return is_runner_alive(root=self.live_root)

    def _start_runner(self, cfg):
        if self._has_active_runner():
            self.notify("An overnight runner is already active — refusing to launch a second one", severity="warning")
            return False
        self._spawned_proc = spawn_runner(cfg, root=self.live_root)
        self.notify("Started detached wc1.overnight runner", severity="information")
        return True

    # ---- Polling & UI rendering ---------------------------------------------

    def _poll_live_state(self):
        try:
            self._poll_live_state_inner()
        except Exception as ex:
            self._report_poll_error("poll_state", ex)

    def _poll_live_state_inner(self):
        if self._spawned_proc is not None and self._spawned_proc.poll() is not None:
            self._spawned_proc = None
        st = live.read_json(live.state_path(root=self.live_root), {}) or {}
        rl = live.load_rate_limits(root=self.live_root)
        self._state = st
        self._rate_limits = rl
        pid = st.get("pid")
        self._runner_alive = live.pid_alive(pid) if pid else False

        run_id = st.get("run_id")
        if run_id and run_id != self._last_run_id:
            self._last_run_id = run_id
            self._user_pinned_worker = False

        # Auto-select active worker when not manually pinned
        actives = st.get("active_workers") or ([st["active_worker"]] if st.get("active_worker") else [])
        if actives and not self._user_pinned_worker and self._pending_highlight_wid is None:
            wid = actives[0].get("id") or actives[0].get("area")
            if wid and wid != self._selected_worker:
                self._select_worker(wid, user_pinned=False)
        elif not self._selected_worker and self._pending_highlight_wid is None:
            completed = st.get("completed") or []
            if completed:
                wid = completed[-1].get("id") or completed[-1].get("area")
                if wid:
                    self._select_worker(wid, user_pinned=False)

        self._render_header()
        self._render_quota()
        self._render_workers_table()
        self._update_stream_title()
        self._sync_heatmap_overlays()

    def _effective_status(self):
        st = self._state
        if not st:
            return "DETACHED"
        raw = str(st.get("status") or "DETACHED").upper()
        if not self._runner_alive and raw not in ("DONE", "FAILED", "KILLED"):
            return "DETACHED"
        return raw

    def _render_header(self):
        st = self._state
        prog = st.get("progress") or {}
        done = int(prog.get("done") or 0)
        total = int(prog.get("total") or 0)
        t3 = int(prog.get("t3") or 0)
        t4 = int(prog.get("t4") or 0)
        delta = int(prog.get("delta_done") or 0)
        if total == 0 and self._heatmap_loader._rows_cache:
            in_sc = [r for r in self._heatmap_loader._rows_cache if r["scope"] == "in"]
            total = len(in_sc)
            done = sum(1 for r in in_sc if r["done"])
            t3 = sum(1 for r in in_sc if r["c"] == "T3")
            t4 = sum(1 for r in in_sc if r["c"] == "T4")

        pct = 100.0 * done / max(1, total)
        status = self._effective_status()
        _, pill_style = STATE_COLORS.get(status, ("#8b949e", "bold #8b949e"))
        bstatus = str(st.get("build_status") or "UNKNOWN").upper()
        bstyle = "bold #3fb950" if bstatus in ("IDENTICAL", "PASS") else (
            "bold #f85149" if bstatus == "FAILED" else "#8b949e"
        )
        now_s = datetime.datetime.now().strftime("%H:%M:%S")
        pid_s = f"pid:{st['pid']}" if self._runner_alive and st.get("pid") else "detached"

        t = Text()
        t.append("⚔ WARCRAFT I DECOMP ", style="bold #58a6ff")
        t.append(f"│ {done}/{total} ({pct:.1f}%) ", style="bold #e6edf3")
        if delta > 0:
            t.append(f"+{delta} ", style="bold #3fb950")
        t.append(f"[T3:{t3} T4:{t4}] ", style="#8b949e")
        t.append("│ war.exe:", style="#8b949e")
        t.append(bstatus, style=bstyle)
        t.append(" │ ", style="#30363d")
        t.append(f" {status} ", style=pill_style)
        if st.get("pause_requested") and status != "PAUSED":
            t.append(" [PAUSE PENDING]", style="bold #f0883e")
        if st.get("stop_requested") and status not in ("STOPPING", "DONE"):
            t.append(" [STOP PENDING]", style="bold #f85149")
        t.append(f" │ {pid_s} │ {now_s}", style="#8b949e")
        self.query_one("#header-bar", Static).update(t)

    def _fallback_ledger_metrics(self):
        now = time.time()
        ts, cached = self._ledger_fallback_cache
        if cached is not None and (now - ts) < 5.0:
            return cached
        m = overnight.ledger_metrics()
        self._ledger_fallback_cache = (now, m)
        return m

    def _render_quota(self):
        st = self._state
        rl = self._rate_limits
        cfg = st.get("config") or {}
        metrics = st.get("metrics") or self._fallback_ledger_metrics()
        now = time.time()

        wb = _safe_float(cfg.get("window_budget"), 0.8)
        cap = _safe_float(cfg.get("window_capacity"), 35.0)
        spend_5h = _safe_float(metrics.get("spend_5h"), 0.0)
        spend_7d = _safe_float(metrics.get("spend_7d"), 0.0)
        cache_hit = _safe_float(metrics.get("cache_hit_pct"), 0.0)
        cost_fn = _safe_float(metrics.get("cost_per_fn"), 0.0)
        est_left = int(_safe_float(metrics.get("est_fns_left"), 0.0))
        burn_h = _safe_float(metrics.get("burn_rate_usd_per_h"), 0.0)

        five = rl.get("five_hour") if isinstance(rl.get("five_hour"), dict) else None
        seven = rl.get("seven_day") if isinstance(rl.get("seven_day"), dict) else None

        bars = Text()
        # 5h window
        five_util = _safe_float(five.get("utilization")) if five else None
        if five_util is not None:
            pct5 = five_util * 100.0
            resets5 = _safe_float(five.get("resets_at"))
            rem5 = (resets5 - now) if resets5 is not None else None
            src5 = f"resets {format_duration(rem5)}" if rem5 and rem5 > 0 else "live"
        else:
            pct5 = min(100.0, 100.0 * spend_5h / max(1.0, cap))
            src5 = "ledger est"
        bars.append("5h ", style="bold #e6edf3")
        bars.append_text(render_bar(pct5, width=20, cap_pct=wb * 100.0 if wb < 1.0 else None))
        bars.append(f" {pct5:5.1f}% ", style="bold #e6edf3")
        bars.append(f"cap:{int(wb * 100)}% ({src5})\n", style="#8b949e")

        # 7d window
        seven_util = _safe_float(seven.get("utilization")) if seven else None
        if seven_util is not None:
            pct7 = seven_util * 100.0
            resets7 = _safe_float(seven.get("resets_at"))
            rem7 = (resets7 - now) if resets7 is not None else None
            src7 = f"resets {format_duration(rem7)}" if rem7 and rem7 > 0 else "live"
        else:
            pct7 = min(100.0, 100.0 * spend_7d / max(1.0, cap * 10.0))
            src7 = f"ledger ${spend_7d:.2f}"
        bars.append("7d ", style="bold #e6edf3")
        bars.append_text(render_bar(pct7, width=20))
        bars.append(f" {pct7:5.1f}% ", style="bold #e6edf3")
        bars.append(f"({src7})\n", style="#8b949e")

        # Sleep / status detail line
        detail = str(st.get("status_detail") or "No active runner — press [l] to launch")
        sleep_until = _safe_float(st.get("sleep_until"))
        if sleep_until is not None:
            rem_sl = max(0.0, sleep_until - now)
            detail = f"Sleeping ({format_duration(rem_sl)} left): {st.get('sleep_reason', '')}"
        bars.append(f"» {detail[:64]}", style="#d2a8ff" if self._runner_alive else "#8b949e")
        self.query_one("#quota-bars", Static).update(bars)

        spark_data = metrics.get("sparkline") or [0.0] * 24
        self.query_one("#burn-spark", Sparkline).data = [_safe_float(x, 0.0) for x in spark_data]

        stats = Text()
        stats.append("5h Spend: ", style="#8b949e")
        stats.append(f"${spend_5h:.2f}  ", style="bold #e6edf3")
        stats.append("Burn: ", style="#8b949e")
        stats.append(f"${burn_h:.2f}/h  ", style="#39c5cf")
        stats.append("Cache: ", style="#8b949e")
        stats.append(f"{cache_hit:.1f}%\n", style="bold #3fb950" if cache_hit >= 60 else "#d29922")
        stats.append("Cost/fn:  ", style="#8b949e")
        stats.append(f"${cost_fn:.3f}  ", style="bold #e6edf3")
        stats.append("Est left: ", style="#8b949e")
        stats.append(f"~{est_left} fn  ", style="bold #58a6ff")
        stats.append("Run: ", style="#8b949e")
        stats.append(f"${_safe_float(metrics.get('run_cost'), 0.0):.2f}", style="#e6edf3")
        self.query_one("#quota-stats", Static).update(stats)

    def _update_legend(self):
        hm = self.query_one("#heatmap-grid", HeatmapWidget)
        leg = Text()
        for key in ("untouched", "named", "ref", "t4", "t3", "active", "failed"):
            g, col, lbl = HEATMAP_STYLES[key]
            leg.append(g, style=f"bold {col}")
            leg.append(f" {lbl}  ", style="#8b949e")
        if hm.show_oos:
            g, col, lbl = HEATMAP_STYLES["oos"]
            leg.append(g, style=col)
            leg.append(f" {lbl}", style="#8b949e")
        self.query_one("#heatmap-legend", Static).update(leg)

    def _refresh_heatmap(self, force=False):
        if self._heatmap_loading:
            return
        self._heatmap_loading = True

        def _load():
            try:
                rows = self._heatmap_loader.load_rows(force=force)
            except Exception as ex:
                if self.is_running:
                    self.call_from_thread(self._finish_heatmap_error, ex)
                else:
                    self._heatmap_loading = False
                return
            if self.is_running:
                self.call_from_thread(self._apply_heatmap_rows, rows)
            else:
                self._heatmap_loading = False

        try:
            self.run_worker(_load, thread=True, group="heatmap")
        except Exception as ex:
            self._heatmap_loading = False
            self._report_poll_error("heatmap", ex)

    def _finish_heatmap_error(self, exc):
        self._heatmap_loading = False
        self._report_poll_error("heatmap", exc)

    def _apply_heatmap_rows(self, rows):
        self._heatmap_loading = False
        try:
            self._sync_heatmap_overlays(rows=rows)
        except Exception as ex:
            self._report_poll_error("heatmap", ex)

    def _sync_heatmap_overlays(self, rows=None, force=False):
        hm = self.query_one("#heatmap-grid", HeatmapWidget)
        st = self._state
        actives = st.get("active_workers") or ([st["active_worker"]] if st.get("active_worker") else [])
        active_addrs = set()
        active_mods = set()
        if self._runner_alive:
            for w in actives:
                active_addrs.update(int(a) for a in (w.get("addrs") or []))
                if w.get("module"):
                    active_mods.add(w["module"])
        failed_addrs = set(int(a) for a in (st.get("failed_addrs") or []))
        failed_mods = set(st.get("failed_modules") or [])

        rows_changed = False
        if rows is not None:
            rows_changed = (rows is not self._heatmap_src_rows)
            self._heatmap_src_rows = rows
        use_rows = self._heatmap_src_rows if self._heatmap_src_rows is not None else hm.fn_rows
        sig = (
            len(use_rows),
            frozenset(active_addrs),
            frozenset(failed_addrs),
            frozenset(active_mods),
            frozenset(failed_mods),
            hm.mode,
            hm.show_oos,
        )
        if not force and not rows_changed and sig == self._last_heatmap_overlay_sig:
            return
        self._last_heatmap_overlay_sig = sig
        hm.set_data(use_rows, active_addrs, failed_addrs, active_mods, failed_mods)
        mode_lbl = "Functions" if hm.mode == "functions" else "Modules"
        self.query_one("#heatmap-panel").border_title = (
            f"Heatmap [{mode_lbl}: {len(hm.cells)}] (m:mode o:oos)"
        )
        self.query_one("#heatmap-inspector", Static).update(format_inspector(hm.current_cell(), hm.mode))

    def on_heatmap_widget_cell_selected(self, msg: HeatmapWidget.CellSelected):
        self.query_one("#heatmap-inspector", Static).update(format_inspector(msg.cell, msg.mode))

    def _render_workers_table(self):
        st = self._state
        actives = st.get("active_workers") or ([st["active_worker"]] if st.get("active_worker") else [])
        completed = list(reversed(st.get("completed") or []))
        queue = list(st.get("queue") or [])

        rows = []
        row_map = {}
        idx = 0
        active_icon = "◆" if self._runner_alive else "○"
        for i, w in enumerate(actives):
            wid = w.get("id") or w.get("area") or ""
            prov = str(w.get("provider") or "claude")[:6]
            mod = f"{w.get('module', '')} ({w.get('area', '')})"
            stage = f"{w.get('phase', 'RUN')}:{w.get('stage', '')}"[:22]
            res = f"~{w.get('count', 0)} fn"
            rows.append((f"active:{i}:{wid}", active_icon, prov, mod[:28], stage, res, wid))
            row_map[idx] = wid
            idx += 1

        for i, c in enumerate(completed[:15]):
            wid = c.get("id") or c.get("area") or ""
            prov = str(c.get("provider") or "claude")[:6]
            st_c = str(c.get("status") or "")
            icon = "✓" if st_c == "COMMITTED" else ("✕" if st_c in ("FAILED", "KILLED", "STALLED", "TOOLCHAIN_ERROR") else "○")
            mod = f"{c.get('module', '')} ({c.get('area', '')})"
            res = (
                f"+{int(c.get('delta') or 0)} ${float(c.get('cost') or 0):.2f} {c.get('commit', '')}"
                if st_c == "COMMITTED"
                else f"{st_c} ${float(c.get('cost') or 0):.2f}"
            )
            rows.append((f"done:{i}:{wid}", icon, prov, mod[:28], c.get("mode", ""), res[:24], wid))
            row_map[idx] = wid
            idx += 1

        for i, q in enumerate(queue[:15]):
            mod = f"{q.get('module', '')} ({q.get('area', '')})"
            rows.append((f"queue:{i}", "⋯", "queue", mod[:28], q.get("mode", ""), f"~{q.get('count', 0)} fn ({q.get('avg_insns', 0)}i)", None))
            idx += 1

        sig = tuple(rows)
        if sig == self._last_table_sig:
            return
        self._last_table_sig = sig
        self._row_worker_map = row_map

        tbl = self.query_one("#workers-table", DataTable)
        new_keys = [r[0] for r in rows]

        def _icon_cell(icon):
            col = "#d2a8ff" if icon == "◆" else (
                "#3fb950" if icon == "✓" else ("#f85149" if icon == "✕" else "#8b949e")
            )
            return Text(icon, style=f"bold {col}")

        if new_keys == self._table_row_keys and len(self._table_col_keys) == 5:
            # Update changed cells in place to preserve scroll position and cursor cleanly
            for r in rows:
                rkey, icon, prov, mod, stage, res, _wid = r
                raw_vals = (icon, prov, mod, stage, res)
                prev_vals = self._table_prev_cells.get(rkey)
                if prev_vals == raw_vals:
                    continue
                self._table_prev_cells[rkey] = raw_vals
                rendered = (_icon_cell(icon), prov, mod, stage, res)
                for ci, val in enumerate(rendered):
                    if prev_vals is None or prev_vals[ci] != raw_vals[ci]:
                        tbl.update_cell(rkey, self._table_col_keys[ci], val, update_width=True)
        else:
            prev_coord = tbl.cursor_coordinate
            with tbl.prevent(DataTable.RowHighlighted):
                tbl.clear()
                self._table_prev_cells = {}
                for r in rows:
                    rkey, icon, prov, mod, stage, res, _wid = r
                    self._table_prev_cells[rkey] = (icon, prov, mod, stage, res)
                    tbl.add_row(_icon_cell(icon), prov, mod, stage, res, key=rkey)
                self._table_row_keys = new_keys
                if rows:
                    target_r = None
                    if self._selected_worker:
                        for r_idx, wid in row_map.items():
                            if wid == self._selected_worker:
                                target_r = r_idx
                                break
                    if target_r is None:
                        target_r = 0 if not self._user_pinned_worker else min(prev_coord.row, len(rows) - 1)
                    tbl.move_cursor(row=target_r, column=0, animate=False)

        self.query_one("#agents-panel").border_title = (
            f"Agents & Queue (active:{len(actives)} done:{len(completed)} next:{len(queue)})"
        )

    def _cancel_highlight_timer(self):
        if self._highlight_timer is not None:
            self._highlight_timer.stop()
            self._highlight_timer = None
        self._pending_highlight_wid = None

    def _apply_pending_highlight(self):
        wid = self._pending_highlight_wid
        self._highlight_timer = None
        self._pending_highlight_wid = None
        if wid and wid != self._selected_worker:
            self._select_worker(wid, user_pinned=True)

    def on_data_table_row_highlighted(self, event: DataTable.RowHighlighted):
        if event.data_table.id != "workers-table":
            return
        wid = self._row_worker_map.get(event.cursor_row)
        if wid and wid != self._selected_worker:
            self._cancel_highlight_timer()
            self._pending_highlight_wid = wid
            self._highlight_timer = self.set_timer(0.06, self._apply_pending_highlight)

    def on_data_table_row_selected(self, event: DataTable.RowSelected):
        if event.data_table.id != "workers-table":
            return
        wid = self._row_worker_map.get(event.cursor_row)
        if not wid:
            return
        self._cancel_highlight_timer()
        if wid != self._selected_worker:
            self._select_worker(wid, user_pinned=True)
        else:
            self._user_pinned_worker = True

    # ---- Live Stream Tailing ------------------------------------------------

    def _worker_stream_stat(self, worker_id):
        if not worker_id:
            return None
        try:
            st = os.stat(live.worker_stream_path(worker_id, root=self.live_root))
            return st.st_ino, st.st_size
        except OSError:
            return None

    def _select_worker(self, worker_id, user_pinned=False):
        self._selected_worker = worker_id
        self._user_pinned_worker = user_pinned
        self._stream_follow = True
        evs, new_off = live.read_recent_events(
            worker_id, limit=STREAM_HISTORY_LIMIT, root=self.live_root,
        )
        stat_info = self._worker_stream_stat(worker_id)
        self._stream_inode = stat_info[0] if stat_info else None
        self._stream_offset = new_off
        self._stream_events = evs
        self._redraw_stream()
        self._update_stream_title()

    def _update_stream_title(self):
        wid = self._selected_worker or "none"
        filt = self._stream_filter.upper()
        fol = "FOLLOW" if self._stream_follow else "SCROLL-PAUSED (f)"
        self.query_one("#stream-panel").border_title = (
            f"Live Stream [{wid}] filter:{filt} │ {fol}"
        )

    def _format_event_line(self, ev):
        k = str(ev.get("kind") or "info").lower()
        txt = str(ev.get("text") or "")
        ts = _safe_float(ev.get("ts"))
        ts_s = datetime.datetime.fromtimestamp(ts).strftime("%H:%M:%S") if ts is not None else "        "
        tag_map = {
            "think":  ("[THINK]", "italic #d2a8ff"),
            "out":    ("[OUT]  ", "#e6edf3"),
            "tool":   ("[TOOL] ", "bold #e3b341"),
            "stage":  ("[STAGE]", "bold #58a6ff"),
            "perm":   ("[PERM] ", "#58a6ff"),
            "match":  ("[MATCH]", "bold #3fb950"),
            "verify": ("[VRFY] ", "#39c5cf"),
            "commit": ("[GIT]  ", "bold #3fb950"),
            "error":  ("[ERR]  ", "bold #f85149"),
            "info":   ("[INFO] ", "#8b949e"),
        }
        tag, style = tag_map.get(k, ("[LOG]  ", "#8b949e"))
        line = Text()
        line.append(f"{ts_s} ", style="#484f58")
        line.append(f"{tag} ", style=style)
        line.append(txt, style=style if k in ("think", "stage", "match", "commit", "error") else "#c9d1d9")
        return line

    def _write_events_to_log(self, log, events):
        if not events:
            return False
        follow = self._stream_follow
        last_idx = len(events) - 1
        for i, ev in enumerate(events):
            log.write(
                self._format_event_line(ev),
                scroll_end=(follow and i == last_idx),
            )
        if follow:
            log.scroll_end(animate=False, x_axis=False)
        return True

    def _redraw_stream(self):
        log = self.query_one("#stream-log", RichLog)
        log.clear()
        log.auto_scroll = self._stream_follow
        filtered = [ev for ev in self._stream_events if filter_stream_event(ev, self._stream_filter)]
        to_show = filtered[-STREAM_RENDER_LIMIT:]
        self._write_events_to_log(log, to_show)

    def _poll_stream(self):
        try:
            self._poll_stream_inner()
        except Exception as ex:
            self._report_poll_error("poll_stream", ex)

    def _poll_stream_inner(self):
        if not self._selected_worker:
            return
        stat_info = self._worker_stream_stat(self._selected_worker)
        if stat_info is not None:
            ino, size = stat_info
            recreated = (self._stream_inode is not None and ino != self._stream_inode)
            truncated = (size < self._stream_offset)
            if recreated or truncated:
                evs, new_off = live.read_recent_events(
                    self._selected_worker, limit=STREAM_HISTORY_LIMIT, root=self.live_root,
                )
                self._stream_inode = ino
                self._stream_offset = new_off
                self._stream_events = evs
                self._redraw_stream()
                return
            if self._stream_inode is None:
                self._stream_inode = ino

        evs, new_off = live.tail_events(
            self._selected_worker,
            offset=self._stream_offset,
            root=self.live_root,
            max_events=STREAM_POLL_MAX_EVENTS,
        )
        if new_off < self._stream_offset:
            # File truncated between stat and tail_events
            evs, new_off = live.read_recent_events(
                self._selected_worker, limit=STREAM_HISTORY_LIMIT, root=self.live_root,
            )
            self._stream_offset = new_off
            self._stream_events = evs
            self._redraw_stream()
            return
        self._stream_offset = new_off
        if not evs:
            return
        self._stream_events.extend(evs)
        if len(self._stream_events) > 2000:
            self._stream_events = self._stream_events[-STREAM_HISTORY_LIMIT:]
        log = self.query_one("#stream-log", RichLog)
        log.auto_scroll = self._stream_follow
        matching = [ev for ev in evs if filter_stream_event(ev, self._stream_filter)]
        self._write_events_to_log(log, matching)

    def on_stream_log_manual_scroll_up(self, _msg: StreamLog.ManualScrollUp):
        if self._stream_follow:
            self._stream_follow = False
            self.query_one("#stream-log", RichLog).auto_scroll = False
            self._update_stream_title()

    def on_stream_log_resume_follow(self, _msg: StreamLog.ResumeFollow):
        self.action_enable_follow()

    # ---- Actions & Controls -------------------------------------------------

    def action_detach(self):
        """Detach UI cleanly without affecting any background runner."""
        self.exit(0)

    def action_toggle_heatmap_mode(self):
        hm = self.query_one("#heatmap-grid", HeatmapWidget)
        hm.set_mode("modules" if hm.mode == "functions" else "functions")
        self._sync_heatmap_overlays(force=True)

    def action_toggle_oos(self):
        hm = self.query_one("#heatmap-grid", HeatmapWidget)
        hm.set_show_oos(not hm.show_oos)
        self._update_legend()
        self._sync_heatmap_overlays(force=True)

    def _set_filter(self, mode):
        self._stream_filter = mode
        self._redraw_stream()
        self._update_stream_title()

    def action_filter_all(self):
        self._set_filter("all")

    def action_filter_thinking(self):
        self._set_filter("thinking")

    def action_filter_verify(self):
        self._set_filter("verify")

    def action_enable_follow(self):
        self._stream_follow = True
        log = self.query_one("#stream-log", RichLog)
        log.auto_scroll = True
        log.scroll_end(animate=False, x_axis=False)
        self._update_stream_title()

    def _require_live_runner(self):
        if not self._runner_alive:
            self.notify("No active runner — control ignored", severity="warning")
            return False
        return True

    def action_toggle_pause(self):
        if not self._require_live_runner():
            return
        st = self._state
        paused = bool(st.get("pause_requested") or st.get("status") == "PAUSED")
        action = "resume" if paused else "pause"
        live.send_control(action, root=self.live_root)
        self.notify(f"Sent control: {action}", severity="information")

    def action_wake_runner(self):
        if not self._require_live_runner():
            return
        live.send_control("wake", root=self.live_root)
        self.notify("Sent control: wake (early resume)", severity="information")

    def action_graceful_stop(self):
        if not self._require_live_runner():
            return
        live.send_control("graceful_stop", root=self.live_root)
        self.notify("Graceful stop sent — finishing active module & committing", severity="warning")

    def action_kill_prompt(self):
        if not self._require_live_runner():
            return
        def _after_confirm(confirmed):
            if confirmed:
                live.send_control("kill", root=self.live_root)
                self.notify("KILL signal sent — rolling back active module", severity="error")
        self.push_screen(KillConfirmScreen(), _after_confirm)

    def action_show_commits(self):
        commits = self._state.get("commits") or []
        self.push_screen(CommitsScreen(commits, root=self.live_root))

    def action_open_launcher(self):
        def _after_launch(res):
            if not res:
                return
            act = res.get("action")
            if act == "quit":
                self.exit(0)
            elif act == "start":
                cfg = res["config"]
                self._start_runner(cfg)
        self.push_screen(
            LauncherScreen(
                initial_config=self._initial_config or self._state.get("config"),
                runner_alive=self._has_active_runner(),
            ),
            _after_launch,
        )


def launch_tui(open_launcher=False, initial_config=None, autostart=False, live_root=None):
    app = WC1DashboardApp(
        live_root=live_root,
        open_launcher=open_launcher,
        initial_config=initial_config,
        autostart=autostart,
    )
    app.run()
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(prog="wc1.tui", description="btop-style TUI monitor & launcher for wc1.overnight")
    ap.add_argument("--launcher", action="store_true", help="Open interactive run launcher on startup")
    ap.add_argument("--root", default=None, help="Optional repo root override (for testing)")
    a = ap.parse_args(argv)
    return launch_tui(open_launcher=a.launcher, live_root=a.root)


if __name__ == "__main__":
    sys.exit(main())
