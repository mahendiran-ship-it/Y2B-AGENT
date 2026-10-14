# Changelog

## 1.2.2
- **Ready-made mini apps.** Plain requests for a calculator, to-do list, stopwatch, countdown timer or clock (for example "create a web calculator with glow effects") now come from tested glow-styled templates instead of the model, so the page always renders and works. Colour words work ("make a red todo list"), and follow-ups such as "make it green" recolour the same file. Specific variants like "birthday calculator" or "alarm clock" still go to the model.

## 1.2.1
- Opening a page in the browser is now verified: the local server is checked before launching, `termux-open-url` is tried first and Android's `am start` second, and Y2B only says it asked the browser to open when a launcher really succeeded. The link is always printed so it can be pasted into Chrome.

## 1.2.0
- **Full websites on small models.** A tiny local model cannot write 500+ lines of working JavaScript, so asking for a website gave blank or basic pages. Y2B now asks the model only for short CONTENT lines (title, tagline, features, gallery items, FAQ, about) and assembles a finished, browser-tested page from a built-in template (`y2b_web.py`): loading screen, particle hero with orb and parallax, live clock, animated nav with mobile drawer, theme toggle, search/filter/sort gallery with preview modal, accordion, tabs, particle lab with sliders and colour pickers, calculator, stopwatch, notes, task list, command palette (Ctrl+K or /), keyboard shortcuts, settings panel, toasts, optional sound, reduced-motion support. Works offline, one HTML file.
- Triggered by words like website, portfolio, futuristic, ultra-modern. New `/site <topic>` command. Follow-ups such as "change the title" rebuild the site instead of asking the small model to rewrite 47 KB.
- Model text is injected as data (never as code), so odd model output cannot break the page.
- `install.sh` copies `y2b_web.py` too.

## 1.1.1
- Multi-line pastes are now sent as ONE prompt. Before, every pasted line was sent to the model as a separate message, so long project prompts were answered line by line and never built. New `/prompt <file>` command sends a whole file as a single request.
- Fixed files silently not being saved: the "Save file?" prompt could be auto-answered "No" by leftover pasted lines or broken input (e.g. after switching away from Termux). Pending keystrokes are now flushed before every question, an empty or unreadable answer uses the default, and "Save file?" now defaults to **Yes** (`[Y/n]`). Dangerous commands still default to No.
- Generated files are first kept in `.y2b_unsaved/` inside the workspace, so nothing is lost if saving is declined; the copy is removed once the file is really saved.

## 1.1.0
- **Offline document generation**: ask for a PDF, an editable Word document, a PowerPoint presentation or an Excel workbook in plain language and Y2B saves a real file (`y2b_docs.py`; uses reportlab, python-docx, python-pptx, openpyxl).
- Files can be saved straight into Android's `AGENT WORK` folder; storage permission problems are explained (`termux-setup-storage`). New `--docs-dir` option and `/docs` command; `--doctor` lists the document libraries.
- Safe by design: the model writes Markdown that is parsed as data (no generated code runs), paths are validated, existing files are never overwritten, spreadsheet text is never turned into formulas unless asked, and success is only reported after the file is reopened and verified.
- `install.sh` installs the document packages (skip with `--no-docs`) and copies `y2b_docs.py`. The chat and coding agent still needs no packages.

## 1.0.3
- Web pages are checked before opening (missing CSS/JS files, scripts that use ids that do not exist, unbalanced braces, CDN links that cannot load offline; exact JS syntax check when `node` is installed) and auto-fixed.
- Follow-ups work on the last file: "it won't work, fix it", "add a score counter to it", "open it again in chrome".
- New `/open [page.html]` command.

## 1.0.2
- Fixed the loading spinner repeating line after line on narrow phone screens: each frame now fits the terminal width and redraws in place.

## 1.0.1
- Requests without a file name ("create a web birthday calculator") now work: Y2B picks a file name itself and writes the file.
- Web pages are generated as one self-contained HTML file and can be opened in your phone browser (Chrome etc.) through a local server: "...and open it in chrome".
- Python programs that use `input()` now run live in the terminal instead of failing with EOFError.
- Default workspace is `~/y2b_workspace` when started from inside the Y2B source folder, so generated files never end up in the repo.
- Status card shows real model size.

## 1.0.0
First public release of **Y2B Agent**.

- Model-agnostic: works with any GGUF that llama.cpp can run (uses the model's own chat template through `llama-server`).
- Fast mode: starts `llama-server` once and keeps the model in RAM; replies stream live.
- Works with any OpenAI-compatible local server (`--url`): llama-server, Ollama, LM Studio.
- Slow fallback with `llama-completion` / `llama-cli` and built-in chat templates (ChatML, Llama 3, Gemma, Mistral, Phi-3, Zephyr).
- Auto-fix loop: runs your code, reads the error, asks the model to fix it, and retries.
- Tool-using agent loop (write / run / read / ls) with y/N confirmations.
- Auto-detects models, free RAM (context size) and CPU threads; model picker and `/model` switcher.
- Ignores `<think>` reasoning blocks from reasoning models.
- Persistent memory, voice (termux-api), `/doctor` diagnostics, animated UI.

Made by : Mahzend
