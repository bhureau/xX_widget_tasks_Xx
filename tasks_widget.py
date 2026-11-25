"""
Task widget for Obsidian.

Shows the main goals (tasks with no indentation) of a Markdown file in a small
always-on-top window. Clicking a goal's arrow shows its subtasks. Ticking a
checkbox updates the file directly, and the widget reloads by itself when the
file changes in Obsidian.

No external dependencies: standard library only (tkinter).
"""

import ctypes
import os
import re
import tkinter as tk
from tkinter import font as tkfont

# Settings (file path, size, colors...) live in config.py
from config import (
    MARKDOWN_PATH, REFRESH_MS, WIDTH, MAX_HEIGHT, CORNER, MARGIN,
    SHOW_DONE, OPACITY, ROUNDED_CORNERS,
    BG, FG, FG_DONE, FG_TITLE, FG_MUTED,
    CHECKBOX_BORDER, CHECKBOX_FILL, CHECKBOX_TICK,
    BAR_BG, BAR_HEIGHT, BAR_COLORS,
    FONT, FONT_BOLD, FONT_TITLE,
)

# ---------------------------------------------------------------------------
# MARKDOWN PARSING
# ---------------------------------------------------------------------------
TASK_RE = re.compile(r"^(\s*[-*+]\s+\[)([ xX])(\]\s+)(.*)$")
HEADING_RE = re.compile(r"^(#{1,6})\s+(.*)$")


def clean_text(text: str) -> str:
    """Strip the most common Obsidian syntax so the text reads cleanly."""
    text = re.sub(r"\[\[([^\]|]+)\|([^\]]+)\]\]", r"\2", text)  # [[link|alias]]
    text = re.sub(r"\[\[([^\]]+)\]\]", r"\1", text)              # [[link]]
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)         # [txt](url)
    text = re.sub(r"(\*\*|__|==|~~)(.+?)\1", r"\2", text)        # bold, highlight...
    text = re.sub(r"`([^`]+)`", r"\1", text)                     # inline code
    text = re.sub(r"✅\s*\d{4}-\d{2}-\d{2}", "", text)            # completion date
    return text.strip()


