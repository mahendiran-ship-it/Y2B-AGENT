#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Y2B Agent  -  an offline, model-agnostic AI coding agent for Termux (and any Linux).

    Made by : Mahzend

* Works with ANY GGUF model that llama.cpp can run (Qwen, Llama, Gemma, Phi, Mistral, ...)
  because it talks to llama-server's chat endpoint, which applies the model's own chat template.
* Also works with any OpenAI-compatible local server (llama-server, Ollama, LM Studio, ...).
* Falls back to llama-completion / llama-cli (slower, reloads the model every reply).
* Real streaming, a tool-using agent loop, and an auto-fix loop for broken code.
* Python standard library only. No pip install needed.

Run:  python y2b_agent.py          (or just `y2b` after running install.sh)
Help: python y2b_agent.py --help
"""
from __future__ import annotations

import argparse
import atexit
import glob
import json
import os
import random
import re
import shutil
import socket
import subprocess
import sys
import tempfile
import threading
import time
import urllib.error
import urllib.parse
import urllib.request

__version__ = "1.0.3"
AUTHOR = "Mahzend"
APP = "Y2B Agent"

# ═══════════════════════════ terminal styling ═══════════════════════════
USE_COLOR = sys.stdout.isatty() and os.environ.get("NO_COLOR") is None
ANIM = USE_COLOR


def c(code, s):
    return "\033[%sm%s\033[0m" % (code, s) if USE_COLOR else s


CY = lambda s: c("96", s)
GR = lambda s: c("92", s)
YE = lambda s: c("93", s)
RD = lambda s: c("91", s)
MG = lambda s: c("95", s)
DM = lambda s: c("90", s)
BD = lambda s: c("1", s)


def g256(n, s):
    return "\033[38;5;%dm%s\033[0m" % (n, s) if USE_COLOR else s


BANNER_LINES = [
    r"██╗   ██╗██████╗ ██████╗ ",
    r"╚██╗ ██╔╝╚════██╗██╔══██╗",
    r" ╚████╔╝  █████╔╝██████╔╝",
    r"  ╚██╔╝  ██╔═══╝ ██╔══██╗",
    r"   ██║   ███████╗██████╔╝",
    r"   ╚═╝   ╚══════╝╚═════╝ ",
]
GRADIENT = [51, 45, 39, 33, 63, 99]
BOT = "Y2B ❯"
MADE_BY = "Made by : " + AUTHOR


def clear_screen():
    if USE_COLOR:
        sys.stdout.write("\033[2J\033[3J\033[H")
        sys.stdout.flush()


def typewrite(text, cap=1.6):
    """Typing animation for short canned lines (instant if not a terminal)."""
    if not ANIM or not text:
        sys.stdout.write(text)
        sys.stdout.flush()
        return
    delay = min(0.012, cap / max(1, len(text)))
    try:
        for i, ch in enumerate(text):
            sys.stdout.write(ch)
            sys.stdout.flush()
            time.sleep(delay * 4 if ch in ".,!?\n" else delay)
    except KeyboardInterrupt:
        sys.stdout.write(text[i + 1:])
        sys.stdout.flush()


def say(text, err=False):
    lab = (RD if err else GR)(BD(BOT))
    sys.stdout.write("\n" + lab + " ")
    sys.stdout.flush()
    typewrite(text)
    sys.stdout.write("\n\n")
    sys.stdout.flush()


def prompt_str():
    if not USE_COLOR:
        return "you> "
    return "\001\033[96;1m\002you ❯ \001\033[0m\002"


def card(lines, width=None):
    cols = shutil.get_terminal_size((50, 20)).columns
    w = width or max(26, min(cols - 2, 48))
    out = [DM("╭" + "─" * (w - 2) + "╮")]
    for color, text in lines:
        text = text if len(text) <= w - 4 else text[: w - 5] + "…"
        out.append(DM("│ ") + color(text.ljust(w - 4)) + DM(" │"))
    out.append(DM("╰" + "─" * (w - 2) + "╯"))
    return "\n".join(out)


def show_banner(compact=False):
    clear_screen()
    cols = shutil.get_terminal_size((60, 20)).columns
    if compact or cols < 30:
        print(CY(BD(APP.upper())) + DM("  ·  " + MADE_BY))
        return
    print()
    for i, ln in enumerate(BANNER_LINES):
        print("  " + g256(GRADIENT[i % len(GRADIENT)], ln))
        if ANIM:
            time.sleep(0.05)
    print("  " + g256(45, BD("A  G  E  N  T")) + DM("   ·   offline   ·   any model"))
    print()


class Spinner:
    """Animated 'working' indicator with a live info string (tokens/sec etc.)."""
    FR = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"
    MSGS = ["thinking", "reasoning", "working", "almost there", "still going"]

    def __init__(self, text="thinking"):
        self.text, self.info, self.active = text, "", False
        self._ev, self._t, self.t0 = threading.Event(), None, 0.0

    def start(self):
        if self.active:
            return
        self.active, self.t0 = True, time.time()
        self._ev.clear()
        if ANIM:
            sys.stdout.write("\033[?25l")
            sys.stdout.flush()
            self._t = threading.Thread(target=self._run, daemon=True)
            self._t.start()
        else:
            print("(%s...)" % self.text)

    def frame(self, i, cols=None):
        """One spinner frame, guaranteed to fit the terminal width (so it never wraps on a phone)."""
        cols = cols or shutil.get_terminal_size((40, 20)).columns
        avail = max(14, cols - 2)
        pos = i % 8
        p = pos if pos < 5 else 8 - pos
        bar = "".join("▰" if j in (p, p - 1) else "▱" for j in range(5))
        secs = int(time.time() - self.t0)
        ss = "%ds" % secs
        label = self.text if secs < 8 else "%s (%s)" % (self.MSGS[(secs // 8) % len(self.MSGS)], self.text)
        info = self.info

        def plain(lab, inf):
            return " %s %s %s %s%s" % (self.FR[i % 10], lab, bar, ss, ("  " + inf) if inf else "")
        if len(plain(label, info)) > avail:
            info = ""
        if len(plain(label, "")) > avail:
            room = avail - len(plain("", "")) - 1
            label = label[:max(3, room)].rstrip() + "…"
        txt = plain(label, info)
        colored = " %s %s %s %s%s" % (g256(45, self.FR[i % 10]), CY(label), g256(39, bar), DM(ss),
                                      DM("  " + info) if info else "")
        return txt, colored

    def _run(self):
        i = 0
        while not self._ev.is_set():
            sys.stdout.write("\r" + self.frame(i)[1] + "\033[K")
            sys.stdout.flush()
            i += 1
            time.sleep(0.09)

    def stop(self):
        if not self.active:
            return
        self.active = False
        self._ev.set()
        if self._t:
            self._t.join()
            self._t = None
            sys.stdout.write("\r\033[K\033[?25h")
            sys.stdout.flush()

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, *a):
        self.stop()


# ═══════════════════════════ paths / config ═══════════════════════════
HOME = os.path.expanduser("~")
STATE_DIR = os.environ.get("Y2B_HOME", os.path.join(HOME, ".y2b"))
MEM_FILE = os.path.join(STATE_DIR, "memory.json")
CONF_FILE = os.path.join(STATE_DIR, "config.json")
LOG_FILE = os.path.join(STATE_DIR, "server.log")
os.makedirs(STATE_DIR, exist_ok=True)

_legacy = os.path.join(HOME, ".jarvis", "memory.json")  # migrate memory from the earlier prototype
if os.path.exists(_legacy) and not os.path.exists(MEM_FILE):
    try:
        shutil.copy(_legacy, MEM_FILE)
    except Exception:
        pass


def load_json(path, default):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default


def save_json(path, data):
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        print(RD("(could not save %s: %s)" % (path, e)))


# ═══════════════════════════ system probing ═══════════════════════════
def mem_available_mb():
    try:
        with open("/proc/meminfo") as f:
            for ln in f:
                if ln.startswith("MemAvailable:"):
                    return int(ln.split()[1]) // 1024
    except Exception:
        pass
    return None


def cpu_threads():
    n = os.cpu_count() or 4
    return max(2, min(8, n // 2 if n > 4 else n))


def find_bin(names):
    for n in names:
        p = shutil.which(n)
        if p:
            return p
    for d in (HOME + "/llama.cpp/build/bin", HOME + "/llama.cpp", "/usr/local/bin", "/opt/homebrew/bin"):
        for n in names:
            p = os.path.join(d, n)
            if os.path.isfile(p) and os.access(p, os.X_OK):
                return p
    return None


PYTHON = shutil.which("python") or shutil.which("python3") or sys.executable
RUNNERS = {".py": PYTHON, ".sh": "bash", ".js": "node"}

# ═══════════════════════════ models ═══════════════════════════
MODEL_DIRS = [".", "~", "~/models", "~/model", "~/llama.cpp/models", "~/storage/downloads",
              "~/storage/shared", "~/storage/shared/Download", "~/storage/shared/Downloads",
              "~/Downloads", "~/Download"]


def discover_models(extra_dirs=()):
    found, seen = [], set()
    for d in list(extra_dirs) + MODEL_DIRS:
        d = os.path.abspath(os.path.expanduser(d))
        for p in glob.glob(os.path.join(d, "*.gguf")):
            rp = os.path.realpath(p)
            name = os.path.basename(p).lower()
            if rp in seen or "mmproj" in name:
                continue
            if "-of-" in name and "00001-of-" not in name:  # only first shard of split models
                continue
            seen.add(rp)
            found.append(p)
    return sorted(found, key=lambda x: os.path.basename(x).lower())


FAMILIES = [("qwen", "chatml"), ("smollm", "chatml"), ("deepseek", "chatml"), ("granite", "chatml"),
            ("lfm", "chatml"), ("phi-4", "chatml"), ("llama-3", "llama3"), ("llama3", "llama3"),
            ("gemma", "gemma"), ("mistral", "mistral"), ("mixtral", "mistral"),
            ("phi-3", "phi3"), ("phi3", "phi3"), ("tinyllama", "zephyr"), ("zephyr", "zephyr")]


def model_info(path):
    name = os.path.basename(path).lower()
    fam, tpl = "generic", "chatml"
    for key, t in FAMILIES:
        if key in name:
            fam, tpl = key, t
            break
    m = re.search(r"(?<![\d.])(\d+(?:\.\d+)?)\s*b(?![a-z])", name)
    q = re.search(r"((?:i?q\d[\w]*)|f16|bf16)", name)
    try:
        size_mb = os.path.getsize(path) // (1024 * 1024)
    except Exception:
        size_mb = 0
    return {"name": os.path.basename(path), "family": fam, "template": tpl,
            "params_b": float(m.group(1)) if m else None,
            "quant": q.group(1).upper() if q else "?", "size_mb": size_mb}


def auto_ctx(model_mb):
    """Pick a context size that fits free RAM after loading the model."""
    avail = mem_available_mb()
    if avail is None:
        return 2048
    spare = avail - model_mb * 1.1
    if spare < 300:
        return 1024
    if spare < 700:
        return 2048
    if spare < 1500:
        return 4096
    return 8192


def format_prompt(tpl, messages):
    """Chat-template fallback for the CLI backend. Returns (prompt, stop_strings)."""
    msgs = [dict(m) for m in messages]
    if tpl in ("gemma", "mistral") and msgs and msgs[0]["role"] == "system":
        sysm = msgs.pop(0)["content"]
        if msgs and msgs[0]["role"] == "user":
            msgs[0]["content"] = sysm + "\n\n" + msgs[0]["content"]
    if tpl == "llama3":
        p = "".join("<|start_header_id|>%s<|end_header_id|>\n\n%s<|eot_id|>" % (m["role"], m["content"]) for m in msgs)
        return p + "<|start_header_id|>assistant<|end_header_id|>\n\n", ["<|eot_id|>"]
    if tpl == "gemma":
        p = "".join("<start_of_turn>%s\n%s<end_of_turn>\n" % ("model" if m["role"] == "assistant" else "user", m["content"]) for m in msgs)
        return p + "<start_of_turn>model\n", ["<end_of_turn>"]
    if tpl == "mistral":
        p = ""
        for m in msgs:
            p += ("[INST] %s [/INST]" % m["content"]) if m["role"] == "user" else (" %s</s>" % m["content"])
        return p, ["</s>"]
    if tpl == "phi3":
        p = "".join("<|%s|>\n%s<|end|>\n" % (m["role"], m["content"]) for m in msgs)
        return p + "<|assistant|>\n", ["<|end|>"]
    if tpl == "zephyr":
        p = "".join("<|%s|>\n%s</s>\n" % (m["role"], m["content"]) for m in msgs)
        return p + "<|assistant|>\n", ["</s>"]
    p = "".join("<|im_start|>%s\n%s<|im_end|>\n" % (m["role"], m["content"]) for m in msgs)  # chatml
    return p + "<|im_start|>assistant\n", ["<|im_end|>"]


# ═══════════════════════════ backends ═══════════════════════════
class BackendError(Exception):
    def __init__(self, msg, code=None):
        super().__init__(msg)
        self.code = code


OPENER = urllib.request.build_opener(urllib.request.ProxyHandler({}))  # never proxy local servers


class OpenAIBackend:
    """Any OpenAI-compatible server: llama-server, Ollama, LM Studio, vLLM, ..."""
    kind = "server"
    owned = False

    def __init__(self, url, model_name=None, api_key=None):
        url = url.rstrip("/")
        if url.endswith("/v1"):
            self.api, self.root = url, url[:-3]
        else:
            self.api, self.root = url + "/v1", url
        self.model_name = model_name or "default"
        self.api_key = api_key
        self.label = "external server"

    def _open(self, url, body=None, timeout=10):
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = "Bearer " + self.api_key
        data = json.dumps(body).encode() if body is not None else None
        return OPENER.open(urllib.request.Request(url, data=data, headers=headers), timeout=timeout)

    def healthy(self):
        try:
            with self._open(self.root + "/health", timeout=1.5) as r:
                return r.status == 200
        except urllib.error.HTTPError as e:
            if e.code == 503:  # llama-server: still loading
                return False
        except Exception:
            pass
        try:
            with self._open(self.api + "/models", timeout=1.5) as r:
                return r.status == 200
        except Exception:
            return False

    def detect_model_name(self):
        try:
            with self._open(self.api + "/models", timeout=3) as r:
                data = json.loads(r.read().decode("utf-8", "ignore"))
            ids = [m.get("id") for m in data.get("data", []) if m.get("id")]
            if ids and self.model_name == "default":
                self.model_name = ids[0]
        except Exception:
            pass

    def start(self, on_wait=None):
        if not self.healthy():
            raise BackendError("Cannot reach server at " + self.root)
        self.detect_model_name()

    def stop(self):
        pass

    def describe(self):
        return "%s (%s)" % (self.label, self.model_name)

    def stream(self, messages, max_tokens, temp):
        body = {"model": self.model_name, "messages": messages, "stream": True,
                "temperature": temp, "max_tokens": max_tokens, "cache_prompt": True}
        try:
            resp = self._open(self.api + "/chat/completions", body, timeout=900)
        except urllib.error.HTTPError as e:
            raw = e.read()[:400].decode("utf-8", "ignore")
            raise BackendError("HTTP %d: %s" % (e.code, raw), code=e.code)
        except Exception as e:
            raise BackendError("Cannot reach model server: %s" % e)
        try:
            for raw in resp:
                line = raw.decode("utf-8", "ignore").strip()
                if not line.startswith("data:"):
                    continue
                data = line[5:].strip()
                if data == "[DONE]":
                    break
                try:
                    obj = json.loads(data)
                except ValueError:
                    continue
                delta = ((obj.get("choices") or [{}])[0].get("delta")) or {}
                txt = delta.get("content")
                if txt:
                    yield txt
        finally:
            resp.close()


class ServerBackend(OpenAIBackend):
    """Starts and owns a local llama-server so the model stays loaded in RAM (fast replies)."""
    owned = True

    def __init__(self, binary, model, ctx, threads, port=None):
        self.binary, self.model, self.ctx, self.threads = binary, model, ctx, threads
        self.port = port or self._free_port()
        super().__init__("http://127.0.0.1:%d" % self.port, model_name=os.path.basename(model))
        self.label = "llama-server (fast)"
        self.proc = None

    @staticmethod
    def _free_port():
        s = socket.socket()
        s.bind(("127.0.0.1", 0))
        p = s.getsockname()[1]
        s.close()
        return p

    def _help(self):
        try:
            r = subprocess.run([self.binary, "--help"], stdin=subprocess.DEVNULL,
                               capture_output=True, text=True, timeout=30)
            return (r.stdout or "") + (r.stderr or "")
        except Exception:
            return ""

    def start(self, on_wait=None):
        h = self._help()
        cmd = [self.binary, "-m", self.model, "-c", str(self.ctx), "-t", str(self.threads),
               "--host", "127.0.0.1", "--port", str(self.port)]
        if "--parallel" in h or "-np," in h:
            cmd += ["-np", "1"]  # one slot, otherwise context is split between slots
        if "--no-webui" in h:
            cmd += ["--no-webui"]
        logf = open(LOG_FILE, "w")
        self.proc = subprocess.Popen(cmd, stdin=subprocess.DEVNULL, stdout=logf, stderr=subprocess.STDOUT)
        atexit.register(self.stop)
        t0 = time.time()
        while time.time() - t0 < 600:
            if self.proc.poll() is not None:
                raise BackendError("llama-server exited early:\n" + self._log_tail())
            if self.healthy():
                return
            if on_wait:
                on_wait(time.time() - t0)
            time.sleep(0.4)
        raise BackendError("llama-server did not become ready in 10 minutes.\n" + self._log_tail())

    def _log_tail(self, n=8):
        try:
            with open(LOG_FILE, errors="ignore") as f:
                return "".join(f.readlines()[-n:])
        except Exception:
            return ""

    def stop(self):
        p, self.proc = self.proc, None
        if p and p.poll() is None:
            p.terminate()
            try:
                p.wait(timeout=5)
            except Exception:
                p.kill()


class CliBackend:
    """Fallback: one-shot llama-completion / llama-cli per reply (slow: reloads the model each time)."""
    kind = "cli"
    owned = True

    def __init__(self, binary, model, ctx, threads, template):
        self.binary, self.model, self.ctx, self.threads, self.template = binary, model, ctx, threads, template
        self.label = "llama-cli (slow mode)"
        self._help_txt = None

    def start(self, on_wait=None):
        if not os.path.exists(self.binary):
            raise BackendError("binary not found: " + self.binary)

    def stop(self):
        pass

    def describe(self):
        return "%s (%s)" % (self.label, os.path.basename(self.model))

    def _supports(self, flag):
        if self._help_txt is None:
            try:
                r = subprocess.run([self.binary, "--help"], stdin=subprocess.DEVNULL,
                                   capture_output=True, text=True, timeout=30)
                self._help_txt = (r.stdout or "") + (r.stderr or "")
            except Exception:
                self._help_txt = ""
        return flag in self._help_txt

    def _cmd(self, pf, max_tokens, temp):
        cmd = [self.binary, "-m", self.model, "-c", str(self.ctx), "-n", str(max_tokens),
               "-f", pf, "-t", str(self.threads), "--temp", str(temp)]
        for flag in ("-no-cnv", "--single-turn", "--no-display-prompt", "--simple-io", "--no-warmup"):
            if self._supports(flag):
                cmd.append(flag)
        return cmd

    def stream(self, messages, max_tokens, temp):
        prompt, stops = format_prompt(self.template, messages)
        with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False, encoding="utf-8") as f:
            f.write(prompt)
            pf = f.name
        proc = None
        stop_re = re.compile("|".join(re.escape(s) for s in stops + ["[end of text]"]) + r"|(?m:^>\s*$)")
        try:
            proc = subprocess.Popen(self._cmd(pf, max_tokens, temp), stdin=subprocess.DEVNULL,
                                    stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
            buf, t0, fd = b"", time.time(), proc.stdout.fileno()
            while time.time() - t0 < 900:
                chunk = os.read(fd, 4096)
                if not chunk:
                    break
                buf += chunk
                text = buf.decode("utf-8", "ignore")
                body = text[len(prompt):] if text.startswith(prompt) else text
                if stop_re.search(body) and re.sub(r">|\s", "", body):
                    break
                if body.count(">") > 6 and not re.sub(r">|\s|Exiting\.\.\.", "", body):
                    raise BackendError("llama-cli went into interactive mode. Use llama-server or "
                                       "llama-completion (pkg install llama-cpp) or pass --llama-cli.")
            text = buf.decode("utf-8", "ignore")
            if text.startswith(prompt):
                text = text[len(prompt):]
            m = stop_re.search(text)
            if m:
                text = text[:m.start()]
            text = text.replace("Exiting...", "").strip()
            if text:
                yield text
        finally:
            if proc is not None:
                try:
                    proc.kill()
                    proc.wait(timeout=5)
                except Exception:
                    pass
            try:
                os.unlink(pf)
            except Exception:
                pass


class LLM:
    """Thin wrapper: shared settings + graceful handling of templates that reject a system role."""

    def __init__(self, backend, ctx, gen, temp):
        self.backend, self.ctx, self.gen, self.temp = backend, ctx, gen, temp
        self.merge_system = False

    @staticmethod
    def _merge(messages):
        msgs = [dict(m) for m in messages]
        if len(msgs) > 1 and msgs[0]["role"] == "system" and msgs[1]["role"] == "user":
            msgs[1]["content"] = msgs[0]["content"] + "\n\n" + msgs[1]["content"]
            msgs.pop(0)
        return msgs

    def stream(self, messages):
        msgs = self._merge(messages) if self.merge_system else messages
        got = False
        try:
            for ch in self.backend.stream(msgs, self.gen, self.temp):
                got = True
                yield ch
        except BackendError as e:
            if not got and not self.merge_system and e.code in (400, 500) and "context" not in str(e).lower():
                self.merge_system = True  # some chat templates (Gemma, Mistral...) refuse a system role
                for ch in self.stream(messages):
                    yield ch
                return
            if "context" in str(e).lower() or "exceed" in str(e).lower():
                raise BackendError("The conversation no longer fits the context window. "
                                   "Type /clear or start with a bigger --ctx.")
            raise


# ═══════════════════════════ text helpers ═══════════════════════════
THINK_RE = re.compile(r"<think>.*?(?:</think>|\Z)", re.S)


def strip_think(s):
    return THINK_RE.sub("", s)


TAG_WRITE = re.compile(r"\[write:([^\]\n]+)\]\n?(.*?)(?:\[/write\]|\Z)", re.S)
TAG_ONE = re.compile(r"\[(run|read|ls):([^\]\n]*)\]")
JUNK_ARGS = {"", "FILE", "COMMAND", "DIR", "file", "command", "dir", "filename", "FILENAME"}
REFUSAL_RE = re.compile(
    r"(?is)^\s*(i'?m sorry|sorry|i apologi[sz]e|i can'?t|i cannot|as an ai).{0,80}"
    r"(can'?t|cannot|unable|not able|won'?t).{0,40}(assist|help|do that|comply)")


def parse_events(reply):
    spans = [(m.start(), m.end()) for m in TAG_WRITE.finditer(reply)]
    ev = [(m.start(), "write", m.group(1).strip(), m.group(2)) for m in TAG_WRITE.finditer(reply)]
    for m in TAG_ONE.finditer(reply):
        if any(a < m.start() < b for a, b in spans):
            continue
        ev.append((m.start(), m.group(1), m.group(2).strip(), ""))
    ev = [e for e in ev if e[2] not in JUNK_ARGS]
    ev.sort(key=lambda e: e[0])
    return [(k, a, b) for _, k, a, b in ev]


def visible_text(reply):
    t = TAG_ONE.sub("", TAG_WRITE.sub("", reply))
    t = re.sub(r"(?m)^Workspace:.*$|\[/?(?:write|code)[^\]]*\]", "", t)
    return t.strip()


def strip_fences(s):
    s = s.strip("\n")
    m = re.match(r"^```[\w+.#-]*[ \t]*\n(.*?)\n?```\s*$", s, re.S)
    return m.group(1) if m else s


class StreamFilter:
    """Live-stream filter: hides <think> blocks and [write:..]..[/write] / [run:..] tool tags."""
    OPEN = ("[write:", "[run:", "[read:", "[ls:")

    def __init__(self):
        self.buf, self.mode = "", None

    @property
    def suppressing(self):
        return self.mode is not None

    def feed(self, chunk):
        self.buf += chunk
        out = []
        while True:
            if self.mode in ("think", "write"):
                end = "</think>" if self.mode == "think" else "[/write]"
                i = self.buf.find(end)
                if i < 0:
                    self.buf = self.buf[-len(end):]
                    break
                self.buf, self.mode = self.buf[i + len(end):], None
                continue
            idx = [x for x in (self.buf.find("["), self.buf.find("<")) if x >= 0]
            if not idx:
                out.append(self.buf)
                self.buf = ""
                break
            i = min(idx)
            out.append(self.buf[:i])
            b = self.buf = self.buf[i:]
            if b[0] == "<":
                if b.startswith("<think>"):
                    self.buf, self.mode = b[7:], "think"
                    continue
                if "<think>".startswith(b):
                    break  # could still become <think>
                out.append("<")
                self.buf = b[1:]
                continue
            hit = next((o for o in self.OPEN if b.startswith(o)), None)
            if hit:
                j = b.find("]")
                if j < 0:
                    if len(b) > 300:
                        out.append("[")
                        self.buf = b[1:]
                        continue
                    break
                if hit == "[write:":
                    self.mode = "write"
                self.buf = b[j + 1:]
                continue
            if any(o.startswith(b) for o in self.OPEN):
                break  # partial opener, wait for more
            out.append("[")
            self.buf = b[1:]
        return "".join(out)

    def flush(self):
        rest = "" if self.mode else self.buf
        self.buf = ""
        return rest


# ═══════════════════════════ tools ═══════════════════════════
DANGEROUS = [r"\brm\s+-[a-z]*r[a-z]*f?\s+(/|~|\$HOME|\*)", r"\bmkfs", r"\bdd\s+if=", r":\(\)\s*\{",
             r">\s*/dev/sd", r"\bchmod\s+-R\s+777\s+/", r"\bshutdown\b", r"\breboot\b"]


class Tools:
    def __init__(self, work, auto=False):
        self.work, self.auto = os.path.abspath(work), auto
        os.makedirs(self.work, exist_ok=True)

    def path(self, name):
        name = name.strip().strip("'\"`")
        p = name if os.path.isabs(name) else os.path.join(self.work, name)
        return os.path.abspath(os.path.expanduser(p))

    def inside(self, p):
        return p == self.work or p.startswith(self.work.rstrip(os.sep) + os.sep)

    def confirm(self, msg, force=False):
        if self.auto and not force:
            return True
        try:
            return input("%s %s %s " % (YE("?"), msg, DM("[y/N]"))).strip().lower() in ("y", "yes")
        except (EOFError, KeyboardInterrupt):
            print()
            return False

    def write(self, name, content, ask=True):
        p = self.path(name)
        if not self.inside(p):
            return "REFUSED: path outside workspace (%s)" % self.work
        content = strip_fences(content)
        lines = content.count("\n") + 1
        print("%s write %s (%d lines)" % (CY("→"), BD(os.path.relpath(p, self.work)), lines))
        print(DM("┌" + "─" * 40))
        for ln in content.splitlines()[:25]:
            print(DM("│ ") + ln)
        if lines > 25:
            print(DM("│ ... %d more lines" % (lines - 25)))
        print(DM("└" + "─" * 40))
        if ask and not self.confirm("Save file?"):
            return "USER DENIED the write."
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "w", encoding="utf-8") as f:
            f.write(content.rstrip("\n") + "\n")
        print(GR("✓ saved " + os.path.relpath(p, self.work)))
        return "OK: wrote %s (%d lines)" % (name, lines)

    def read(self, name):
        p = self.path(name)
        try:
            with open(p, errors="replace") as f:
                data = f.read(3000)
            print("%s read %s (%d chars)" % (CY("→"), name, len(data)))
            return data
        except Exception as e:
            return "ERROR: %s" % e

    def ls(self, name=""):
        p = self.path(name or ".")
        try:
            items = sorted(os.listdir(p))
            print("%s ls %s" % (CY("→"), name or "."))
            return "\n".join(items[:60]) or "(empty)"
        except Exception as e:
            return "ERROR: %s" % e

    def run_live(self, cmd):
        """Run a program attached to the terminal (for scripts that ask for input())."""
        try:
            return subprocess.run(cmd, shell=True, cwd=self.work).returncode
        except KeyboardInterrupt:
            return 130
        except Exception as e:
            print(RD(str(e)))
            return 1

    def run_cmd(self, cmd, ask=True, quiet=False):
        """Run a shell command. Returns (exit_code, output). exit_code is None if the user said no."""
        cmd = cmd.strip()
        danger = any(re.search(d, cmd) for d in DANGEROUS)
        if not quiet:
            print("%s run %s" % (CY("→"), BD(cmd)))
        if danger:
            print(RD("⚠ looks dangerous!"))
        if (ask or danger) and not self.confirm("Run command?", force=danger):
            return None, "USER DENIED the command."
        try:
            r = subprocess.run(cmd, shell=True, cwd=self.work, capture_output=True, text=True,
                               timeout=60, stdin=subprocess.DEVNULL)
            rc, out = r.returncode, ((r.stdout or "") + (r.stderr or "")).strip()
        except subprocess.TimeoutExpired:
            rc, out = 124, "ERROR: command timed out (60s)"
        except Exception as e:
            rc, out = 1, "ERROR: %s" % e
        shown = out[:1500] + ("\n...[truncated]" if len(out) > 1500 else "")
        if not quiet or rc != 0:
            print(DM(shown) if rc == 0 else RD(shown) if shown else DM("(no output)"))
        return rc, shown or "(no output)"


# ═══════════════════════════ agent ═══════════════════════════
SYSTEM = """You are Y2B Agent, an offline AI assistant and coder running in Termux on a phone. Be brief, friendly and casual, like a helpful friend.
Greetings and small talk are welcome: reply warmly in one or two sentences.
Never refuse a harmless request and never say you cannot assist.
To use tools, put these tags in your reply:
[write:FILE]
file contents here
[/write]
[run:COMMAND]
[read:FILE]
[ls:DIR]
After a tool result arrives, continue. If a command failed, fix the file and run it again. When done, give a short final answer without tags.
Example:
User: make hi.py that prints hi and run it
Assistant: Creating and running it.
[write:hi.py]
print("hi")
[/write]
[run:python hi.py]
"""

GEN_SYSTEM = ("You are an expert programmer. Reply with ONLY the complete contents of the requested file "
              "inside one markdown code block. No explanation before or after. Prefer the language's "
              "standard library; it must run on Termux/Linux.")


class Agent:
    GREET_RE = re.compile(
        r"^\s*(hi+|hello+|hey+|hlo+|yo+|sup|howdy|namaste|vanakkam|good\s+(morning|afternoon|evening|night))\b"
        r"[\s!.,]*(bro+|buddy|man|dude|y2b|agent|there)?[\s!.?]*$", re.I)
    GREETS = ["Hey bro! Y2B Agent here, fully offline. What are we building today?",
              "Hello! Ready when you are. Try: create hello.py that prints hello and run it",
              "Hi! I can write code, fix bugs, run commands and manage files. What do you need?"]
    FILE_RE = re.compile(r"\b([\w\-]+\.(?:py|sh|js|txt|md|html|css|c|cpp|json))\b", re.I)
    NAMED_RE = re.compile(r"\bfile\s+(?:named|name|called)\s+([\w\-]+)\b", re.I)
    MAKE_RE = re.compile(r"\b(create|make|write|build|generate|save)\b", re.I)
    RUN_RE = re.compile(r"\b(run|test|execute)\b", re.I)
    RUNCMD_RE = re.compile(
        r"^\s*(?:please\s+)?(?:run|execute)\s+(?:the\s+)?[`'\"]?(.+?)[`'\"]?(?:\s+command)?"
        r"(?:\s+(?:in|on)\s+(?:my\s+)?(?:termux|terminal|phone|here))?\s*[.!]?\s*$", re.I)
    BUILD_RE = re.compile(r"\b(web|website|webpage|page|site|app|application|calculator|game|script|program|tool|"
                          r"todo|to-do|clock|timer|converter|generator|quiz|form|landing|portfolio|dashboard)\b", re.I)
    WEBISH_RE = re.compile(r"\b(web|website|webpage|html|page|site|browser|chrome|firefox|landing|portfolio)\b", re.I)
    OPEN_RE = re.compile(r"\b(open|launch|view|preview|show)\b|\b(chrome|browser|firefox)\b", re.I)
    QUESTION_RE = re.compile(r"^\s*(how|what|why|when|where|who|which|is|are|do|does|can|could|should|explain|tell)\b", re.I)
    STOP = set("a an the me my in on it to and or for of with that this please create make write build generate "
               "save run open using by your termux phone web based simple small new file named called want need "
               "can you i us then also test chrome browser firefox html launch view preview show".split())
    NEW_RE = re.compile(r"^\s*(please\s+)?(create|build|generate|write)\b", re.I)
    EDIT_RE = re.compile(r"\b(fix|won'?t work|wont work|doesn'?t work|not working|broken|blank|error|bug|"
                         r"change|add|update|improve|modify|edit|remove|rewrite|redo|bigger|smaller|faster|"
                         r"colou?r|make it)\b", re.I)
    REF_RE = re.compile(r"\b(it|this|that|the (page|file|game|site|website|app|code|script|calculator|program))\b", re.I)
    LIVE = {"sl", "htop", "top", "btop", "nano", "vim", "vi", "cmatrix", "nmtui", "less", "man", "cava"}

    def __init__(self, llm, tools, mem, steps=6, fix=3):
        self.llm, self.tools, self.mem = llm, tools, mem
        self.steps, self.fix_n = steps, fix
        self.hist = []          # [(role, text)]
        self.voice = False
        self._nudge = False
        self.last_file = None   # last file created/edited (for 'fix it', 'open it again')
        self.last_html = None
        self._http = None

    # ---- prompt building ----
    def system_prompt(self):
        s = SYSTEM
        facts = self.mem.get("facts", [])[-8:]
        if facts:
            s += "\nUser facts: " + "; ".join(facts) + "\n"
        if self._nudge:
            s += "\nThe request is harmless. Help directly. Do not refuse.\n"
        return s

    def build_messages(self):
        sysm = {"role": "system", "content": self.system_prompt()}
        h = [{"role": r, "content": t} for r, t in self.hist]
        budget = int((self.llm.ctx - self.llm.gen - 100) * 2.8)

        def size(ms):
            return sum(len(m["content"]) + 12 for m in ms)
        while len(h) > 1 and size([sysm] + h) > budget:
            h.pop(0)
        while h and h[0]["role"] != "user":
            h.pop(0)
        if h and size([sysm] + h) > budget:
            keep = max(200, budget - len(sysm["content"]) - 60)
            h[-1]["content"] = h[-1]["content"][-keep:]
        out = []
        for m in h:  # some chat templates require strictly alternating roles
            if out and out[-1]["role"] == m["role"]:
                out[-1]["content"] += "\n\n" + m["content"]
            else:
                out.append(dict(m))
        return [sysm] + out

    # ---- streaming ----
    def stream_reply(self, messages, detect_refusal=False):
        """Stream a reply live. Hides tool tags and <think>. Returns the full raw text."""
        sp = Spinner("thinking")
        sp.start()
        filt = StreamFilter()
        st = {"label": False, "n": 0, "t0": None, "hold": "", "holding": detect_refusal}
        full = []

        def emit(txt):
            if not txt:
                return
            if sp.active:
                sp.stop()
            if not st["label"]:
                if not txt.strip():
                    return
                sys.stdout.write("\n" + GR(BD(BOT)) + " ")
                st["label"] = True
                txt = txt.lstrip()
            sys.stdout.write(txt)
            sys.stdout.flush()

        def release(final=False):
            if st["holding"] and (final or len(st["hold"]) >= 70):
                st["holding"] = False
                if REFUSAL_RE.match(st["hold"]):
                    raise _Refusal()
                emit(st["hold"])
                st["hold"] = ""

        gen = self.llm.stream(messages)
        try:
            for ch in gen:
                full.append(ch)
                st["n"] += 1
                if st["t0"] is None:
                    st["t0"] = time.time()
                out = filt.feed(ch)
                if st["holding"]:
                    st["hold"] += out
                    release()
                else:
                    emit(out)
                if filt.suppressing and not sp.active and not st["holding"]:
                    if st["label"]:
                        sys.stdout.write("\n")
                    sp.start()
                if sp.active and st["n"] % 4 == 0:
                    sp.info = "%d tok · %.1f tok/s" % (st["n"], st["n"] / max(0.001, time.time() - st["t0"]))
            tail = filt.flush()
            if st["holding"]:
                st["hold"] += tail
                release(final=True)
            else:
                emit(tail)
        finally:
            gen.close()  # drops the HTTP connection so the server stops generating
            sp.stop()
        if st["label"]:
            dt = max(0.001, time.time() - (st["t0"] or time.time()))
            sys.stdout.write("\n" + DM("  ⚡ %d tok · %.1f tok/s" % (st["n"], st["n"] / dt)) + "\n\n")
            sys.stdout.flush()
        return "".join(full)

    def collect(self, messages, label):
        """Collect a reply silently (spinner with live token speed). Used for code generation."""
        sp = Spinner(label)
        sp.start()
        n, t0, buf = 0, None, []
        try:
            for ch in self.llm.stream(messages):
                t0 = t0 or time.time()
                n += 1
                buf.append(ch)
                if n % 4 == 0:
                    sp.info = "%d tok · %.1f tok/s" % (n, n / max(0.001, time.time() - t0))
        finally:
            sp.stop()
        return strip_think("".join(buf)).strip()

    def speak(self, text):
        if self.voice and shutil.which("termux-tts-speak") and text:
            subprocess.Popen(["termux-tts-speak", text[:300]], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    # ---- entry ----
    def handle(self, text):
        m = re.match(r"^\s*remember( that)?\s+(.+)", text, re.I)
        if m:
            self.mem.setdefault("facts", []).append(m.group(2).strip())
            save_json(MEM_FILE, self.mem)
            say("Got it, I'll remember that.")
            return
        if self.GREET_RE.match(text):
            say(random.choice(self.GREETS))
            return
        try:
            if (self.edit_task(text) or self.open_task(text) or self.file_task(text)
                    or self.run_task(text)):
                return
            self.agent_loop(text)
        except BackendError as e:
            say(str(e), err=True)
        except KeyboardInterrupt:
            print(YE("\n(interrupted)\n"))

    # ---- fast path 1: run a command ----
    def run_task(self, text):
        m = self.RUNCMD_RE.match(text)
        if not m:
            return False
        cmd = m.group(1).strip()
        first = cmd.split()[0]
        ext = os.path.splitext(first)[1].lower()
        if ext in RUNNERS and os.path.exists(self.tools.path(first)):
            cmd = "%s %s" % (RUNNERS[ext], cmd)
        elif not shutil.which(first):
            if first.lower() in ("it", "that", "this", "and", "the", "my", "a") or (
                    " " in cmd and not re.match(r"^[\w\-./]+$", first)):
                return False
            say("'%s' is not installed. Install it with: pkg install %s" % (first, first))
            return True
        if first in self.LIVE:
            say("Launching %s live. Exit it to come back to Y2B." % first)
            if self.tools.confirm("Run `%s`?" % cmd):
                try:
                    subprocess.run(cmd, shell=True, cwd=self.tools.work)
                except KeyboardInterrupt:
                    pass
                print()
            return True
        say("Running %s" % cmd)
        rc, out = self.tools.run_cmd(cmd)
        self.hist.append(("user", text))
        self.hist.append(("assistant", "Ran %s (exit %s). Output: %s" % (cmd, rc, out[:300])))
        print()
        return True

    # ---- fast path 2: create a file (+ run + auto-fix) ----
    @staticmethod
    def extract_code(reply):
        cb = re.search(r"```[\w+.#-]*[ \t]*\n(.*?)(?:```|\Z)", reply, re.S)
        code = cb.group(1) if cb else reply
        code = TAG_ONE.sub("", TAG_WRITE.sub(r"\2", code))
        return code.strip("\n")

    def infer_name(self, text):
        words = [w for w in re.findall(r"[a-z0-9]+", text.lower()) if w not in self.STOP and len(w) > 1]
        ext = ".html" if self.WEBISH_RE.search(text) else ".py"
        return ("_".join(words[:3]) or "app") + ext

    @staticmethod
    def gen_system(name):
        ext = os.path.splitext(name)[1].lower()
        extra = {".html": " Produce ONE complete self-contained HTML5 file with inline CSS and JavaScript only "
                          "(no external libraries, no CDN, no other files). Make it responsive and good looking on a phone.",
                 ".py": " Use only the Python standard library."}.get(ext, "")
        return GEN_SYSTEM + extra

    def open_in_browser(self, name):
        """Serve the workspace on localhost and open the page in the phone's browser (Chrome etc.)."""
        rel = os.path.relpath(self.tools.path(name), self.tools.work)
        if not self.tools.confirm("Open %s in your browser?" % rel):
            return False
        srv = getattr(self, "_http", None)
        if srv is None or srv[1] != self.tools.work or srv[0].poll() is not None:
            if srv and srv[0].poll() is None:
                srv[0].terminate()
            port = ServerBackend._free_port()
            try:
                proc = subprocess.Popen([PYTHON, "-m", "http.server", str(port), "--bind", "127.0.0.1"],
                                        cwd=self.tools.work, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            except Exception as e:
                print(RD("could not start a local web server: %s" % e))
                return False
            atexit.register(proc.terminate)
            self._http = srv = (proc, self.tools.work, port)
            time.sleep(0.7)
        url = "http://127.0.0.1:%d/%s" % (srv[2], urllib.parse.quote(rel))
        for tool in ("termux-open-url", "xdg-open", "open"):
            if shutil.which(tool):
                subprocess.Popen([tool, url], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                print(GR("→ opened ") + url + DM("  (stays live until you quit Y2B)"))
                return True
        print(YE("open this link in your browser: ") + url)
        return True

    def gen_code(self, msgs, name):
        reply = self.collect(msgs, "writing " + name)
        return self.extract_code(reply), reply

    def file_task(self, text):
        if not self.MAKE_RE.search(text):
            return False
        fm = self.FILE_RE.search(text)
        if fm:
            name = fm.group(1)
        else:
            nm = self.NAMED_RE.search(text)
            if nm:
                name = nm.group(1) + (".html" if self.WEBISH_RE.search(text) else ".py")
            elif self.BUILD_RE.search(text) and not self.QUESTION_RE.match(text):
                name = self.infer_name(text)  # "create a web birthday calculator" -> birthday_calculator.html
            else:
                return False
        base = [{"role": "system", "content": self.gen_system(name)},
                {"role": "user", "content": "File: %s\nTask: %s" % (name, text)}]
        code, reply = self.gen_code(base, name)
        if len(code.strip()) < 2:
            say(reply or "The model returned nothing. Try again or /clear.", err=True)
            return True
        say("Here's %s:" % name)
        return self.finish_file(name, code, text, base)

    @staticmethod
    def fix_note(fixes, rc):
        if not fixes:
            return ""
        if rc == 0:
            return " Auto-fixed in %d attempt%s." % (fixes, "" if fixes == 1 else "s")
        return " Auto-fix tried %d time(s) but it still has problems." % fixes

    def finish_file(self, name, code, text, base, verb="Created"):
        """Save, then run / open / check the file, auto-fixing problems. Shared by create and edit."""
        r = self.tools.write(name, code)
        if not r.startswith("OK"):
            say("%s was not saved." % name)
            return True
        self.last_file = name
        ext = os.path.splitext(name)[1].lower()
        runner = RUNNERS.get(ext)
        if ext in (".html", ".htm"):
            self.last_html = name
            rc, out = self.check_html(name, code)
            fixes = 0
            if rc and self.fix_n > 0:
                rc, out, code, fixes = self.fix_loop(base, name, code, "page check", True, rc, out,
                                                     check=lambda c: self.check_html(name, c))
            note = "%s %s." % (verb, name) + self.fix_note(fixes, rc)
            if rc and not fixes:
                note += " Heads up: " + out[:140]
            if self.RUN_RE.search(text) or self.OPEN_RE.search(text):
                note += " Opened in your browser." if self.open_in_browser(name) else " (not opened)"
            say(note)
            self.hist.append(("user", text))
            self.hist.append(("assistant", "%s\n```\n%s\n```" % (note, code[:1200])))
            return True
        wants_run = bool(self.RUN_RE.search(text)) and runner is not None
        rc, out, cmd, quiet, live = 0, "", "", False, False
        if wants_run and ext == ".py" and "input(" in code:
            print(DM("this program asks for input, so it runs live in your terminal"))
            cmd = "%s %s" % (runner, name)
            rc = self.tools.run_live(cmd) if self.tools.confirm("Run `%s`?" % cmd) else None
            live, cmd = True, ""  # no captured error text, so no auto-fix
        elif wants_run:
            cmd = "%s %s" % (runner, name)
            rc, out = self.tools.run_cmd(cmd)
        elif ext == ".py":  # free safety net: syntax-check every python file we create
            cmd, quiet = "%s -m py_compile %s" % (PYTHON, name), True
            rc, out = self.tools.run_cmd(cmd, ask=False, quiet=True)
        fixes = 0
        if rc not in (0, None) and self.fix_n > 0 and cmd:
            rc, out, code, fixes = self.fix_loop(base, name, code, cmd, quiet, rc, out)
        note = "%s %s." % (verb, name) + self.fix_note(fixes, rc)
        if live:
            note += " Ran it live." if rc == 0 else ""
        elif wants_run and rc == 0:
            note += " Output: " + out[:200]
        elif wants_run and rc not in (0, None) and not fixes:
            note += " It failed (exit %s)." % rc
        say(note)
        self.hist.append(("user", text))
        self.hist.append(("assistant", "%s\n```\n%s\n```" % (note, code[:1200])))
        return True

    # ---- web page sanity checks (the usual reasons a small model's page is blank) ----
    @staticmethod
    def js_error(js):
        node = shutil.which("node")
        if node:
            with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False, encoding="utf-8") as f:
                f.write(js)
                tmp = f.name
            try:
                r = subprocess.run([node, "--check", tmp], capture_output=True, text=True, timeout=20)
                if r.returncode != 0:
                    msg = [ln for ln in (r.stderr or "").splitlines() if "Error" in ln]
                    return "script error: " + (msg[0] if msg else "syntax error")[:140]
                return ""
            except Exception:
                pass
            finally:
                try:
                    os.unlink(tmp)
                except Exception:
                    pass
        # no node: strip strings/comments, then check that brackets balance
        t = re.sub(r"\"(?:\\.|[^\"\\\n])*\"|'(?:\\.|[^'\\\n])*'|`(?:\\.|[^`\\])*`", '""', js)
        t = re.sub(r"/\*.*?\*/", "", t, flags=re.S)
        t = re.sub(r"//[^\n]*", "", t)
        for o, c_ in (("{", "}"), ("(", ")"), ("[", "]")):
            if t.count(o) != t.count(c_):
                return "script has unbalanced %s%s (%d vs %d)" % (o, c_, t.count(o), t.count(c_))
        return ""

    def check_html(self, name, code=None):
        """Returns (0, 'ok') or (1, problems). Cheap static checks, no browser needed."""
        if code is None:
            with open(self.tools.path(name), errors="replace") as f:
                code = f.read()
        problems = []
        folder = os.path.dirname(self.tools.path(name))
        for m in re.finditer(r"<(?:link[^>]+href|script[^>]+src|img[^>]+src)\s*=\s*[\"']([^\"']+)[\"']", code, re.I):
            ref = m.group(1)
            if re.match(r"^(https?:)?//", ref, re.I):
                problems.append("external file %s cannot load offline, inline it" % ref[:50])
            elif not re.match(r"^(data:|#|mailto:)", ref, re.I) and \
                    not os.path.exists(os.path.join(folder, ref.split("?")[0])):
                problems.append("%s does not exist, put the CSS/JS inline in <style>/<script>" % ref)
        scripts = re.findall(r"<script(?![^>]*\bsrc=)[^>]*>(.*?)</script>", code, re.S | re.I)
        for js in scripts:
            err = self.js_error(js)
            if err:
                problems.append(err)
            ids = set(re.findall(r"getElementById\(\s*['\"]([\w\-]+)['\"]", js)) | \
                set(re.findall(r"querySelector\(\s*['\"]#([\w\-]+)['\"]", js))
            for ident in ids:
                if not re.search(r"\bid\s*=\s*[\"']?%s(?=[\"'\s>/])" % re.escape(ident), code) and \
                        not re.search(r"\.id\s*=\s*[\"']%s[\"']" % re.escape(ident), js):
                    problems.append("script uses id '%s' but no element has it" % ident)
        if problems:
            return 1, "; ".join(problems)[:600]
        return 0, "ok"

    # ---- follow-ups: "fix it", "it won't work", "open it again" ----
    def edit_task(self, text):
        if not self.last_file or self.NEW_RE.match(text):
            return False
        if not (self.EDIT_RE.search(text) and self.REF_RE.search(text)):
            return False
        p = self.tools.path(self.last_file)
        if not os.path.exists(p):
            return False
        name = self.last_file
        with open(p, errors="replace") as f:
            old = f.read()
        base = [{"role": "system", "content": self.gen_system(name)},
                {"role": "user", "content": "Here is the current file %s:\n```\n%s\n```\nChange requested: %s\n"
                                            "Return the complete corrected file in one code block."
                                            % (name, old[:6000], text)}]
        code, reply = self.gen_code(base, name)
        if len(code.strip()) < 2:
            say(reply or "The model returned nothing. Try again.", err=True)
            return True
        say("Updating %s:" % name)
        ext = os.path.splitext(name)[1].lower()
        follow = " open it" if ext in (".html", ".htm") else (
            " run it" if re.search(r"fix|error|work|bug|broken|fail", text, re.I) else "")
        return self.finish_file(name, code, text + follow, base, verb="Updated")

    def open_task(self, text):
        if self.MAKE_RE.search(text) or not re.search(r"\b(open|reopen|launch)\b", text, re.I):
            return False
        fm = re.search(r"\b([\w\-]+\.html?)\b", text, re.I)
        name = fm.group(1) if fm else None
        if not name and self.last_html and re.search(
                r"\b(again|it|that|chrome|browser|page|site|website|game|app)\b", text, re.I):
            name = self.last_html
        if not name:
            return False
        if not os.path.exists(self.tools.path(name)):
            say("I can't find %s in %s" % (name, self.tools.work), err=True)
            return True
        say("Opened %s in your browser." % name if self.open_in_browser(name) else "OK, not opening it.")
        return True

    def fix_loop(self, base, name, code, cmd, quiet, rc, out, check=None):
        if not self.tools.confirm("%s has a problem. Let Y2B auto-fix it (up to %d tries)?" % (name, self.fix_n)):
            return rc, out, code, 0
        fixes, hint = 0, ""
        while rc not in (0, None) and fixes < self.fix_n:
            fixes += 1
            print("%s auto-fix %d/%d" % (YE("🔧"), fixes, self.fix_n))
            msgs = base + [
                {"role": "assistant", "content": "```\n%s\n```" % code},
                {"role": "user", "content": "Checking `%s` failed (exit code %s):\n%s\n%sFix the bug. Return the "
                                            "complete corrected file in one code block, nothing else."
                                            % (cmd, rc, out[-700:], hint)}]
            newcode, _ = self.gen_code(msgs, name)
            if len(newcode.strip()) < 2:
                break
            if newcode.strip() == code.strip():
                hint = "Your previous answer changed nothing. You MUST change the code. "
                continue
            hint, code = "", newcode
            self.tools.write(name, code, ask=False)
            rc, out = check(code) if check else self.tools.run_cmd(cmd, ask=False, quiet=quiet)
        return rc, out, code, fixes

    # ---- general agent loop ----
    def agent_loop(self, text):
        self.hist.append(("user", text))
        for step in range(self.steps):
            try:
                reply = self.stream_reply(self.build_messages(), detect_refusal=(step == 0))
            except _Refusal:
                self._nudge = True
                try:
                    reply = self.stream_reply(self.build_messages())
                finally:
                    self._nudge = False
            reply = strip_think(reply).strip()
            if not reply:
                say("The model returned an empty reply. Try rephrasing, or /clear.", err=True)
                self.hist.pop()
                return
            self.hist.append(("assistant", reply))
            self.speak(visible_text(reply))
            events = parse_events(reply)
            results = []
            if not events:
                results = self.fallback_save(text, reply)
                if not results:
                    return
            failed = False
            for kind, arg, body in events:
                if kind == "write":
                    r = self.tools.write(arg, body)
                elif kind == "run":
                    rc, out = self.tools.run_cmd(arg)
                    r = "exit %s\n%s" % (rc, out)
                    failed = failed or (rc not in (0, None))
                elif kind == "read":
                    r = self.tools.read(arg)
                else:
                    r = self.tools.ls(arg)
                results.append("%s %s: %s" % (kind, arg, r))
            msg = "TOOL RESULT:\n" + "\n".join(results)[:1500]
            if failed:
                msg += "\nThe command FAILED. Read the error, fix the file and run it again."
            self.hist.append(("user", msg))
        print(DM("(step limit reached)\n"))

    def fallback_save(self, user_text, reply):
        fm = self.FILE_RE.search(user_text)
        cb = re.search(r"```[\w+.#-]*[ \t]*\n(.*?)```", reply, re.S)
        if fm and cb and self.MAKE_RE.search(user_text):
            print(GR("→ saving the code block as %s" % fm.group(1)))
            r = self.tools.write(fm.group(1), cb.group(1))
            res = [r]
            runner = RUNNERS.get(os.path.splitext(fm.group(1))[1].lower())
            if r.startswith("OK") and runner and self.RUN_RE.search(user_text):
                rc, out = self.tools.run_cmd("%s %s" % (runner, fm.group(1)))
                res.append("exit %s\n%s" % (rc, out))
            return res
        return []


class _Refusal(Exception):
    pass


# ═══════════════════════════ app / commands ═══════════════════════════
HELP = """
%(chat)s      just type naturally, e.g. "create calc.py that adds two numbers and run it"
%(mem)s    remember <fact>    /mem    /forget    /clear (reset chat)
%(files)s     /ls [dir]  /cat <file>  /write <file>  /rm <file>  /cd <dir>  /pwd
%(shell)s     /run <command>     !<command>     /open [page.html]
%(model)s     /models  /model <n>  /info  /doctor  /ctx
%(mode)s      /auto  /fix <n>  /steps <n>  /temp <0-1>  /voice  /listen
%(misc)s      /cls  /help  /exit
"""


def help_text():
    return HELP % {k: BD(v) for k, v in dict(chat="Chat", mem="Memory", files="Files", shell="Shell",
                                              model="Model", mode="Mode", misc="Misc").items()}


class App:
    def __init__(self, args, conf):
        self.args, self.conf = args, conf
        self.backend = None
        self.info = None
        self.ctx = args.ctx
        self.llm = None

    def make_backend(self, model, pick_new=False):
        a = self.args
        self.info = model_info(model)
        ctx = a.ctx or auto_ctx(self.info["size_mb"])
        threads = a.threads or cpu_threads()
        srv = a.llama_server or find_bin(["llama-server"])
        if srv:
            return ServerBackend(srv, model, ctx, threads, a.port), ctx, threads
        cli = a.llama_cli or find_bin(["llama-completion", "llama-cli", "llama-cpp-cli", "main"])
        if cli:
            return CliBackend(cli, model, ctx, threads, self.info["template"]), ctx, threads
        return None, ctx, threads

    def load(self, backend, label):
        sp = Spinner("loading " + label)
        sp.start()
        t0 = time.time()
        try:
            backend.start(on_wait=lambda s: setattr(sp, "info", "waiting for the model to load into RAM"))
        finally:
            sp.stop()
        return time.time() - t0


def pick_model_menu(models, default=None):
    print(BD("\nModels found:"))
    for i, m in enumerate(models, 1):
        info = model_info(m)
        size = "%.1f GB" % (info["size_mb"] / 1024) if info["size_mb"] >= 1024 else "%d MB" % info["size_mb"]
        print("  %s %s  %s" % (CY("%d)" % i), info["name"], DM("%s · %s" % (size, info["quant"]))))
    if not sys.stdin.isatty():
        return models[0]
    while True:
        try:
            s = input("\n%s Pick a model %s " % (YE("?"), DM("[1-%d, Enter=1]" % len(models)))).strip()
        except (EOFError, KeyboardInterrupt):
            print()
            sys.exit(0)
        if not s:
            return models[0]
        if s.isdigit() and 1 <= int(s) <= len(models):
            return models[int(s) - 1]


def no_runtime_help():
    return ("\n%s\n  No llama.cpp binary found. Install one:\n"
            "    Termux:   pkg install llama-cpp\n"
            "    Other:    https://github.com/ggml-org/llama.cpp  (build llama-server)\n"
            "  Or point Y2B at a running server:  y2b --url http://127.0.0.1:8080\n" % RD("✗ llama.cpp not found"))


def no_model_help():
    return ("\n%s\n  Put any .gguf model in ~/models (or pass --model /path/model.gguf).\n"
            "  Example (small, good at code):\n"
            "    mkdir -p ~/models && cd ~/models\n"
            "    curl -L -O https://huggingface.co/Qwen/Qwen2.5-Coder-1.5B-Instruct-GGUF/resolve/main/"
            "qwen2.5-coder-1.5b-instruct-q4_k_m.gguf\n" % RD("✗ no .gguf model found"))


def doctor(args, conf):
    print(BD("\nY2B Agent %s · doctor" % __version__))
    print(" python       :", sys.version.split()[0])
    print(" platform     :", sys.platform, "(Termux)" if os.environ.get("PREFIX", "").startswith("/data/data/com.termux") else "")
    print(" free RAM     :", ("%d MB" % mem_available_mb()) if mem_available_mb() else "unknown")
    print(" cpu threads  : %d (auto: %d)" % (os.cpu_count() or 0, cpu_threads()))
    print(" llama-server :", args.llama_server or find_bin(["llama-server"]) or RD("not found"))
    print(" llama-cli    :", args.llama_cli or find_bin(["llama-completion", "llama-cli"]) or RD("not found"))
    models = discover_models()
    print(" models       :", len(models))
    for m in models[:10]:
        i = model_info(m)
        print("    - %s  (%s, %s, %d MB, template=%s)" % (i["name"], i["family"], i["quant"], i["size_mb"], i["template"]))
    for url in ("http://127.0.0.1:8080", "http://127.0.0.1:11434"):
        print(" server %-22s: %s" % (url, GR("running") if OpenAIBackend(url).healthy() else DM("not running")))
    print(" config       :", CONF_FILE, conf)
    print()


def cmd_loop(app, agent, tools):
    llm = app.llm
    while True:
        try:
            line = input(prompt_str()).strip()
        except (EOFError, KeyboardInterrupt):
            bye()
            return
        if not line:
            continue
        if line.startswith("!"):
            line = "/run " + line[1:]
        if not line.startswith("/"):
            agent.handle(line)
            continue
        cmd, _, arg = line[1:].partition(" ")
        arg = arg.strip()
        if cmd in ("exit", "quit", "q"):
            bye()
            return
        elif cmd == "help":
            print(help_text())
        elif cmd == "clear":
            agent.hist.clear()
            print(GR("chat cleared\n"))
        elif cmd == "cls":
            show_banner(compact=True)
            print()
        elif cmd == "ls":
            print(tools.ls(arg) + "\n")
        elif cmd == "pwd":
            print(tools.work + "\n")
        elif cmd == "cd":
            p = tools.path(arg or "~")
            if os.path.isdir(p):
                tools.work = p
                print(GR("workspace: %s\n" % p))
            else:
                print(RD("not a directory\n"))
        elif cmd == "cat":
            print(tools.read(arg) + "\n")
        elif cmd == "run":
            if arg:
                tools.run_cmd(arg)
                print()
        elif cmd == "open":
            name = arg or agent.last_html
            if not name:
                print(YE("no page yet. Usage: /open page.html\n"))
            elif not os.path.exists(tools.path(name)):
                print(RD("file not found: %s\n" % name))
            else:
                agent.open_in_browser(name)
                print()
        elif cmd == "write":
            if not arg:
                print(RD("usage: /write <file>\n"))
                continue
            print(DM("type the content, finish with a line containing only :wq"))
            buf = []
            while True:
                try:
                    ln = input()
                except EOFError:
                    break
                if ln.strip() == ":wq":
                    break
                buf.append(ln)
            tools.write(arg, "\n".join(buf))
            print()
        elif cmd == "rm":
            p = tools.path(arg)
            if os.path.isfile(p) and tools.inside(p) and tools.confirm("Delete %s?" % arg, force=True):
                os.remove(p)
                print(GR("deleted\n"))
            else:
                print(RD("not deleted\n"))
        elif cmd == "mem":
            facts = agent.mem.get("facts", [])
            print("\n".join(" %d. %s" % (i + 1, f) for i, f in enumerate(facts)) or DM("(no memories)"), "\n")
        elif cmd == "forget":
            agent.mem["facts"] = []
            save_json(MEM_FILE, agent.mem)
            print(GR("memory wiped\n"))
        elif cmd == "auto":
            tools.auto = not tools.auto
            print((RD("AUTO-APPROVE ON") if tools.auto else GR("auto-approve off")) + "\n")
        elif cmd == "fix":
            if arg.isdigit():
                agent.fix_n = int(arg)
            print(GR("auto-fix attempts: %d\n" % agent.fix_n))
        elif cmd == "steps":
            if arg.isdigit() and int(arg) > 0:
                agent.steps = int(arg)
            print(GR("max agent steps: %d\n" % agent.steps))
        elif cmd == "voice":
            agent.voice = not agent.voice
            ok = shutil.which("termux-tts-speak")
            print(GR("voice %s" % ("on" if agent.voice else "off")) +
                  ("" if ok else YE(" (install: pkg install termux-api)")) + "\n")
        elif cmd == "listen":
            if not shutil.which("termux-speech-to-text"):
                print(YE("install: pkg install termux-api (and the Termux:API app)\n"))
                continue
            print(DM("listening..."))
            try:
                heard = subprocess.run(["termux-speech-to-text"], capture_output=True, text=True, timeout=30).stdout.strip()
            except Exception:
                heard = ""
            if heard:
                print(CY("you ❯ ") + heard)
                agent.handle(heard)
            else:
                print(YE("didn't catch that\n"))
        elif cmd == "temp":
            try:
                llm.temp = max(0.0, min(1.5, float(arg)))
                print(GR("temp=%s\n" % llm.temp))
            except ValueError:
                print(RD("usage: /temp 0.2\n"))
        elif cmd == "ctx":
            print(" context window: %d tokens (restart with --ctx N to change)\n" % llm.ctx)
        elif cmd == "info":
            print(" backend : %s\n model   : %s\n ctx     : %d   gen: %d   temp: %s\n work    : %s\n" % (
                llm.backend.describe(), (app.info or {}).get("name", "-"), llm.ctx, llm.gen, llm.temp, tools.work))
        elif cmd == "doctor":
            doctor(app.args, app.conf)
        elif cmd in ("models", "model"):
            models = discover_models()
            if cmd == "model" and arg:
                target = models[int(arg) - 1] if arg.isdigit() and 1 <= int(arg) <= len(models) else os.path.expanduser(arg)
                if not os.path.exists(target):
                    print(RD("model not found\n"))
                    continue
                if not llm.backend.owned:
                    print(YE("This is an external server; switch the model there.\n"))
                    continue
                llm.backend.stop()
                nb, ctx, thr = app.make_backend(target)
                try:
                    secs = app.load(nb, os.path.basename(target))
                except BackendError as e:
                    print(RD(str(e)) + "\n")
                    continue
                llm.backend, llm.ctx = nb, ctx
                app.conf["model"] = target
                save_json(CONF_FILE, app.conf)
                print(GR("✓ switched to %s (%.0fs)\n" % (os.path.basename(target), secs)))
            else:
                cur = (app.info or {}).get("name")
                for i, m in enumerate(models, 1):
                    mark = GR("●") if os.path.basename(m) == cur else " "
                    print(" %s %s %s" % (mark, CY("%d)" % i), os.path.basename(m)))
                print(DM(" switch with /model <number>\n"))
        else:
            print(RD("unknown command, try /help\n"))


def bye():
    sys.stdout.write("\n")
    typewrite(g256(45, "Y2B Agent") + DM(" going offline. See you soon!"), cap=1.0)
    sys.stdout.write("\n" + DM("  ✦ " + MADE_BY) + "\n\n")
    sys.stdout.flush()


# ═══════════════════════════ main ═══════════════════════════
def build_parser():
    ap = argparse.ArgumentParser(prog="y2b", description="Y2B Agent - offline, model-agnostic AI coding agent. " + MADE_BY)
    ap.add_argument("--model", "-m", help="path to a .gguf model (default: auto-detect / menu)")
    ap.add_argument("--pick", action="store_true", help="always show the model menu")
    ap.add_argument("--url", help="use an existing OpenAI-compatible server, e.g. http://127.0.0.1:8080 or Ollama :11434")
    ap.add_argument("--model-name", help="model name for --url servers (auto-detected if omitted)")
    ap.add_argument("--api-key", help="API key for --url servers (if needed)")
    ap.add_argument("--no-attach", action="store_true", help="don't auto-attach to a server that is already running")
    ap.add_argument("--llama-server", help="path to llama-server")
    ap.add_argument("--llama-cli", help="path to llama-completion / llama-cli (slow fallback)")
    ap.add_argument("--port", type=int, help="port for the llama-server Y2B starts")
    ap.add_argument("--ctx", type=int, help="context window in tokens (default: auto from free RAM)")
    ap.add_argument("--gen", type=int, default=768, help="max tokens per reply (default 768)")
    ap.add_argument("--temp", type=float, default=0.2, help="temperature (default 0.2)")
    ap.add_argument("--threads", type=int, help="CPU threads (default: auto)")
    ap.add_argument("--work", default=None, help="workspace folder (default: current directory)")
    ap.add_argument("--auto", action="store_true", help="auto-approve file writes and commands (careful!)")
    ap.add_argument("--steps", type=int, default=6, help="max tool steps per request (default 6)")
    ap.add_argument("--fix", type=int, default=3, help="max auto-fix attempts for broken code (0 = off)")
    ap.add_argument("--no-anim", action="store_true", help="disable animations")
    ap.add_argument("--doctor", action="store_true", help="print diagnostics and exit")
    ap.add_argument("--version", action="version", version="Y2B Agent %s (%s)" % (__version__, MADE_BY))
    return ap


def main(argv=None):
    global ANIM
    args = build_parser().parse_args(argv)
    if not args.work:
        cwd = os.getcwd()  # don't scatter generated files inside the Y2B source folder
        args.work = os.path.join(HOME, "y2b_workspace") if os.path.exists(os.path.join(cwd, "y2b_agent.py")) else cwd
    if args.no_anim:
        ANIM = False
    conf = load_json(CONF_FILE, {})
    if args.doctor:
        doctor(args, conf)
        return 0

    show_banner()
    app = App(args, conf)
    backend, ctx, info = None, args.ctx, None

    # 1) explicit URL, or an already-running server -> no model files needed
    if args.url:
        backend = OpenAIBackend(args.url, args.model_name, args.api_key)
    elif not args.no_attach and not args.model:
        for url in ("http://127.0.0.1:8080", "http://127.0.0.1:11434"):
            ob = OpenAIBackend(url, args.model_name, args.api_key)
            if ob.healthy():
                backend = ob
                break
    if backend is None:
        # 2) local model + local llama.cpp
        model = args.model and os.path.expanduser(args.model)
        if model and not os.path.exists(model):
            print(RD("model file not found: %s" % model))
            return 1
        if not model:
            saved = conf.get("model")
            models = discover_models()
            if saved and os.path.exists(saved) and not args.pick:
                model = saved
            elif not models:
                print(no_model_help())
                return 1
            elif len(models) == 1 and not args.pick:
                model = models[0]
            else:
                model = pick_model_menu(models)
        backend, ctx, _thr = app.make_backend(model)
        if backend is None:
            print(no_runtime_help())
            return 1
        conf["model"] = model
        save_json(CONF_FILE, conf)
    else:
        ctx = ctx or 4096
        app.info = {"name": backend.model_name, "family": "external", "template": "-", "params_b": None,
                    "quant": "?", "size_mb": 0}

    try:
        secs = app.load(backend, (app.info or {}).get("name", "model"))
    except BackendError as e:
        print(RD("\n✗ could not start the model backend:\n") + str(e))
        print(DM("  run `y2b --doctor` for diagnostics; log: " + LOG_FILE))
        return 1
    atexit.register(backend.stop)

    llm = LLM(backend, ctx, args.gen, args.temp)
    app.llm = llm
    tools = Tools(args.work, args.auto)
    mem = load_json(MEM_FILE, {"facts": []})
    agent = Agent(llm, tools, mem, steps=args.steps, fix=args.fix)

    show_banner()
    inf = app.info or {}
    if inf.get("size_mb"):
        gb = inf["size_mb"] / 1024.0
        parts = ["%.1f GB" % gb if gb >= 1 else "%d MB" % inf["size_mb"]]
        if inf.get("params_b"):
            parts.append("%gB" % inf["params_b"])
        if inf.get("quant") not in (None, "?"):
            parts.append(inf["quant"])
        size_line = "size    " + " · ".join(parts)
    else:
        size_line = "mode    attached to a running server"
    print(card([
        (GR, "● online  ·  fully offline" + ("  ·  ready in %.0fs" % secs if backend.owned else "")),
        (CY, "model   " + inf.get("name", "?")),
        (CY, size_line),
        (CY, "backend " + backend.label),
        (CY, "ctx %d  ·  gen %d  ·  fix x%d" % (llm.ctx, llm.gen, agent.fix_n)),
        (CY, "work    " + tools.work),
    ]))
    print(" " + MG("✦ " + MADE_BY))
    if backend.kind == "cli":
        print(" " + YE("tip: install llama-server (pkg install llama-cpp) for much faster replies"))
    print(" " + DM("type ") + YE("/help") + DM(" for commands  ·  ") + YE("/exit") + DM(" to quit") + "\n")

    cmd_loop(app, agent, tools)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        sys.exit(130)
