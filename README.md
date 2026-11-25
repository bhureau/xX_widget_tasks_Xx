# Obsidian Tasks Widget

A small desktop widget for Windows that shows the tasks from an Obsidian Markdown note and stays on top of your other windows. Ticking a task in the widget updates the note, and changes you make in Obsidian appear in the widget within a couple of seconds.

<img width="630" height="452" alt="widget_funny" src="https://github.com/user-attachments/assets/5a96a000-e8a3-4fae-99f9-135a0956af9b" />



## Features

- **Main goals only**: the widget lists the top-level tasks (no indentation). Click a goal's arrow ▸ to show its subtasks.
- **Progress per goal**: a percentage and a thin progress bar show how many subtasks are done. The color goes from red to orange to green as you progress.
- **Two-way sync**: clicking a checkbox writes `[x]` or `[ ]` to the Markdown file. The widget watches the file and reloads when it changes.
- **Obsidian-style look**: rounded checkboxes that turn purple when checked, a dark card with rounded corners (Windows 11) and header buttons that only appear on hover.
- **Sharp on high-DPI screens**: the widget adapts to Windows display scaling (125 %, 150 %, 200 %…).
- **No dependencies**: it uses only the Python standard library (`tkinter`).

## Expected Markdown format

The widget reads standard Markdown task lists, with subtasks indented by a tab or 4 spaces:

```markdown
# Personal

- [ ] Finish the PyTorch book
	- [x] Chapter 4 ✅ 2026-11-24
	- [ ] Chapter 5
	- [ ] Chapter 6
- [ ] Sport
	- [ ] Swimming
	- [ ] Yoga
```

- `- [ ]`, `* [ ]` and `+ [ ]` are all recognized.
- `#` headings group the goals. Headings with no tasks under them are hidden.
- The widget hides common Obsidian syntax so the text is easier to read: `[[links|alias]]`, `**bold**`, `==highlight==`, `` `code` `` and the `✅ YYYY-MM-DD` completion dates added by the Tasks plugin. Your file keeps all of it.

## Requirements

- Windows 10 or 11. Rounded corners need Windows 11; on Windows 10 the corners stay square.
- Python 3.9 or newer, with `tkinter`. The official Windows installer from python.org includes it by default.

No packages need to be installed.

## Installation

```bash
git clone <repository-url>
cd <repository-folder>
```

The widget works right away with the demo note `Funny_objectives.md`, which sits next to the script. To use your own note, open `config.py` and replace the path:

```python
MARKDOWN_PATH = r"C:\path\to\your\vault\Tasks.md"
```

## Usage

```bash
python tasks_widget.py
```

- **Move** the widget by dragging its header.
- **Expand or collapse** a goal by clicking its arrow or its name.
- **Tick or untick** a task by clicking its checkbox. Subtasks can also be ticked by clicking their text.
- **Reload** with ⟳ and **close** with ✕. Both buttons appear when the mouse is over the widget.
- **Scroll** with the mouse wheel when the list is taller than the maximum height.

### Run without a console window

Use `pythonw` or rename the script to `.pyw`:

```bash
pythonw tasks_widget.py
```

### Start with Windows

1. Press `Win + R`, type `shell:startup` and press Enter.
2. In the folder that opens, create a shortcut with this target:
   ```
   pythonw.exe "C:\path\to\tasks_widget.py"
   ```