def read_tasks(path: str):
    """
    Return a list of items:
      ('heading', text)
      ('goal', task, [subtasks])
    where a task is a dict {line, done, text, level}.
    """
    with open(path, encoding="utf-8") as f:
        lines = f.read().splitlines()

    items = []
    goal = None
    for i, line in enumerate(lines):
        m = TASK_RE.match(line)
        if m:
            # Indentation width (one tab = 4 spaces)
            width = len(line[:len(line) - len(line.lstrip())].expandtabs(4))
            task = {
                "line": i,
                "done": m.group(2).lower() == "x",
                "text": clean_text(m.group(4)),
                "level": 0 if width == 0 else max(1, width // 4),
            }
            if task["level"] == 0:
                goal = ("goal", task, [])
                items.append(goal)
            elif goal is not None:
                goal[2].append(task)
            continue
        h = HEADING_RE.match(line)
        if h:
            goal = None
            items.append(("heading", clean_text(h.group(2))))
    return items


def toggle_task(path: str, line_number: int) -> None:
    """Tick / untick the task on the given line, directly in the file."""
    with open(path, encoding="utf-8", newline="") as f:
        content = f.read()
    newline = "\r\n" if "\r\n" in content else "\n"
    lines = content.split(newline)

    m = TASK_RE.match(lines[line_number])
    if not m:
        return  # the file changed in the meantime
    new_state = " " if m.group(2).lower() == "x" else "x"
    lines[line_number] = m.group(1) + new_state + m.group(3) + m.group(4)

    with open(path, "w", encoding="utf-8", newline="") as f:
        f.write(newline.join(lines))


# ---------------------------------------------------------------------------
# DRAWING HELPERS
# ---------------------------------------------------------------------------
SCALE = 1.0  # display scaling factor (2.0 for a 200 % screen)


def px(*values):
    """Convert "logical" pixels to real pixels according to display scaling."""
    res = tuple(round(v * SCALE) for v in values)
    return res[0] if len(res) == 1 else res


def enable_dpi_awareness():
    """Sharp rendering on scaled displays (otherwise Windows blurs the window)."""
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except (AttributeError, OSError):
        pass


def blend(c1: str, c2: str, t: float) -> str:
    """Color between c1 and c2 (t = 0 -> c1, t = 1 -> c2)."""
    a = [int(c1[i:i + 2], 16) for i in (1, 3, 5)]
    b = [int(c2[i:i + 2], 16) for i in (1, 3, 5)]
    return "#" + "".join(f"{round(x + (y - x) * t):02x}" for x, y in zip(a, b))


def progress_color(ratio: float) -> str:
    """Red -> orange -> green gradient based on progress."""
    start, middle, end = BAR_COLORS
    if ratio <= 0.5:
        return blend(start, middle, ratio / 0.5)
    return blend(middle, end, (ratio - 0.5) / 0.5)


def rounded_rectangle(canvas, x1, y1, x2, y2, r, **options):
    """Draw a rounded rectangle (smoothed polygon) on a canvas."""
    points = [x1 + r, y1, x2 - r, y1, x2, y1, x2, y1 + r, x2, y2 - r, x2, y2,
              x2 - r, y2, x1 + r, y2, x1, y2, x1, y2 - r, x1, y1 + r, x1, y1]
    return canvas.create_polygon(points, smooth=True, **options)


class ObsidianCheckbox(tk.Canvas):
    """Drawn checkbox: rounded square, purple with a tick once checked."""

    def __init__(self, parent, size, done, command):
        super().__init__(parent, width=size + 2, height=size + 2, bg=BG,
                         highlightthickness=0, cursor="hand2")
        self.size, self.done = size, done
        self._draw(hover=False)
        self.bind("<Button-1>", lambda e: command())
        self.bind("<Enter>", lambda e: self._draw(hover=True))
        self.bind("<Leave>", lambda e: self._draw(hover=False))

    def _draw(self, hover):
        self.delete("all")
        s = self.size
        r = max(3, s // 4)
        if self.done:
            rounded_rectangle(self, 1, 1, s, s, r, fill=CHECKBOX_FILL,
                              outline=CHECKBOX_FILL)
            self.create_line(s * 0.28, s * 0.52, s * 0.44, s * 0.68,
                             s * 0.74, s * 0.36, fill=CHECKBOX_TICK,
                             width=max(2, s // 8), capstyle="round",
                             joinstyle="round")
        else:
            rounded_rectangle(self, 1, 1, s, s, r, fill=BG, width=1.5 * SCALE,
                              outline=CHECKBOX_FILL if hover else CHECKBOX_BORDER)


def round_window_corners(root: tk.Tk) -> None:
    """Windows 11 rounded corners and thin border (no effect elsewhere)."""
    try:
        hwnd = ctypes.windll.user32.GetParent(root.winfo_id())
        dwm = ctypes.windll.dwmapi
        rounded = ctypes.c_int(2)                                  # DWMWCP_ROUND
        dwm.DwmSetWindowAttribute(hwnd, 33, ctypes.byref(rounded), 4)
        r, g, b = (int(BAR_BG[i:i + 2], 16) for i in (1, 3, 5))
        border = ctypes.c_int(r | (g << 8) | (b << 16))            # COLORREF
        dwm.DwmSetWindowAttribute(hwnd, 34, ctypes.byref(border), 4)
    except (AttributeError, OSError):
        pass  # Windows 10 or another OS: square corners


# ---------------------------------------------------------------------------
# INTERFACE
# ---------------------------------------------------------------------------
class TasksWidget:
    def __init__(self, root: tk.Tk):
        global SCALE
        SCALE = root.winfo_fpixels("1i") / 96

        self.root = root
        self.last_mtime = None
        self.expanded = set()     # texts of the goals currently expanded
        self._drag = (0, 0)
        self.placed = False       # has the widget been placed in its corner yet?
        self.hovered = False      # is the mouse over the widget?

        root.overrideredirect(True)            # no title bar
        root.attributes("-topmost", True)      # always on top
        root.attributes("-alpha", OPACITY)
        root.configure(bg=BG)
        root.geometry(f"{px(WIDTH)}x{px(200)}")

        self.f_normal = tkfont.Font(family=FONT, size=10)
        self.f_strike = tkfont.Font(family=FONT, size=10, overstrike=True)
        self.f_goal = tkfont.Font(family=FONT_BOLD, size=10)
        self.f_goal_strike = tkfont.Font(family=FONT_BOLD, size=10,
                                         overstrike=True)
        self.f_small = tkfont.Font(family=FONT, size=9)
        self.f_title = tkfont.Font(family=FONT_TITLE, size=13)
        self.f_button = tkfont.Font(family="Segoe UI Symbol", size=14)
        self.f_refresh = tkfont.Font(family="Segoe UI Symbol", size=17)
        self.f_arrow = tkfont.Font(family="Segoe UI Symbol", size=12)

        self._build_header()
        self._build_list()

        root.bind("<Enter>", lambda e: self._check_hover())
        root.bind("<Leave>", lambda e: root.after(30, self._check_hover))

        if ROUNDED_CORNERS:
            root.update_idletasks()
            round_window_corners(root)
        self.watch_file()

    # --- Integrated header (draggable) -------------------------------------
    def _build_header(self):
        self.header = tk.Frame(self.root, bg=BG)
        self.header.pack(fill="x", padx=px(14, 8), pady=px(10, 4))

        self.title = tk.Label(self.header, text="Tasks", font=self.f_title,
                              bg=BG, fg=FG)
        self.title.pack(side="left")
        self.counter = tk.Label(self.header, text="", font=self.f_normal,
                                bg=BG, fg=FG_MUTED)
        self.counter.pack(side="left", padx=px(6, 0), pady=px(3, 0))

        # Discreet buttons: invisible until the mouse is over the widget
        self.buttons = []

        def button(text, cmd, hover_color=FG, font=None, gap=0):
            b = tk.Label(self.header, text=text, bg=BG, fg=BG,
                         font=font or self.f_button, padx=px(4), cursor="hand2")
            b.pack(side="right", padx=px(0, gap))
            b.bind("<Button-1>", lambda e: cmd())
            b.bind("<Enter>", lambda e: b.config(fg=hover_color))
            b.bind("<Leave>", lambda e: b.config(
                fg=FG_MUTED if self.hovered else BG))
            self.buttons.append(b)

        button("✕", self.root.destroy, "#f38ba8")
        button("⟳", self.reload, font=self.f_refresh, gap=8)

        for w in (self.header, self.title, self.counter):
            w.bind("<ButtonPress-1>", self._start_drag)
            w.bind("<B1-Motion>", self._drag_move)

    def _check_hover(self):
        x, y = self.root.winfo_pointerxy()
        rx, ry = self.root.winfo_rootx(), self.root.winfo_rooty()
        inside = (rx <= x < rx + self.root.winfo_width()
                  and ry <= y < ry + self.root.winfo_height())
        if inside != self.hovered:
            self.hovered = inside
            for b in self.buttons:
                b.config(fg=FG_MUTED if inside else BG)

    def _start_drag(self, e):
        self._drag = (e.x_root - self.root.winfo_x(), e.y_root - self.root.winfo_y())

    def _drag_move(self, e):
        self.root.geometry(f"+{e.x_root - self._drag[0]}+{e.y_root - self._drag[1]}")

    # --- Scrollable list ---------------------------------------------------
    def _build_list(self):
        container = tk.Frame(self.root, bg=BG)
        container.pack(fill="both", expand=True)

        self.canvas = tk.Canvas(container, bg=BG, highlightthickness=0)
        self.canvas.pack(side="left", fill="both", expand=True)

        self.list = tk.Frame(self.canvas, bg=BG)
        self.canvas.create_window((0, 0), window=self.list, anchor="nw",
                                  width=px(WIDTH))
        self.list.bind("<Configure>", lambda e: self.canvas.configure(
            scrollregion=self.canvas.bbox("all")))
        self.root.bind_all("<MouseWheel>", lambda e: self.canvas.yview_scroll(
            int(-e.delta / 120), "units"))

    # --- Loading -------------------------------------------------------------
    def watch_file(self):
        """Reload if the file was modified (by Obsidian, for example)."""
        try:
            mtime = os.path.getmtime(MARKDOWN_PATH)
        except OSError:
            mtime = None
        if mtime != self.last_mtime:
            self.last_mtime = mtime
            self.reload()
        self.root.after(REFRESH_MS, self.watch_file)

    def reload(self):
        for w in self.list.winfo_children():
            w.destroy()

        try:
            items = read_tasks(MARKDOWN_PATH)
        except OSError as err:
            self._message(f"File not found:\n{MARKDOWN_PATH}\n\n{err}")
            self._fit_height()
            return

        goals = [e for e in items if e[0] == "goal"]
        self.title.config(text=os.path.splitext(os.path.basename(MARKDOWN_PATH))[0])
        remaining = sum(1 for e in goals if not e[1]["done"])
        self.counter.config(text=f"· {remaining}")

        if not SHOW_DONE:
            items = [e for e in items if e[0] == "heading" or not e[1]["done"]]

        # Drop headings with no goal under them
        items = [e for i, e in enumerate(items)
                 if e[0] != "heading"
                 or (i + 1 < len(items) and items[i + 1][0] == "goal")]

        if not any(e[0] == "goal" for e in items):
            self._message("No tasks 🎉")

        for item in items:
            if item[0] == "heading":
                tk.Label(self.list, text=item[1].upper(), font=self.f_small, bg=BG,
                         fg=FG_TITLE, anchor="w", padx=px(14)
                         ).pack(fill="x", pady=px(10, 2))
            else:
                self._goal(item[1], item[2])

        self._fit_height()

    def _goal(self, task, subtasks):
        key = task["text"]
        is_open = key in self.expanded
        done = task["done"]

        row = tk.Frame(self.list, bg=BG)
        row.pack(fill="x", padx=px(6, 14), pady=px(6, 0))

        # Arrow to expand / collapse
        arrow = tk.Label(row, text=("▾" if is_open else "▸") if subtasks else "",
                         width=2, bg=BG, fg=FG_MUTED, font=self.f_arrow,
                         cursor="hand2" if subtasks else "")
        arrow.pack(side="left", anchor="n")

        ObsidianCheckbox(row, px(15), done,
                         lambda n=task["line"]: self._on_task_click(n)
                         ).pack(side="left", anchor="n", pady=px(4, 0))

        # Completion percentage: 100 % if the goal is ticked,
        # otherwise the share of subtasks done (0 % if it has none)
        if done:
            ratio = 1.0
        elif subtasks:
            ratio = sum(1 for s in subtasks if s["done"]) / len(subtasks)
        else:
            ratio = 0.0
        color = progress_color(ratio)
        tk.Label(row, text=f"{round(ratio * 100)} %", bg=BG,
                 fg=color if ratio else FG_MUTED,
                 font=self.f_small).pack(side="right", anchor="n", pady=px(1, 0))

        label = tk.Label(row, text=task["text"], bg=BG,
                         fg=FG_DONE if done else FG,
                         font=self.f_goal_strike if done else self.f_goal,
                         anchor="w", justify="left", wraplength=px(WIDTH - 110),
                         cursor="hand2" if subtasks else "")
        label.pack(side="left", fill="x", padx=px(8, 0))

        if subtasks:
            for w in (arrow, label):
                w.bind("<Button-1>", lambda e, k=key: self._toggle_expanded(k))

        # Thin progress bar under the goal
        track = tk.Frame(self.list, bg=BAR_BG, height=px(BAR_HEIGHT))
        track.pack(fill="x", padx=px(54, 16), pady=px(3, 4))
        if ratio:
            tk.Frame(track, bg=color).place(x=0, y=0, relwidth=ratio, relheight=1)

        if is_open and subtasks:
            for s in subtasks:
                if s["done"] and not SHOW_DONE:
                    continue
                self._subtask(s)
            tk.Frame(self.list, bg=BG, height=px(4)).pack()

    def _subtask(self, task):
        done = task["done"]
        indent = 54 + (task["level"] - 1) * 18

        row = tk.Frame(self.list, bg=BG)
        row.pack(fill="x", padx=px(indent, 14), pady=px(2))

        ObsidianCheckbox(row, px(13), done,
                         lambda n=task["line"]: self._on_task_click(n)
                         ).pack(side="left", anchor="n", pady=px(5, 0))

        label = tk.Label(row, text=task["text"], bg=BG,
                         fg=FG_DONE if done else FG,
                         font=self.f_strike if done else self.f_normal,
                         anchor="w", justify="left", cursor="hand2",
                         wraplength=px(WIDTH - indent - 40))
        label.pack(side="left", fill="x", padx=px(8, 0))
        label.bind("<Button-1>", lambda e, n=task["line"]: self._on_task_click(n))

    def _toggle_expanded(self, key):
        self.expanded ^= {key}
        self.reload()

    def _on_task_click(self, line_number):
        try:
            toggle_task(MARKDOWN_PATH, line_number)
        except OSError as err:
            self._message(f"Could not write the file: {err}")
            return
        self.last_mtime = os.path.getmtime(MARKDOWN_PATH)
        self.reload()

    def _message(self, text):
        tk.Label(self.list, text=text, bg=BG, fg=FG_DONE, font=self.f_normal,
                 wraplength=px(WIDTH - 28), justify="left", padx=px(14), pady=px(10)
                 ).pack(fill="x")

    def _fit_height(self):
        self.root.update_idletasks()
        h = min(self.list.winfo_reqheight() + self.header.winfo_reqheight() + px(24),
                px(MAX_HEIGHT))
        if self.placed:
            self.root.geometry(f"{px(WIDTH)}x{h}")
            return
        # First display: place the widget in the chosen corner
        x, y = px(*MARGIN)
        if "right" in CORNER:
            x = self.root.winfo_screenwidth() - px(WIDTH) - px(MARGIN[0])
        if "bottom" in CORNER:
            y = self.root.winfo_screenheight() - h - px(MARGIN[1])
        self.root.geometry(f"{px(WIDTH)}x{h}+{x}+{y}")
        self.placed = True


if __name__ == "__main__":
    enable_dpi_awareness()
    root = tk.Tk()
    TasksWidget(root)
    root.mainloop()
