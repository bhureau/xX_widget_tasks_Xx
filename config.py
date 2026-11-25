"""Settings for the task widget (tasks_widget.py)."""

import os

# Path to the Markdown note in your Obsidian vault (change it to yours).
# Default: the demo note next to the script.
# Absolute path example: MARKDOWN_PATH = r"C:\path\to\your\vault\Tasks.md"
MARKDOWN_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                             "Funny_objectives.md")
REFRESH_MS = 2000          # how often the file is checked for changes (ms)
WIDTH = 320                # widget width in pixels
MAX_HEIGHT = 600           # maximum height before scrolling
CORNER = "top-right"       # starting corner: top-left, top-right, bottom-left, bottom-right
MARGIN = (40, 40)          # distance (x, y) in pixels from that corner
SHOW_DONE = True           # show ticked tasks (False = hide them)
OPACITY = 0.95             # 0.0 (transparent) to 1.0 (opaque)

ROUNDED_CORNERS = True     # Windows 11-style rounded corners

# Colors
BG = "#1e1e2e"             # card background
FG = "#cdd6f4"             # text
FG_DONE = "#6c7086"        # text of completed tasks
FG_TITLE = "#89b4fa"       # headings
FG_MUTED = "#7f849c"       # header buttons, arrows, 0 % percentage

# Checkboxes (Obsidian style)
CHECKBOX_BORDER = "#6c7086"   # border of an empty checkbox
CHECKBOX_FILL = "#8b5cf6"     # fill of a checked checkbox
CHECKBOX_TICK = "#ffffff"     # tick color

# Goal progress bar
BAR_BG = "#313244"         # bar track color
BAR_HEIGHT = 3             # thickness in pixels
# Gradient by progress: 0 % -> 50 % -> 100 %
BAR_COLORS = ("#f38ba8", "#fab387", "#a6e3a1")

# Fonts (installed fonts: Settings > Personalization > Fonts)
FONT = "Segoe UI Variable Text"                 # regular text
FONT_BOLD = "Segoe UI Variable Text Semibold"   # main goals
FONT_TITLE = "Segoe UI Variable Display Semib"  # header title
