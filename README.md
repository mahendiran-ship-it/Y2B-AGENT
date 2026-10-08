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

**Any local model. Zero cloud. Zero dependencies.**

![license](https://img.shields.io/badge/license-MIT-blue)
![python](https://img.shields.io/badge/python-3.8%2B-yellow)
![deps](https://img.shields.io/badge/dependencies-none-brightgreen)
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

No installer? Just run the file: `python y2b_agent.py`

**Other Linux / macOS:** install [llama.cpp](https://github.com/ggml-org/llama.cpp) so `llama-server` is on your PATH, put a `.gguf` in `~/models`, then `python y2b_agent.py`.

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
| `/mem`, `/forget`, `/clear` | memory and chat reset |
| `/voice`, `/listen` | speech out / in (termux-api) |
| `/cls`, `/exit` | clear screen / quit |

## ⚙️ Options

```text
y2b [--model FILE] [--pick] [--url URL] [--model-name N] [--api-key K]
    [--llama-server PATH] [--llama-cli PATH] [--port P]
    [--ctx N] [--gen N] [--temp T] [--threads N]
    [--work DIR] [--auto] [--steps N] [--fix N] [--no-anim] [--no-attach]
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
        │  Y2B Agent (y2b_agent.py)    │  fast paths: greetings, "run <cmd>", file creation
        │  agent loop · auto-fix loop  │  tool tags: [write] [run] [read] [ls]
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

## 🛠️ Troubleshooting

| Problem | Fix |
|---|---|
| `llama.cpp not found` | `pkg install llama-cpp`, or `--llama-server /path/to/llama-server`, or `--url ...` |
| `no .gguf model found` | put a model in `~/models` or pass `--model` |
| Out of memory / killed | use a smaller or lower-quant model, or `--ctx 1024` |
| Slow replies | make sure it says `llama-server (fast)` in the status card; try fewer `--threads` or a smaller model |
| `exceeds the available context` | `/clear`, or restart with a larger `--ctx` |
| Model refuses or rambles | try a coder/instruct model, `/temp 0.1`, and say clearly what the file should do |
| Anything else | run `y2b --doctor` and check `~/.y2b/server.log` |

A leftover server after a crash? `pkill llama-server`.

## 🤝 Contributing

PRs welcome - see [CONTRIBUTING.md](CONTRIBUTING.md). Good first issues: more chat templates, more instant commands, a diff view before overwriting files.

## 📄 License

MIT - see [LICENSE](LICENSE).

---

<div align="center">

**✦ Made by : Mahzend**

</div>
