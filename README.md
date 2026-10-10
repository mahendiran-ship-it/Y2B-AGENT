<div align="center">

```
██╗   ██╗██████╗ ██████╗ 
╚██╗ ██╔╝╚════██╗██╔══██╗
 ╚████╔╝  █████╔╝██████╔╝
  ╚██╔╝  ██╔═══╝ ██╔══██╗
   ██║   ███████╗██████╔╝
   ╚═╝   ╚══════╝╚═════╝ 
   A  G  E  N  T
```

### An offline AI coding agent that lives in your terminal

**Any local model. Zero cloud. No dependencies for the agent itself.**

![license](https://img.shields.io/badge/license-MIT-blue)
![python](https://img.shields.io/badge/python-3.8%2B-yellow)
![deps](https://img.shields.io/badge/core%20dependencies-none-brightgreen)
![offline](https://img.shields.io/badge/works-100%25%20offline-purple)
![termux](https://img.shields.io/badge/runs%20on-Termux%20%7C%20Linux%20%7C%20macOS-orange)

</div>

---

Y2B Agent turns a small GGUF model running on your phone (or laptop) into a **real agent**: it writes files, runs them, reads the errors, **fixes its own bugs**, and keeps going - all without internet.

```text
you ❯ create calc.py that adds two numbers from input and run it
Y2B ❯ Here's calc.py:
→ write calc.py (4 lines)   ✓ saved
→ run python calc.py
Traceback (most recent call last): ... NameError ...
🔧 auto-fix 1/3
→ run python calc.py        ✓ works
Y2B ❯ Created calc.py. Auto-fixed in 1 attempt.
  ⚡ 94 tok · 13.2 tok/s
```

## ✨ Features

| | |
|---|---|
| 🧠 **Any model** | Qwen, Llama, Gemma, Phi, Mistral, SmolLM, DeepSeek... anything llama.cpp can load. It uses the model's *own* chat template, so there is nothing to configure per model. |
| ⚡ **Fast** | Starts `llama-server` once and keeps the model in RAM. Replies **stream live** with a tokens/sec readout. |
| 🔧 **Auto-fix loop** | Runs your code, feeds the error back to the model, rewrites, re-runs. Also syntax-checks every Python file it creates. |
| 🤖 **Real agent loop** | Tools: write files, run commands, read files, list folders. Multi-step, with failure recovery. |
| 🔌 **Bring your own server** | `--url` works with llama-server, **Ollama**, **LM Studio** or any OpenAI-compatible endpoint. |
| 📱 **Adapts to your device** | Auto-picks context size from free RAM and CPU threads. Model menu and `/model` switcher. |
| 🛡️ **Safe by default** | Every file write and command asks `y/N`. Dangerous commands always ask. File writes stay inside your workspace. |
| 📄 **Office files, offline** | Say *"make a 5-slide PowerPoint about X"* and get a real `.pptx`. Also **PDF**, editable **Word** (`.docx`) and **Excel** (`.xlsx`). Saved straight into your phone's `AGENT WORK` folder. See [Office documents](#-office-documents-pdf-word-powerpoint-excel). |
| 🧩 **Reasoning models** | `<think>` blocks are hidden automatically. |
| 💾 **Memory** | `remember my name is Sam` - kept between sessions. |
| 🎙️ **Voice** | Optional speech in/out with `termux-api`. |
| 🎨 **Pretty** | Gradient banner, animated spinner, typing effect, status card. |

## 🚀 Quick start (Termux)

```bash
# 1. get the code
pkg install -y git
git clone https://github.com/mahendiran-ship-it/Y2B-AGENT
cd Y2B-AGENT

# 2. install (installs python + llama-cpp, creates the `y2b` command)
bash install.sh

# 3. download any GGUF model, for example a small coder model
mkdir -p ~/models && cd ~/models
curl -L -O https://huggingface.co/Qwen/Qwen2.5-Coder-1.5B-Instruct-GGUF/resolve/main/qwen2.5-coder-1.5b-instruct-q4_k_m.gguf
#   (if a link ever changes, grab the .gguf from the model's "Files" page)

# 4. run
y2b
```

No installer? Just run the file: `python y2b_agent.py` (the document tools also need `y2b_docs.py` next to it and `pip install -r requirements.txt`).

**Other Linux / macOS:** install [llama.cpp](https://github.com/ggml-org/llama.cpp) so `llama-server` is on your PATH, put a `.gguf` in `~/models`, then `python y2b_agent.py`.

## 📄 Office documents (PDF, Word, PowerPoint, Excel)

Ask in plain language and Y2B writes the content with your local model, builds a **real file** with
[reportlab](https://pypi.org/project/reportlab/), [python-docx](https://pypi.org/project/python-docx/),
[python-pptx](https://pypi.org/project/python-pptx/) or [openpyxl](https://pypi.org/project/openpyxl/),
reopens it to check it is valid, and tells you the path it was **actually** saved to. Nothing needs internet once
the four packages are installed. The model only writes simple Markdown that Y2B parses as data; no model-written
code is ever executed to make a document.

| Format | You get |
|---|---|
| **PDF** | title, headings, paragraphs, bullet/numbered lists, tables, page breaks, automatic wrapping and page numbers |
| **Word** `.docx` | editable document: title, headings, bullets, numbered lists (each list restarts at 1), tables with a header row |
| **PowerPoint** `.pptx` | editable 16:9 deck: title slide, one slide per section, bullets, tables; long lists continue on extra slides; asks the model for the slide count you request |
| **Excel** `.xlsx` | one or more sheets, bold header row, frozen header, filters, sensible column widths, numbers stored as numbers, basic formulas (`SUM`, `AVERAGE`, ...) when you ask for totals |

```text
Create a PDF explaining Wireshark and save it in AGENT WORK.
Create an editable Word document titled Payment QR with the content I provide.
Make a 5-slide PowerPoint presentation about marine pollution.
Create an Excel spreadsheet containing student names, marks, and total scores.
Create a professional project report in both PDF and Word formats.
Save a PDF called Y2B_Test.pdf in AGENT WORK.
```

Y2B asks a question only when it really needs one (for example *"with the content I provide"* makes it ask you to paste
the text, finishing with a line that contains only `:wq`, the same as `/write`).

### Install (Termux)

```bash
pkg install -y git
git clone https://github.com/mahendiran-ship-it/Y2B-AGENT && cd Y2B-AGENT
bash install.sh            # also installs reportlab, python-docx, python-pptx, openpyxl
```

`install.sh` runs `pkg install python-pip python-pillow python-lxml` first (prebuilt, so pip does not have to compile
anything) and then `pip install -r requirements.txt`. The packages need internet **once**. Skip them with
`bash install.sh --no-docs`. Check the result any time with `y2b --doctor` or `/docs` inside Y2B.

> **About Pillow.** Y2B does not use images and `requirements.txt` does not list Pillow, but `reportlab` and
> `python-pptx` themselves require it (without it `python-pptx` cannot even be imported), so pip installs it as their dependency.

### Saving to the `AGENT WORK` folder (Android storage permission)

Run this **once** in Termux, tap **Allow**, then restart Termux:

```bash
termux-setup-storage
```

Then create a folder called `AGENT WORK` in your phone's internal storage (or let Y2B create it). Y2B saves there when you say
*"... in AGENT WORK"*, or give the full path `/storage/emulated/0/AGENT WORK/` (spaces are fine, no quotes needed).

Where files go:

| You say | Saved in |
|---|---|
| `... in AGENT WORK` | `/storage/emulated/0/AGENT WORK/` |
| `... in /some/folder` or `... in ~/folder` | that folder, if it is allowed (below) |
| `... in the workspace` | your workspace folder |
| nothing | `AGENT WORK` when storage access works, otherwise `<workspace>/documents` (and it tells you why) |

Allowed folders: the workspace, Android shared storage (`/storage/emulated/0`, `/sdcard`, `~/storage/shared`) and the folder
from `--docs-dir DIR` (which also becomes the default). Anything else (for example `/etc`) is refused with a suggestion.
Existing files are **never overwritten**: a second `report.pdf` is saved as `report (1).pdf`. Generated files stay out of your
source code folders unless you name one.

Every file is shown (first lines) and **asked about** before saving (`Save PDF file?`), like every other write. With `--auto` the
workspace, `AGENT WORK` and `--docs-dir` are saved without asking, while other shared-storage folders still ask. The code
file tool (`[write:]`, `/write`) is unchanged and still refuses anything outside the workspace.

### If something goes wrong

| Message | Fix |
|---|---|
| `Missing Python package ...` | `pip install reportlab python-docx python-pptx openpyxl` (internet needed once) |
| `Android storage is not accessible ...` | run `termux-setup-storage`, tap **Allow**, restart Termux. Or say "save it in the workspace" |
| `... is outside the folders Y2B may save documents to` | use `AGENT WORK`, the workspace, or start Y2B with `--docs-dir DIR` |
| `No permission to write to ...` / `out of free storage` | pick another folder / free some space |
| `The model returned no content` | try again, or give the text yourself ("with the content I provide") |
| a spreadsheet request fails with "needs a table" | the model answered with prose; ask again, naming the columns |

Y2B only says **Saved** after the file exists, is non-empty and has been reopened with its own library. Any failure is reported
as a failure and leaves no half-written file behind.

### Known limitations

- **Unicode in PDFs.** PDFs use a Unicode TrueType font if one is installed (DejaVu Sans, Liberation Sans, Android's Noto Sans/Roboto
  are tried automatically; set `Y2B_PDF_FONT=/path/to/Font-Regular.ttf` to choose one). Without one, only Western European
  characters (Latin-1 plus common punctuation such as `€ “ ”`) are drawn; anything else is shown as `?` and Y2B warns you.
  Scripts that need shaping (Tamil, Hindi/Devanagari, Arabic, ...) are **not** supported in PDFs even with a font. Use the Word,
  PowerPoint or Excel format for those, since they store the text as Unicode and the viewer app draws it.
- **No images** in any format yet (Markdown images are left out, with a warning).
- **Slide count is best effort**: Y2B asks the model for the number you request, retries once, then saves what it got and tells you the real count.
- **Length is limited by the model and `--ctx`**: a small on-phone model will write short documents. Long, factual or specialised content needs a bigger model, or give your own text.
- Excel formulas are limited to simple same-sheet ones; anything else (links, external data, unknown functions) is stored as plain text on purpose.
- **Not yet verified on a real Android phone.** Everything above is covered by automated tests on Linux (Android storage is
  simulated). Android/Termux behaviour, including whether `python-pillow` / `python-lxml` install from `pkg`, still needs
  your confirmation: see the Termux checklist below.

### Termux verification checklist

```bash
bash install.sh && termux-setup-storage     # tap Allow, restart Termux
y2b --doctor                                # all four libraries listed, "save to ... AGENT WORK [ready]"
y2b                                         # then, one at a time:
#   Save a PDF called Y2B_Test.pdf in AGENT WORK.
#   Make a 3-slide PowerPoint presentation about the moon.
#   Create an Excel spreadsheet with 3 students, their marks and totals.
#   Create an editable Word document titled Test with the content I provide.
```

Open the files in the phone's Files / Word / Excel / PowerPoint / Google Docs apps and confirm they open and look right.

## 🧠 Choosing a model

Y2B finds `.gguf` files in the current folder, `~`, `~/models`, `~/storage/downloads` and similar. With more than one it shows a menu; `/model 2` switches live.

Rough guidance (smaller = faster, bigger = smarter; tune to your free RAM):

| Free RAM | Try |
|---|---|
| ~1-2 GB | 0.5B-1.5B models (Q4) |
| ~3-4 GB | 3B models (Q4) |
| 6 GB+ | 7B-8B models (Q4) |

Coder-tuned instruct models (e.g. *Qwen2.5-Coder*) write noticeably better code than general chat models of the same size. Y2B is designed to work with any instruct/chat GGUF, but results depend on the model.

## 💬 Things to try

```text
hi
create hello.py that prints hello and run it
create a todo.py command line todo app and test it
make a 5-slide PowerPoint presentation about marine pollution
run sl command in my termux
read hello.py and add comments
remember my name is Sam
```

## ⌨️ Commands

| Command | What it does |
|---|---|
| `/help` | list commands |
| `/models`, `/model <n>` | list / switch models |
| `/info`, `/doctor`, `/ctx` | status and diagnostics |
| `/ls` `/cat <f>` `/write <f>` `/rm <f>` `/cd <d>` `/pwd` | files |
| `/run <cmd>` or `!<cmd>` | run a shell command |
| `/auto` | toggle auto-approve (use carefully) |
| `/fix <n>` | auto-fix attempts (0 = off) |
| `/steps <n>` | max tool steps per request |
| `/temp <0-1>` | creativity |
| `/docs` | PDF/Word/PowerPoint/Excel status and where files are saved |
| `/mem`, `/forget`, `/clear` | memory and chat reset |
| `/voice`, `/listen` | speech out / in (termux-api) |
| `/cls`, `/exit` | clear screen / quit |

## ⚙️ Options

```text
y2b [--model FILE] [--pick] [--url URL] [--model-name N] [--api-key K]
    [--llama-server PATH] [--llama-cli PATH] [--port P]
    [--ctx N] [--gen N] [--temp T] [--threads N]
    [--work DIR] [--docs-dir DIR] [--auto] [--steps N] [--fix N] [--no-anim] [--no-attach]
    [--doctor] [--version]
```

Examples:

```bash
y2b --model ~/models/llama-3.2-3b-instruct-q4_k_m.gguf   # specific model
y2b --ctx 2048 --gen 512                                  # tighter memory budget
y2b --url http://127.0.0.1:11434 --model-name qwen2.5-coder:1.5b   # use Ollama
y2b --fix 5                                               # more auto-fix attempts
```

By default the **workspace is the folder you start Y2B in** (your home folder if you just open Termux).

## 🔍 How it works

```text
            you ❯ "create app.py ... and run it"
                       │
        ┌──────────────▼───────────────┐
        │  Y2B Agent (y2b_agent.py)    │  fast paths: greetings, PDF/Word/PPT/Excel, "run <cmd>",
        │  agent loop · auto-fix loop  │  file creation.  tool tags: [write] [run] [read] [ls]
        └──────────────┬───────────────┘
                       │ streaming chat API (OpenAI-compatible)
        ┌──────────────▼───────────────┐
        │ llama-server  (or Ollama...) │  model stays loaded in RAM, applies the
        │   any GGUF model             │  model's own chat template
        └──────────────────────────────┘
   fallback: llama-completion / llama-cli with built-in templates (slower)
```

1. **Backend selection** - uses `--url` if given, else attaches to a server already running on `:8080` / Ollama `:11434`, else starts `llama-server` for your model, else falls back to `llama-completion` / `llama-cli`.
2. **Chat template** - handled by the server, so a new model "just works". The CLI fallback ships templates for ChatML, Llama 3, Gemma, Mistral, Phi-3 and Zephyr.
3. **Auto-fix** - after running a file, a non-zero exit code sends the error back to the model for a corrected file, up to `--fix` times.

## 🧪 Tests

No model needed - the tests use a fake OpenAI-compatible server:

```bash
python -m unittest discover -s tests -v
```

The document tests need the four packages from `requirements.txt` (they are skipped if a package is missing). They write only to
temporary folders; Android storage is simulated, so they never touch a real `/storage/emulated/0`.

## 🛠️ Troubleshooting

| Problem | Fix |
|---|---|
| `llama.cpp not found` | `pkg install llama-cpp`, or `--llama-server /path/to/llama-server`, or `--url ...` |
| `no .gguf model found` | put a model in `~/models` or pass `--model` |
| Out of memory / killed | use a smaller or lower-quant model, or `--ctx 1024` |
| Slow replies | make sure it says `llama-server (fast)` in the status card; try fewer `--threads` or a smaller model |
| `exceeds the available context` | `/clear`, or restart with a larger `--ctx` |
| Model refuses or rambles | try a coder/instruct model, `/temp 0.1`, and say clearly what the file should do |
| Document / storage problems | see [If something goes wrong](#if-something-goes-wrong) |
| Anything else | run `y2b --doctor` and check `~/.y2b/server.log` |

A leftover server after a crash? `pkill llama-server`.

## 🤝 Contributing

PRs welcome - see [CONTRIBUTING.md](CONTRIBUTING.md). Good first issues: more chat templates, more instant commands, a diff view before overwriting files.

## 📄 License

MIT - see [LICENSE](LICENSE).

---

<div align="center">

```
███╗   ███╗ █████╗ ██╗  ██╗███████╗███████╗███╗   ██╗██████╗
████╗ ████║██╔══██╗██║  ██║╚══███╔╝██╔════╝████╗  ██║██╔══██╗
██╔████╔██║███████║███████║  ███╔╝ █████╗  ██╔██╗ ██║██║  ██║
██║╚██╔╝██║██╔══██║██╔══██║ ███╔╝  ██╔══╝  ██║╚██╗██║██║  ██║
██║ ╚═╝ ██║██║  ██║██║  ██║███████╗███████╗██║ ╚████║██████╔╝
╚═╝     ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝╚══════╝╚══════╝╚═╝  ╚═══╝╚═════╝
```

**✦ Made By : MAHZEND ✦**

</div>
