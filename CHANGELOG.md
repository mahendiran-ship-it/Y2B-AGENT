# Changelog

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
