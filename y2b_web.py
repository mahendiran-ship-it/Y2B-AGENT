"""Y2B web builder: complete, tested, futuristic one-file websites that work offline.

Small local models cannot write 500+ lines of working JavaScript in one go. So Y2B lets the
model write only the *content* (title, tagline, features, gallery items, FAQ...) as a few short
lines, and this module assembles it into a finished page from a built-in, tested template.
The model's text is injected as JSON data and rendered with textContent, never as code.
"""
from __future__ import annotations

import json
import re

ACCENTS = {
    "cyan": ("#22d3ee", "#8b5cf6"),
    "violet": ("#8b5cf6", "#22d3ee"),
    "green": ("#34d399", "#22d3ee"),
    "orange": ("#fb923c", "#f43f5e"),
    "pink": ("#f472b6", "#8b5cf6"),
    "blue": ("#60a5fa", "#a78bfa"),
}

DEFAULTS = {
    "title": "Nexus Core",
    "tagline": "An offline command center for ideas, tools and play. Fast, private and beautifully animated.",
    "accent": "cyan",
    "features": [
        ["Instant Search", "Find anything in the gallery as you type, with category filters and sorting."],
        ["Command Palette", "Press Ctrl+K or / to jump to any section or action without touching the mouse."],
        ["Live Particle Lab", "Tune particle count, speed, size and colour and watch the network react."],
        ["Built-in Tools", "A calculator, stopwatch, notes and task list that save on your device."],
        ["Adaptive Themes", "Switch between dark and light, pick an accent colour, calm all motion."],
        ["Fully Offline", "One file. No servers, no accounts, no tracking, works in airplane mode."],
    ],
    "items": [
        ["Aurora", "Light", "Slow ribbons of colour drifting across a midnight sky."],
        ["Helix", "Motion", "Twin strands rotating around a glowing axis."],
        ["Prism", "Light", "A beam split into a spectrum of soft glass edges."],
        ["Orbit", "Motion", "Small worlds circling a quiet, bright centre."],
        ["Lattice", "Structure", "A fine grid that bends toward your cursor."],
        ["Monolith", "Structure", "A tall dark slab with a single glowing seam."],
        ["Pulse", "Motion", "Rings of light expanding from a heartbeat."],
        ["Nebula", "Light", "Dust and colour gathering into a slow cloud."],
    ],
    "faq": [
        ["Does it need internet?", "No. Everything lives in this single HTML file and runs offline."],
        ["Is my data uploaded?", "Never. Notes and tasks are stored only in this browser."],
        ["Can I change the look?", "Yes. Use the settings panel for theme, accent colour and motion."],
        ["Which keys work?", "Ctrl+K or / opens the palette, ? shows all shortcuts, T toggles the theme."],
    ],
    "about": "We build calm, fast and playful software that respects your device and your time. "
             "Everything here runs locally, so it is quick, private and always available.",
    "stats": [["Sections", 6], ["Tools", 4], ["Particles", 120], ["Kilobytes", 40]],
}

SPEC_SYSTEM = (
    "You write website CONTENT only (no code). Reply with exactly these lines and nothing else:\n"
    "TITLE: short brand name (1-3 words)\n"
    "TAGLINE: one sentence under 20 words\n"
    "ACCENT: one of cyan, violet, green, orange, pink, blue\n"
    "FEATURE: name | one sentence   (6 lines)\n"
    "ITEM: name | category | one sentence   (8 lines, use 3 categories)\n"
    "FAQ: question | answer   (4 lines)\n"
    "ABOUT: two sentences\n"
    "Match the topic the user asked for."
)

_SITE_WORDS = re.compile(r"\b(website|web\s*site|portfolio|futuristic|ultra[- ]modern|"
                         r"interactive\s+(?:site|page|website)|multi-?section)\b", re.I)


def wants_site(text: str) -> bool:
    """True for requests that describe a full website (not a tiny one-purpose page)."""
    t = text or ""
    if _SITE_WORDS.search(t):
        return True
    return len(t) > 600 and bool(re.search(r"\b(html|web|page|site)\b", t, re.I))


def _clean(s: str, n: int) -> str:
    s = re.sub(r"[`*_#<>{}\[\]\\]", "", s or "").strip(" -\t\"'")
    s = re.sub(r"\s+", " ", s)
    return s[:n]


def parse_spec(reply: str) -> dict:
    """Leniently parse the model's line format. Anything missing falls back to a good default."""
    spec = json.loads(json.dumps(DEFAULTS))
    feats, items, faq = [], [], []
    for raw in (reply or "").splitlines():
        line = raw.strip().lstrip("-•*0123456789. ").strip()
        m = re.match(r"(?i)^(title|tagline|accent|feature|item|faq|about)\s*[:=]\s*(.+)$", line)
        if not m:
            continue
        key, val = m.group(1).lower(), m.group(2).strip()
        parts = [p.strip() for p in val.split("|")]
        if key == "title" and _clean(val, 28):
            spec["title"] = _clean(val, 28)
        elif key == "tagline" and len(_clean(val, 160)) > 8:
            spec["tagline"] = _clean(val, 160)
        elif key == "accent":
            a = val.lower().split()[0].strip(".,")
            if a in ACCENTS:
                spec["accent"] = a
        elif key == "about" and len(_clean(val, 400)) > 20:
            spec["about"] = _clean(val, 400)
        elif key == "feature" and len(parts) >= 2 and parts[0] and parts[1]:
            feats.append([_clean(parts[0], 30), _clean(" ".join(parts[1:]), 160)])
        elif key == "item" and len(parts) >= 3 and parts[0] and parts[1]:
            items.append([_clean(parts[0], 24), _clean(parts[1], 16) or "General", _clean(" ".join(parts[2:]), 160)])
        elif key == "faq" and len(parts) >= 2 and parts[0] and parts[1]:
            faq.append([_clean(parts[0], 80), _clean(" ".join(parts[1:]), 200)])
    if len(feats) >= 3:
        spec["features"] = feats[:8]
    if len(items) >= 4:
        spec["items"] = items[:12]
    if len(faq) >= 2:
        spec["faq"] = faq[:6]
    return spec


def build_site(spec: dict | None = None) -> str:
    spec = dict(DEFAULTS, **(spec or {}))
    a1, a2 = ACCENTS.get(spec.get("accent"), ACCENTS["cyan"])
    data = json.dumps(spec, ensure_ascii=False).replace("</", "<\\/").replace(" ", " ").replace(" ", " ")
    title = re.sub(r"[<>&\"]", "", spec["title"])
    html = TEMPLATE.replace("/*SITE*/null", data).replace("__A1__", a1).replace("__A2__", a2)
    return html.replace("__TITLE__", title)


TEMPLATE = r'''<!DOCTYPE html>
<html lang="en" data-theme="dark">
<head>
<meta charset="UTF-8">
<meta name="generator" content="y2b-site">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>__TITLE__</title>
<style>
:root{--a1:__A1__;--a2:__A2__;--bg:#04060f;--bg2:#0a1024;--tx:#e8edff;--mu:#93a0c8;--gl:rgba(255,255,255,.06);--bd:rgba(255,255,255,.12);--sh:0 20px 60px rgba(0,0,0,.5)}
[data-theme=light]{--bg:#eef2ff;--bg2:#ffffff;--tx:#10162f;--mu:#56608a;--gl:rgba(255,255,255,.7);--bd:rgba(16,22,47,.14);--sh:0 20px 50px rgba(40,50,110,.18)}
*{box-sizing:border-box;margin:0}
html{scroll-behavior:smooth;scroll-padding-top:76px}
body{font-family:system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;background:var(--bg);color:var(--tx);line-height:1.6;overflow-x:hidden;
background-image:radial-gradient(900px 500px at 15% -10%,color-mix(in srgb,var(--a2) 22%,transparent),transparent),radial-gradient(800px 500px at 100% 10%,color-mix(in srgb,var(--a1) 16%,transparent),transparent)}
body:before{content:"";position:fixed;inset:0;pointer-events:none;z-index:0;background-image:linear-gradient(var(--bd) 1px,transparent 1px),linear-gradient(90deg,var(--bd) 1px,transparent 1px);background-size:46px 46px;opacity:.35;animation:grid 14s linear infinite;mask-image:radial-gradient(circle at 50% 30%,#000,transparent 75%);-webkit-mask-image:radial-gradient(circle at 50% 30%,#000,transparent 75%)}
@keyframes grid{to{background-position:0 46px,46px 0}}
a{color:inherit;text-decoration:none}button,input,select,textarea{font:inherit;color:inherit}
button{cursor:pointer;border:0;background:none}
.calm *,.calm *:before,.calm *:after{animation:none!important;transition:none!important;scroll-behavior:auto!important}
#loader{position:fixed;inset:0;z-index:100;background:var(--bg);display:grid;place-content:center;justify-items:center;gap:14px;transition:opacity .6s,visibility .6s}
#loader.off{opacity:0;visibility:hidden}
.ring{width:64px;height:64px;border-radius:50%;border:3px solid var(--bd);border-top-color:var(--a1);border-right-color:var(--a2);animation:spin 1s linear infinite}
@keyframes spin{to{transform:rotate(360deg)}}
#bar{position:fixed;top:0;left:0;height:3px;width:0;background:linear-gradient(90deg,var(--a1),var(--a2));z-index:60;box-shadow:0 0 12px var(--a1)}
#glow{position:fixed;width:420px;height:420px;margin:-210px 0 0 -210px;border-radius:50%;pointer-events:none;z-index:1;background:radial-gradient(circle,color-mix(in srgb,var(--a1) 22%,transparent),transparent 65%);opacity:0;transition:opacity .3s;mix-blend-mode:screen}
header{position:fixed;top:0;left:0;right:0;z-index:50;display:flex;align-items:center;justify-content:space-between;gap:12px;padding:12px max(16px,4vw);transition:background .3s,backdrop-filter .3s,border-color .3s;border-bottom:1px solid transparent}
header.sc{background:color-mix(in srgb,var(--bg) 70%,transparent);backdrop-filter:blur(16px);-webkit-backdrop-filter:blur(16px);border-color:var(--bd)}
.logo{display:flex;align-items:center;gap:10px;font-weight:800;letter-spacing:.04em}
.logo i{width:22px;height:22px;border-radius:7px;background:conic-gradient(from 180deg,var(--a1),var(--a2),var(--a1));box-shadow:0 0 18px var(--a1)}
#links{position:relative;display:flex;gap:4px;padding:4px;border-radius:999px;background:var(--gl);border:1px solid var(--bd);backdrop-filter:blur(10px)}
#links a{position:relative;z-index:1;padding:7px 15px;border-radius:999px;font-size:14px;color:var(--mu);transition:color .2s}
#links a.on,#links a:hover{color:var(--tx)}
#ind{position:absolute;top:4px;bottom:4px;left:0;border-radius:999px;background:color-mix(in srgb,var(--a1) 22%,transparent);border:1px solid color-mix(in srgb,var(--a1) 50%,transparent);transition:left .35s cubic-bezier(.3,1.3,.5,1),width .35s}
.tools{display:flex;gap:6px}
.ib{width:38px;height:38px;border-radius:12px;background:var(--gl);border:1px solid var(--bd);display:grid;place-items:center;font-size:15px;transition:transform .2s,border-color .2s}
.ib:hover{transform:translateY(-2px);border-color:var(--a1)}
#burger{display:none}
#drawer{position:fixed;inset:0 0 0 auto;width:min(300px,82vw);z-index:70;background:var(--bg2);border-left:1px solid var(--bd);padding:80px 22px 22px;display:flex;flex-direction:column;gap:6px;transform:translateX(105%);transition:transform .35s;box-shadow:var(--sh)}
#drawer.open{transform:none}
#drawer a{padding:13px 14px;border-radius:12px;font-size:17px}#drawer a:hover{background:var(--gl)}
#scrim{position:fixed;inset:0;background:rgba(0,0,0,.55);z-index:65;opacity:0;visibility:hidden;transition:.3s}
#scrim.on{opacity:1;visibility:visible}
section{position:relative;z-index:2;padding:96px max(16px,5vw) 40px;max-width:1180px;margin:0 auto}
.rv{opacity:0;transform:translateY(28px);transition:opacity .7s,transform .7s}.rv.in{opacity:1;transform:none}
h2{font-size:clamp(28px,4.5vw,44px);line-height:1.1;margin-bottom:8px;letter-spacing:-.02em}
.sub{color:var(--mu);max-width:60ch;margin-bottom:28px}
.eyebrow{font:600 12px/1 ui-monospace,Menlo,monospace;letter-spacing:.2em;text-transform:uppercase;color:var(--a1);margin-bottom:12px;display:block}
#home{min-height:100svh;display:grid;align-items:center;padding-top:110px;max-width:none;overflow:hidden}
#hcv{position:absolute;inset:0;width:100%;height:100%;z-index:0;pointer-events:none}
.hero{position:relative;z-index:2;max-width:1180px;margin:0 auto;width:100%;display:grid;grid-template-columns:1.15fr .85fr;gap:30px;align-items:center}
h1{font-size:clamp(40px,8vw,88px);line-height:1;letter-spacing:-.04em;font-weight:800}
h1 .w{display:inline-block;opacity:0;transform:translateY(40px) rotateX(-50deg);animation:wi .9s cubic-bezier(.2,.9,.2,1) forwards}
@keyframes wi{to{opacity:1;transform:none}}
h1 .g{background:linear-gradient(100deg,var(--a1),var(--a2));-webkit-background-clip:text;background-clip:text;color:transparent}
.lead{margin:22px 0 28px;font-size:clamp(16px,2vw,20px);color:var(--mu);max-width:46ch}
.cta{display:flex;flex-wrap:wrap;gap:12px}
.btn{position:relative;overflow:hidden;padding:13px 24px;border-radius:14px;font-weight:600;border:1px solid var(--bd);background:var(--gl);backdrop-filter:blur(8px);transition:transform .2s,box-shadow .2s}
.btn:hover{transform:translateY(-2px)}
.btn.p{background:linear-gradient(120deg,var(--a1),var(--a2));color:#050814;border-color:transparent;box-shadow:0 10px 34px color-mix(in srgb,var(--a1) 40%,transparent)}
.rp{position:absolute;border-radius:50%;background:rgba(255,255,255,.45);transform:scale(0);animation:rp .6s ease-out forwards;pointer-events:none}
@keyframes rp{to{transform:scale(4);opacity:0}}
.clock{margin-top:30px;display:inline-flex;align-items:center;gap:10px;padding:8px 14px;border-radius:12px;border:1px solid var(--bd);background:var(--gl);font:500 14px ui-monospace,Menlo,monospace}
.clock b{color:var(--a1);font-size:18px}
.orbw{position:relative;aspect-ratio:1;max-width:440px;width:100%;margin:auto;transform:translate(calc(var(--px,0)*18px),calc(var(--py,0)*18px));transition:transform .15s}
.orb{position:absolute;inset:16%;border-radius:50%;background:radial-gradient(circle at 32% 28%,#fff 0,var(--a1) 18%,var(--a2) 58%,#0a0f26 100%);box-shadow:0 0 90px color-mix(in srgb,var(--a1) 55%,transparent),inset -20px -30px 60px rgba(0,0,0,.55);animation:fl 6s ease-in-out infinite}
@keyframes fl{50%{transform:translateY(-14px) scale(1.03)}}
.rg{position:absolute;inset:3%;border-radius:50%;border:1px solid color-mix(in srgb,var(--a1) 55%,transparent);animation:spin 18s linear infinite}
.rg:nth-child(2){inset:-4%;border-color:color-mix(in srgb,var(--a2) 55%,transparent);animation-duration:26s;animation-direction:reverse;border-style:dashed}
.rg:after{content:"";position:absolute;top:-5px;left:50%;width:10px;height:10px;border-radius:50%;background:var(--a1);box-shadow:0 0 14px var(--a1)}
.fl{position:absolute;width:46px;height:46px;border:1px solid var(--a1);border-radius:12px;opacity:.6;animation:fl 7s ease-in-out infinite;transform:translate(calc(var(--px,0)*-26px),calc(var(--py,0)*-26px))}
.fl.a{top:6%;right:6%;transform:rotate(20deg)}.fl.b{bottom:10%;left:2%;border-color:var(--a2);border-radius:50%;animation-delay:-2s}.fl.c{bottom:2%;right:18%;width:28px;height:28px;animation-delay:-4s}
.scr{position:absolute;bottom:22px;left:50%;transform:translateX(-50%);z-index:3;display:grid;justify-items:center;gap:6px;font-size:11px;letter-spacing:.2em;color:var(--mu);text-transform:uppercase}
.scr i{width:22px;height:36px;border:1.5px solid var(--mu);border-radius:12px;position:relative}
.scr i:after{content:"";position:absolute;left:50%;top:6px;width:3px;height:7px;margin-left:-1.5px;border-radius:2px;background:var(--a1);animation:sd 1.6s infinite}
@keyframes sd{60%{transform:translateY(12px);opacity:0}}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(250px,1fr));gap:18px}
.card{position:relative;border-radius:20px;padding:22px;background:var(--gl);border:1px solid var(--bd);backdrop-filter:blur(14px);-webkit-backdrop-filter:blur(14px);box-shadow:var(--sh);transition:transform .15s,border-color .3s;transform-style:preserve-3d;overflow:hidden}
.card:before{content:"";position:absolute;inset:0;border-radius:inherit;padding:1px;background:conic-gradient(from var(--ang,0deg),transparent 0 70%,var(--a1),var(--a2),transparent);-webkit-mask:linear-gradient(#000 0 0) content-box,linear-gradient(#000 0 0);-webkit-mask-composite:xor;mask-composite:exclude;animation:bd 6s linear infinite;opacity:.8;pointer-events:none}
@property --ang{syntax:"<angle>";inherits:false;initial-value:0deg}
@keyframes bd{to{--ang:360deg}}
.card h3{margin-bottom:6px;font-size:19px}.card p{color:var(--mu);font-size:15px}
.ico{width:44px;height:44px;border-radius:14px;margin-bottom:14px;display:grid;place-items:center;font-weight:800;color:#050814;background:linear-gradient(135deg,var(--a1),var(--a2))}
.lab{display:grid;grid-template-columns:1fr 280px;gap:18px}
.cvw{position:relative;border-radius:20px;overflow:hidden;border:1px solid var(--bd);background:#02040c;min-height:340px}
.cvw canvas{width:100%;height:100%;display:block;position:absolute;inset:0;touch-action:none}
.pan{border-radius:20px;padding:20px;background:var(--gl);border:1px solid var(--bd);backdrop-filter:blur(14px);display:grid;gap:14px;align-content:start}
label.rg2{display:grid;gap:6px;font-size:13px;color:var(--mu)}label.rg2 b{color:var(--tx);float:right}
input[type=range]{width:100%;accent-color:var(--a1)}
input[type=color]{width:100%;height:36px;border:1px solid var(--bd);border-radius:10px;background:none;padding:2px}
input[type=text],input[type=search],select,textarea{width:100%;padding:11px 14px;border-radius:12px;background:var(--gl);border:1px solid var(--bd);outline:0}
input:focus,select:focus,textarea:focus{border-color:var(--a1);box-shadow:0 0 0 3px color-mix(in srgb,var(--a1) 25%,transparent)}
select option{background:var(--bg2);color:var(--tx)}
.tabs{display:flex;gap:6px;margin-bottom:18px;flex-wrap:wrap}
.tab{padding:9px 18px;border-radius:12px;background:var(--gl);border:1px solid var(--bd);color:var(--mu)}
.tab.on{color:#050814;background:linear-gradient(120deg,var(--a1),var(--a2));border-color:transparent;font-weight:600}
.pane{display:none}.pane.on{display:block;animation:wi .5s both}
.tg{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:18px}
.calc{display:grid;grid-template-columns:repeat(4,1fr);gap:8px}
.calc .d{grid-column:1/-1;text-align:right;font:600 30px ui-monospace,Menlo,monospace;padding:12px 14px;border-radius:12px;background:#02040c;color:var(--a1);overflow:hidden;min-height:60px}
.calc button{padding:14px 0;border-radius:12px;background:var(--gl);border:1px solid var(--bd);font-size:18px;transition:transform .1s,background .2s}
.calc button:active{transform:scale(.94)}.calc button.o{background:color-mix(in srgb,var(--a2) 30%,transparent)}.calc button.e{background:linear-gradient(120deg,var(--a1),var(--a2));color:#050814;font-weight:700}
.big{font:700 38px ui-monospace,Menlo,monospace;color:var(--a1);margin:6px 0 12px}
.row{display:flex;gap:8px;flex-wrap:wrap}.row>*{flex:1}
.sm{padding:9px 14px;border-radius:10px;background:var(--gl);border:1px solid var(--bd);font-size:14px}.sm:hover{border-color:var(--a1)}
ul.l{list-style:none;padding:0;display:grid;gap:8px;margin-top:12px;max-height:210px;overflow:auto}
ul.l li{display:flex;align-items:center;gap:10px;padding:8px 12px;border-radius:10px;background:var(--gl);border:1px solid var(--bd);font-size:14px}
ul.l li span{flex:1;word-break:break-word}ul.l li.done span{text-decoration:line-through;opacity:.5}
.fb{display:flex;gap:10px;flex-wrap:wrap;margin-bottom:20px}.fb input{flex:2;min-width:180px}.fb select{flex:1;min-width:130px}
.chips{display:flex;gap:8px;flex-wrap:wrap;margin-bottom:20px}
.chip{padding:7px 16px;border-radius:999px;border:1px solid var(--bd);background:var(--gl);font-size:14px;color:var(--mu)}.chip.on{border-color:var(--a1);color:var(--tx);background:color-mix(in srgb,var(--a1) 18%,transparent)}
.art{height:130px;border-radius:14px;margin:-6px -6px 14px;position:relative;overflow:hidden}
.art svg{width:100%;height:100%;display:block}
.tag{display:inline-block;font-size:11px;padding:3px 10px;border-radius:999px;border:1px solid var(--bd);color:var(--a1);margin-bottom:8px;letter-spacing:.06em}
.empty{text-align:center;color:var(--mu);padding:40px;grid-column:1/-1}
.acc{display:grid;gap:10px;max-width:820px}
.ai{border-radius:16px;background:var(--gl);border:1px solid var(--bd);overflow:hidden}
.ai button{width:100%;text-align:left;padding:16px 20px;font-weight:600;display:flex;justify-content:space-between;gap:10px}
.ai button:after{content:"+";color:var(--a1);font-size:22px;line-height:1;transition:transform .3s}.ai.on button:after{transform:rotate(45deg)}
.ai div{max-height:0;overflow:hidden;transition:max-height .4s;padding:0 20px;color:var(--mu)}.ai.on div{max-height:240px;padding-bottom:16px}
.stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:16px;margin-top:26px}
.stat{padding:22px;border-radius:18px;background:var(--gl);border:1px solid var(--bd);text-align:center}
.stat b{display:block;font-size:40px;background:linear-gradient(120deg,var(--a1),var(--a2));-webkit-background-clip:text;background-clip:text;color:transparent}.stat span{color:var(--mu);font-size:14px}
footer{position:relative;z-index:2;text-align:center;color:var(--mu);padding:50px 16px 60px;font-size:14px}
#top{position:fixed;right:18px;bottom:18px;z-index:40;width:48px;height:48px;border-radius:50%;background:linear-gradient(135deg,var(--a1),var(--a2));color:#050814;font-size:20px;font-weight:800;box-shadow:0 10px 30px color-mix(in srgb,var(--a1) 45%,transparent);opacity:0;transform:translateY(20px);pointer-events:none;transition:.3s}
#top.on{opacity:1;transform:none;pointer-events:auto}
.ov{position:fixed;inset:0;z-index:90;background:rgba(2,4,12,.7);backdrop-filter:blur(8px);display:grid;place-items:center;padding:16px;opacity:0;visibility:hidden;transition:.25s}
.ov.on{opacity:1;visibility:visible}
.mod{width:min(560px,100%);max-height:88vh;overflow:auto;border-radius:22px;padding:26px;background:var(--bg2);border:1px solid var(--bd);box-shadow:var(--sh);transform:scale(.94);transition:.25s;position:relative}
.ov.on .mod{transform:none}
.x{position:absolute;top:12px;right:12px;width:34px;height:34px;border-radius:10px;background:var(--gl);border:1px solid var(--bd)}
.mod h3{font-size:24px;margin-bottom:10px;padding-right:30px}.mod p{color:var(--mu);margin-bottom:12px}
.pal{align-self:start;margin-top:14vh}
.pal input{margin-bottom:10px;font-size:17px}
.pal ul{list-style:none;padding:0;display:grid;gap:4px;max-height:50vh;overflow:auto}
.pal li{padding:11px 14px;border-radius:12px;cursor:pointer;display:flex;justify-content:space-between;gap:10px}.pal li.on{background:color-mix(in srgb,var(--a1) 20%,transparent)}.pal li small{color:var(--mu)}
kbd{font:12px ui-monospace,Menlo,monospace;padding:2px 8px;border-radius:6px;border:1px solid var(--bd);background:var(--gl)}
.ks{display:grid;gap:8px}.ks div{display:flex;justify-content:space-between;gap:10px;color:var(--mu)}
#set{position:fixed;top:0;bottom:0;right:0;width:min(340px,92vw);z-index:80;background:var(--bg2);border-left:1px solid var(--bd);padding:26px 22px;transform:translateX(105%);transition:transform .35s;box-shadow:var(--sh);display:grid;gap:18px;align-content:start;overflow:auto}
#set.open{transform:none}
.sw{display:flex;justify-content:space-between;align-items:center;gap:10px}
.sw button{width:48px;height:28px;border-radius:99px;background:var(--gl);border:1px solid var(--bd);position:relative;flex:none}.sw button:after{content:"";position:absolute;top:3px;left:3px;width:20px;height:20px;border-radius:50%;background:var(--mu);transition:.25s}.sw button.on{background:color-mix(in srgb,var(--a1) 40%,transparent)}.sw button.on:after{left:23px;background:var(--a1)}
#toasts{position:fixed;left:50%;bottom:22px;transform:translateX(-50%);z-index:120;display:grid;gap:8px;justify-items:center;pointer-events:none;width:max-content;max-width:92vw}
.toast{padding:11px 18px;border-radius:14px;background:var(--bg2);border:1px solid var(--a1);box-shadow:var(--sh);animation:wi .35s both;font-size:14px}
@media(max-width:860px){#links{display:none}#burger{display:grid}.hero{grid-template-columns:1fr}.orbw{max-width:300px;order:-1}.lab{grid-template-columns:1fr}.cvw{min-height:300px}#home{padding-top:96px}}
@media(max-width:480px){section{padding-top:78px}.logo span{display:none}}
</style>
</head>
<body>
<div id="loader"><div class="ring"></div><b id="lp">0%</b></div>
<div id="bar"></div><div id="glow"></div>
<header id="nav">
  <a class="logo" href="#home"><i></i><span id="logoT"></span></a>
  <nav id="links"><span id="ind"></span></nav>
  <div class="tools">
    <button class="ib" id="pal" title="Command palette (Ctrl+K)" aria-label="Command palette">&#8984;</button>
    <button class="ib" id="theme" title="Toggle theme (T)" aria-label="Toggle theme">&#9680;</button>
    <button class="ib" id="setb" title="Settings" aria-label="Settings">&#9881;</button>
    <button class="ib" id="burger" aria-label="Menu">&#9776;</button>
  </div>
</header>
<div id="scrim"></div>
<aside id="drawer"></aside>

<main>
<section id="home">
  <canvas id="hcv"></canvas>
  <div class="hero">
    <div>
      <span class="eyebrow" id="eye">Online &middot; Offline-ready</span>
      <h1 id="h1"></h1>
      <p class="lead" id="lead"></p>
      <div class="cta"><button class="btn p" data-go="#features">Explore</button><button class="btn" data-go="#lab">Open the Lab</button></div>
      <div class="clock"><span>LIVE</span><b id="clk">--:--:--</b><span id="dt"></span></div>
    </div>
    <div class="orbw"><div class="fl a"></div><div class="fl b"></div><div class="fl c"></div><div class="rg"></div><div class="rg"></div><div class="orb"></div></div>
  </div>
  <div class="scr"><i></i>Scroll</div>
</section>

<section id="features">
  <span class="eyebrow rv">Features</span><h2 class="rv">Built to feel instant</h2>
  <p class="sub rv">Every piece below is real and working. Tilt a card, search the gallery, or press <kbd>Ctrl</kbd> + <kbd>K</kbd>.</p>
  <div class="grid" id="fgrid"></div>
</section>

<section id="lab">
  <span class="eyebrow rv">Interactive Lab</span><h2 class="rv">Particle playground</h2>
  <p class="sub rv">Drag across the canvas to attract particles. Use the sliders to reshape the swarm.</p>
  <div class="lab rv">
    <div class="cvw"><canvas id="lcv"></canvas></div>
    <div class="pan">
      <label class="rg2">Particles <b id="vN">90</b><input type="range" id="sN" min="10" max="300" value="90"></label>
      <label class="rg2">Speed <b id="vS">1.0</b><input type="range" id="sS" min="0" max="5" step=".1" value="1"></label>
      <label class="rg2">Size <b id="vZ">2</b><input type="range" id="sZ" min="1" max="6" step=".5" value="2"></label>
      <label class="rg2">Link distance <b id="vL">110</b><input type="range" id="sL" min="30" max="220" value="110"></label>
      <label class="rg2">Particle colour<input type="color" id="cA"></label>
      <label class="rg2">Line colour<input type="color" id="cB"></label>
      <div class="row"><button class="sm" id="lrand">Randomize</button><button class="sm" id="lreset">Reset</button></div>
    </div>
  </div>
</section>

<section id="tools">
  <span class="eyebrow rv">Mini tools</span><h2 class="rv">Everything in one pocket</h2>
  <p class="sub rv">Notes and tasks are saved on this device.</p>
  <div class="tabs rv" id="ttabs"></div>
  <div class="rv">
    <div class="pane on" id="p-calc"><div class="tg"><div class="card"><h3>Calculator</h3><div class="calc" id="calc"></div></div><div class="card"><h3>Live clock</h3><div class="big" id="clk2">--:--:--</div><p id="dt2"></p><h3 style="margin-top:18px">Progress</h3><p id="prg">Scroll progress: 0%</p></div></div></div>
    <div class="pane" id="p-sw"><div class="card" style="max-width:480px"><h3>Stopwatch</h3><div class="big" id="swd">00:00.00</div><div class="row"><button class="sm" id="swg">Start</button><button class="sm" id="swl">Lap</button><button class="sm" id="swr">Reset</button></div><ul class="l" id="swlaps"></ul></div></div>
    <div class="pane" id="p-notes"><div class="card" style="max-width:640px"><h3>Notes</h3><textarea id="note" rows="8" placeholder="Type anything. It saves automatically."></textarea><p id="nst" style="margin-top:8px;font-size:13px"></p></div></div>
    <div class="pane" id="p-tasks"><div class="card" style="max-width:560px"><h3>Task list</h3><div class="row"><input type="text" id="tin" placeholder="Add a task and press Enter" style="flex:3"><button class="sm" id="tadd">Add</button></div><ul class="l" id="tl"></ul><p id="tc" style="margin-top:10px;font-size:13px"></p></div></div>
  </div>
</section>

<section id="gallery">
  <span class="eyebrow rv">Gallery</span><h2 class="rv">Browse the collection</h2>
  <p class="sub rv">Search, filter by category and sort. Tap a card to preview.</p>
  <div class="fb rv"><input type="search" id="q" placeholder="Search..." aria-label="Search"><select id="so" aria-label="Sort"><option value="n">Newest first</option><option value="a">Name A-Z</option><option value="z">Name Z-A</option></select></div>
  <div class="chips rv" id="chips"></div>
  <div class="grid" id="ggrid"></div>
</section>

<section id="about">
  <span class="eyebrow rv">About</span><h2 class="rv">Who we are</h2>
  <p class="sub rv" id="abt"></p>
  <div class="stats" id="stats"></div>
  <h2 class="rv" style="margin-top:56px;font-size:clamp(24px,3.4vw,34px)">Questions</h2>
  <div class="acc rv" id="acc" style="margin-top:14px"></div>
</section>
</main>
<footer id="foot"></footer>
<button id="top" aria-label="Back to top">&uarr;</button>

<div class="ov" id="mov"><div class="mod"><button class="x" data-close aria-label="Close">&#10005;</button><div id="mbody"></div></div></div>
<div class="ov" id="pov"><div class="mod pal"><input type="text" id="pin" placeholder="Type a command..." autocomplete="off"><ul id="plist"></ul></div></div>
<div class="ov" id="kov"><div class="mod"><button class="x" data-close aria-label="Close">&#10005;</button><h3>Keyboard shortcuts</h3><div class="ks">
<div><span>Command palette</span><span><kbd>Ctrl</kbd> <kbd>K</kbd> or <kbd>/</kbd></span></div>
<div><span>Toggle theme</span><kbd>T</kbd></div><div><span>Settings</span><kbd>S</kbd></div>
<div><span>Jump to section</span><span><kbd>1</kbd>-<kbd>6</kbd></span></div>
<div><span>This help</span><kbd>?</kbd></div><div><span>Close any panel</span><kbd>Esc</kbd></div></div></div></div>
<aside id="set"><button class="x" id="setx" aria-label="Close settings" style="position:absolute;top:12px;right:12px;width:34px;height:34px;border-radius:10px;background:var(--gl);border:1px solid var(--bd)">&#10005;</button>
<h3>Settings</h3>
<div class="sw"><span>Light theme</span><button id="swT" aria-label="Light theme"></button></div>
<div class="sw"><span>Reduce motion</span><button id="swM" aria-label="Reduce motion"></button></div>
<div class="sw"><span>Sound effects</span><button id="swA" aria-label="Sound effects"></button></div>
<div class="sw"><span>Cursor light</span><button id="swC" aria-label="Cursor light"></button></div>
<label class="rg2">Background particles <b id="vB">60</b><input type="range" id="sB" min="0" max="160" value="60"></label>
<label class="rg2">Accent colour<select id="acs"><option value="">Default</option><option value="cyan">Cyan</option><option value="violet">Violet</option><option value="green">Green</option><option value="orange">Orange</option><option value="pink">Pink</option><option value="blue">Blue</option></select></label>
<button class="btn" id="kb">Keyboard shortcuts</button><button class="btn" id="rs">Reset all settings</button></aside>
<div id="toasts" aria-live="polite"></div>

<script>
"use strict";
const SITE=/*SITE*/null;
const $=(q,r=document)=>r.querySelector(q),$$=(q,r=document)=>[...r.querySelectorAll(q)];
const store={get(k,d){try{const v=localStorage.getItem("y2b_"+k);return v===null?d:JSON.parse(v)}catch(e){return d}},set(k,v){try{localStorage.setItem("y2b_"+k,JSON.stringify(v))}catch(e){}}};
const mk=(t,c,x)=>{const e=document.createElement(t);if(c)e.className=c;if(x!=null)e.textContent=x;return e};
const root=document.documentElement,hov=matchMedia("(hover:hover)").matches;
const ACC={cyan:["#22d3ee","#8b5cf6"],violet:["#8b5cf6","#22d3ee"],green:["#34d399","#22d3ee"],orange:["#fb923c","#f43f5e"],pink:["#f472b6","#8b5cf6"],blue:["#60a5fa","#a78bfa"]};
const DEF={light:false,calm:matchMedia("(prefers-reduced-motion:reduce)").matches,sound:false,cursor:true,bg:60,accent:""};
let cfg=Object.assign({},DEF,store.get("cfg",{}));
function save(){store.set("cfg",cfg)}

/* toast + sound */
function toast(m){const t=mk("div","toast",m);$("#toasts").appendChild(t);setTimeout(()=>{t.style.opacity=0;t.style.transition="opacity .4s"},2400);setTimeout(()=>t.remove(),2900)}
let AC=null;function beep(f=520,d=.07){if(!cfg.sound)return;try{AC=AC||new(window.AudioContext||window.webkitAudioContext)();const o=AC.createOscillator(),g=AC.createGain();o.frequency.value=f;o.type="sine";g.gain.value=.05;o.connect(g);g.connect(AC.destination);o.start();g.gain.exponentialRampToValueAtTime(.0001,AC.currentTime+d);o.stop(AC.currentTime+d)}catch(e){}}

/* settings apply */
function applySettings(){
  root.dataset.theme=cfg.light?"light":"dark";root.classList.toggle("calm",!!cfg.calm);
  const c=ACC[cfg.accent]||ACC[SITE.accent]||ACC.cyan;root.style.setProperty("--a1",c[0]);root.style.setProperty("--a2",c[1]);
  $("#swT").classList.toggle("on",cfg.light);$("#swM").classList.toggle("on",cfg.calm);$("#swA").classList.toggle("on",cfg.sound);$("#swC").classList.toggle("on",cfg.cursor);
  $("#sB").value=cfg.bg;$("#vB").textContent=cfg.bg;$("#acs").value=cfg.accent;
}

/* content */
document.title=SITE.title;$("#logoT").textContent=SITE.title.toUpperCase();$("#lead").textContent=SITE.tagline;$("#abt").textContent=SITE.about;
$("#foot").textContent=SITE.title+" - made offline, runs anywhere.";
const words=SITE.title.split(/\s+/);const h1=$("#h1");
["Welcome to"].concat(words).forEach((w,i)=>{const s=mk("span","w"+(i?" g":""),w);s.style.animationDelay=(.5+i*.14)+"s";h1.appendChild(s);h1.appendChild(document.createTextNode(" "))});
const SECS=[["home","Home"],["features","Features"],["lab","Lab"],["tools","Tools"],["gallery","Gallery"],["about","About"]];
SECS.forEach(([id,n])=>{const a=mk("a","",n);a.href="#"+id;$("#links").appendChild(a);const b=mk("a","",n);b.href="#"+id;b.addEventListener("click",closeDrawer);$("#drawer").appendChild(b)});
SITE.features.forEach((f,i)=>{const c=mk("div","card tilt rv");const ic=mk("div","ico",String(i+1));c.append(ic,mk("h3","",f[0]),mk("p","",f[1]));$("#fgrid").appendChild(c)});
SITE.faq.forEach((f,i)=>{const d=mk("div","ai rv"),b=mk("button","",f[0]),p=mk("div","",f[1]);b.setAttribute("aria-expanded","false");b.addEventListener("click",()=>{const on=!d.classList.contains("on");$$(".ai").forEach(x=>{x.classList.remove("on");$("button",x).setAttribute("aria-expanded","false")});if(on){d.classList.add("on");b.setAttribute("aria-expanded","true")}beep(on?640:420)});d.append(b,p);$("#acc").appendChild(d)});
SITE.stats.forEach(s=>{const d=mk("div","stat rv");const b=mk("b","","0");b.dataset.to=s[1];d.append(b,mk("span","",s[0]));$("#stats").appendChild(d)});

/* scroll: bar, header, back-to-top, active link, reveal, counters */
const links=$$("#links a"),ind=$("#ind");let active=0;
function moveInd(){const a=links[active];if(a){ind.style.left=a.offsetLeft+"px";ind.style.width=a.offsetWidth+"px"}links.forEach((l,i)=>l.classList.toggle("on",i===active))}
function onScroll(){
  const y=scrollY,max=document.documentElement.scrollHeight-innerHeight,p=max>0?y/max:0;
  $("#bar").style.width=(p*100)+"%";$("#nav").classList.toggle("sc",y>30);$("#top").classList.toggle("on",y>500);$("#prg").textContent="Scroll progress: "+Math.round(p*100)+"%";
  let cur=0;SECS.forEach(([id],i)=>{const e=document.getElementById(id);if(e&&e.getBoundingClientRect().top<innerHeight*.4)cur=i});
  if(cur!==active){active=cur;moveInd()}
}
addEventListener("scroll",onScroll,{passive:true});addEventListener("resize",moveInd);
const io="IntersectionObserver"in window?new IntersectionObserver(es=>es.forEach(e=>{if(e.isIntersecting){e.target.classList.add("in");io.unobserve(e.target);$$("[data-to]",e.target).forEach(count)}}),{threshold:.15}):null;
function count(el){const to=+el.dataset.to||0,t0=performance.now(),d=cfg.calm?1:1300;(function s(t){const k=Math.min(1,(t-t0)/d);el.textContent=Math.round(to*(1-Math.pow(1-k,3)));if(k<1)requestAnimationFrame(s)})(t0)}
function observeAll(){$$(".rv:not(.in)").forEach(e=>{if(io)io.observe(e);else{e.classList.add("in");$$("[data-to]",e).forEach(count)}})}
$("#top").addEventListener("click",()=>{scrollTo({top:0,behavior:cfg.calm?"auto":"smooth"});beep(700)});
document.addEventListener("click",e=>{const g=e.target.closest("[data-go]");if(g){const t=$(g.dataset.go);t&&t.scrollIntoView({behavior:cfg.calm?"auto":"smooth"});beep()}
  const b=e.target.closest(".btn");if(b){const r=b.getBoundingClientRect(),s=Math.max(r.width,r.height),x=mk("span","rp");x.style.cssText="width:"+s+"px;height:"+s+"px;left:"+(e.clientX-r.left-s/2)+"px;top:"+(e.clientY-r.top-s/2)+"px";b.appendChild(x);setTimeout(()=>x.remove(),650)}});

/* drawer */
function openDrawer(){$("#drawer").classList.add("open");$("#scrim").classList.add("on")}
function closeDrawer(){$("#drawer").classList.remove("open");$("#scrim").classList.remove("on")}
$("#burger").addEventListener("click",()=>$("#drawer").classList.contains("open")?closeDrawer():openDrawer());
$("#scrim").addEventListener("click",()=>{closeDrawer();closeSettings()});

/* overlays */
function openOv(id){closeAllOv();$("#"+id).classList.add("on")}
function closeAllOv(){$$(".ov").forEach(o=>o.classList.remove("on"))}
$$(".ov").forEach(o=>o.addEventListener("click",e=>{if(e.target===o||e.target.closest("[data-close]"))o.classList.remove("on")}));
function modal(title,body,tag){const b=$("#mbody");b.textContent="";if(tag)b.appendChild(mk("span","tag",tag));b.appendChild(mk("h3","",title));(Array.isArray(body)?body:[body]).forEach(x=>x instanceof Node?b.appendChild(x):b.appendChild(mk("p","",x)));openOv("mov")}
function openSettings(){$("#set").classList.add("open");$("#scrim").classList.add("on")}
function closeSettings(){$("#set").classList.remove("open");if(!$("#drawer").classList.contains("open"))$("#scrim").classList.remove("on")}
$("#setb").addEventListener("click",openSettings);$("#setx").addEventListener("click",closeSettings);
$("#theme").addEventListener("click",toggleTheme);
function toggleTheme(){cfg.light=!cfg.light;save();applySettings();toast(cfg.light?"Light theme":"Dark theme");beep(600)}
$("#swT").onclick=toggleTheme;
$("#swM").onclick=()=>{cfg.calm=!cfg.calm;save();applySettings();toast(cfg.calm?"Motion reduced":"Motion on")};
$("#swA").onclick=()=>{cfg.sound=!cfg.sound;save();applySettings();toast(cfg.sound?"Sound on":"Sound off");beep(660)};
$("#swC").onclick=()=>{cfg.cursor=!cfg.cursor;save();applySettings()};
$("#sB").oninput=e=>{cfg.bg=+e.target.value;save();applySettings()};
$("#acs").onchange=e=>{cfg.accent=e.target.value;save();applySettings();toast("Accent updated")};
$("#rs").onclick=()=>{cfg=Object.assign({},DEF);save();applySettings();toast("Settings reset")};
$("#kb").onclick=()=>{closeSettings();openOv("kov")};

/* command palette */
const CMDS=[...SECS.map(([id,n],i)=>({n:"Go to "+n,k:String(i+1),f:()=>$("#"+id).scrollIntoView({behavior:cfg.calm?"auto":"smooth"})})),
 {n:"Toggle theme",k:"T",f:toggleTheme},{n:"Open settings",k:"S",f:openSettings},{n:"Keyboard shortcuts",k:"?",f:()=>openOv("kov")},
 {n:"Toggle sound",f:()=>$("#swA").click()},{n:"Toggle reduced motion",f:()=>$("#swM").click()},{n:"Add a task",f:()=>{$("#tools").scrollIntoView();tab("tasks");setTimeout(()=>$("#tin").focus(),400)}},
 {n:"Start stopwatch",f:()=>{$("#tools").scrollIntoView();tab("sw");swToggle()}},{n:"Back to top",f:()=>scrollTo({top:0})}];
let psel=0,pres=[];
function pfill(){const q=$("#pin").value.toLowerCase();pres=CMDS.filter(c=>c.n.toLowerCase().includes(q));psel=Math.min(psel,Math.max(0,pres.length-1));const u=$("#plist");u.textContent="";
  pres.forEach((c,i)=>{const li=mk("li",i===psel?"on":"");li.append(mk("span","",c.n),mk("small","",c.k||""));li.onclick=()=>prun(c);u.appendChild(li)});if(!pres.length)u.appendChild(mk("li","","No matches"))}
function prun(c){closeAllOv();c.f();beep(560)}
function openPal(){openOv("pov");$("#pin").value="";psel=0;pfill();setTimeout(()=>$("#pin").focus(),60)}
$("#pal").onclick=openPal;$("#pin").oninput=()=>{psel=0;pfill()};
$("#pin").addEventListener("keydown",e=>{if(e.key==="ArrowDown"){psel=Math.min(pres.length-1,psel+1);pfill();e.preventDefault()}else if(e.key==="ArrowUp"){psel=Math.max(0,psel-1);pfill();e.preventDefault()}else if(e.key==="Enter"&&pres[psel])prun(pres[psel])});
addEventListener("keydown",e=>{
  const typing=/^(INPUT|TEXTAREA|SELECT)$/.test((e.target.tagName||""));
  if((e.ctrlKey||e.metaKey)&&e.key.toLowerCase()==="k"){e.preventDefault();openPal();return}
  if(e.key==="Escape"){closeAllOv();closeDrawer();closeSettings();return}
  if(typing||e.ctrlKey||e.metaKey||e.altKey)return;
  if(e.key==="/"){e.preventDefault();openPal()}else if(e.key==="?"){openOv("kov")}else if(e.key.toLowerCase()==="t"){toggleTheme()}else if(e.key.toLowerCase()==="s"){openSettings()}
  else if(/^[1-6]$/.test(e.key)){$("#"+SECS[+e.key-1][0]).scrollIntoView({behavior:cfg.calm?"auto":"smooth"})}
});

/* pointer: parallax, cursor light, tilt */
addEventListener("pointermove",e=>{
  root.style.setProperty("--px",(e.clientX/innerWidth-.5).toFixed(3));root.style.setProperty("--py",(e.clientY/innerHeight-.5).toFixed(3));
  const g=$("#glow");if(hov&&cfg.cursor){g.style.opacity=1;g.style.left=e.clientX+"px";g.style.top=e.clientY+"px"}else g.style.opacity=0;
  if(!cfg.calm){const c=e.target.closest&&e.target.closest(".tilt");if(c){const r=c.getBoundingClientRect(),x=(e.clientX-r.left)/r.width-.5,y=(e.clientY-r.top)/r.height-.5;c.style.transform="perspective(700px) rotateY("+(x*12)+"deg) rotateX("+(-y*12)+"deg) translateZ(4px)"}}
},{passive:true});
document.addEventListener("pointerout",e=>{const c=e.target.closest&&e.target.closest(".tilt");if(c&&!c.contains(e.relatedTarget))c.style.transform=""});

/* particles */
function particles(cv,get,interactive){
  const c=cv.getContext("2d");if(!c)return{};let w=0,h=0,P=[],mx=-1e4,my=-1e4,vis=true,dpr=Math.min(devicePixelRatio||1,2);
  function size(){const r=cv.getBoundingClientRect();w=cv.width=Math.max(1,r.width*dpr|0);h=cv.height=Math.max(1,r.height*dpr|0)}
  size();addEventListener("resize",size);
  if("IntersectionObserver"in window)new IntersectionObserver(e=>{vis=e[0].isIntersecting}).observe(cv);
  const tgt=interactive?cv:window;
  tgt.addEventListener("pointermove",e=>{const r=cv.getBoundingClientRect();mx=(e.clientX-r.left)*dpr;my=(e.clientY-r.top)*dpr},{passive:true});
  tgt.addEventListener("pointerleave",()=>{mx=my=-1e4});
  function frame(){
    requestAnimationFrame(frame);if(!vis)return;const o=get();
    while(P.length<o.n)P.push({x:Math.random()*w,y:Math.random()*h,vx:Math.random()-.5,vy:Math.random()-.5});P.length=o.n;
    c.clearRect(0,0,w,h);const sp=cfg.calm&&!interactive?0:o.s,L=o.l*dpr;
    for(const p of P){p.x+=p.vx*sp*dpr;p.y+=p.vy*sp*dpr;if(p.x<0||p.x>w)p.vx*=-1;if(p.y<0||p.y>h)p.vy*=-1;
      const dx=mx-p.x,dy=my-p.y,d=Math.hypot(dx,dy);if(d<160*dpr&&d>1&&sp){p.x+=dx/d*.6*dpr*(interactive?2:1);p.y+=dy/d*.6*dpr*(interactive?2:1)}}
    c.fillStyle=o.a;for(const p of P){c.beginPath();c.arc(p.x,p.y,o.z*dpr,0,6.283);c.fill()}
    c.strokeStyle=o.b;c.lineWidth=dpr*.7;
    for(let i=0;i<P.length;i++)for(let j=i+1;j<P.length;j++){const d=Math.hypot(P[i].x-P[j].x,P[i].y-P[j].y);if(d<L){c.globalAlpha=1-d/L;c.beginPath();c.moveTo(P[i].x,P[i].y);c.lineTo(P[j].x,P[j].y);c.stroke()}}
    c.globalAlpha=1;
  }
  frame();return{reset(){P=[]}};
}
const css=n=>getComputedStyle(root).getPropertyValue(n).trim();
particles($("#hcv"),()=>({n:cfg.bg,s:.6,z:1.4,l:120,a:css("--a1"),b:css("--a2")}),false);
const LAB={n:90,s:1,z:2,l:110,a:"#22d3ee",b:"#8b5cf6"};const LAB0=Object.assign({},LAB);
const labp=particles($("#lcv"),()=>LAB,true);
function labUI(){[["sN","n","vN"],["sS","s","vS"],["sZ","z","vZ"],["sL","l","vL"]].forEach(([i,k,v])=>{$("#"+i).value=LAB[k];$("#"+v).textContent=LAB[k]});$("#cA").value=LAB.a;$("#cB").value=LAB.b}
[["sN","n","vN"],["sS","s","vS"],["sZ","z","vZ"],["sL","l","vL"]].forEach(([i,k,v])=>$("#"+i).oninput=e=>{LAB[k]=+e.target.value;$("#"+v).textContent=LAB[k]});
$("#cA").oninput=e=>LAB.a=e.target.value;$("#cB").oninput=e=>LAB.b=e.target.value;
$("#lreset").onclick=()=>{Object.assign(LAB,LAB0);labUI();toast("Lab reset")};
$("#lrand").onclick=()=>{const hx=()=>"#"+[0,0,0].map(()=>(Math.random()*180+75|0).toString(16).padStart(2,"0")).join("");LAB.a=hx();LAB.b=hx();LAB.n=Math.random()*200+40|0;LAB.s=+(Math.random()*3+.3).toFixed(1);labUI();toast("Randomized");beep(740)};
labUI();

/* tabs (tools) */
const TT=[["calc","Calculator"],["sw","Stopwatch"],["notes","Notes"],["tasks","Tasks"]];
function tab(id){$$("#ttabs .tab").forEach(t=>t.classList.toggle("on",t.dataset.t===id));$$(".pane").forEach(p=>p.classList.toggle("on",p.id==="p-"+id));beep(480)}
TT.forEach(([id,n],i)=>{const b=mk("button","tab"+(i?"":" on"),n);b.dataset.t=id;b.onclick=()=>tab(id);$("#ttabs").appendChild(b)});

/* calculator (no eval) */
(function(){
  let cur="0",prev=null,op=null,fresh=true;const disp=mk("div","d","0");$("#calc").appendChild(disp);
  const show=()=>disp.textContent=cur.length>12?(+cur).toPrecision(9):cur;
  const calc=(a,b,o)=>o==="+"?a+b:o==="-"?a-b:o==="*"?a*b:o==="/"?(b===0?NaN:a/b):b;
  const fmt=n=>isFinite(n)?String(+n.toPrecision(12)):"Error";
  function press(k){
    if(/\d/.test(k)){cur=(fresh||cur==="0")?k:cur+k;fresh=false}
    else if(k==="."){if(fresh){cur="0.";fresh=false}else if(!cur.includes("."))cur+="."}
    else if(k==="C"){cur="0";prev=op=null;fresh=true}
    else if(k==="⌫"){cur=cur.length>1&&!fresh?cur.slice(0,-1):"0"}
    else if(k==="±"){if(cur!=="0")cur=cur[0]==="-"?cur.slice(1):"-"+cur}
    else if(k==="%"){cur=fmt(parseFloat(cur)/100)}
    else if(k==="="){if(op!==null&&prev!==null){cur=fmt(calc(prev,parseFloat(cur),op));prev=op=null;fresh=true}}
    else{if(op!==null&&!fresh){cur=fmt(calc(prev,parseFloat(cur),op))}prev=parseFloat(cur);op=k;fresh=true}
    show();beep(500+Math.random()*100,.04);
  }
  ["C","±","%","/","7","8","9","*","4","5","6","-","1","2","3","+","0",".","⌫","="].forEach(k=>{const b=mk("button",/[\/*\-+]/.test(k)?"o":k==="="?"e":"",k==="*"?"×":k==="/"?"÷":k);b.onclick=()=>press(k);$("#calc").appendChild(b)});
  addEventListener("keydown",e=>{if(!$("#p-calc").classList.contains("on")||/^(INPUT|TEXTAREA|SELECT)$/.test(e.target.tagName||"")||e.ctrlKey||e.metaKey)return;const k=e.key==="Enter"?"=":e.key==="Backspace"?"⌫":e.key;if(/^[0-9.+\-*\/%=]$|^⌫$/.test(k)){if(k==="/")return;press(k)}});
})();

/* clock */
function tick(){const d=new Date(),t=d.toLocaleTimeString([], {hour12:false}),dt=d.toLocaleDateString([], {weekday:"short",month:"short",day:"numeric"});["#clk","#clk2"].forEach(s=>$(s).textContent=t);["#dt","#dt2"].forEach(s=>$(s).textContent=dt)}
tick();setInterval(tick,1000);

/* stopwatch */
let swRun=false,swT0=0,swAcc=0,swId=0,laps=[];
const swfmt=ms=>{const m=Math.floor(ms/60000),s=Math.floor(ms/1000)%60,c=Math.floor(ms/10)%100;return String(m).padStart(2,"0")+":"+String(s).padStart(2,"0")+"."+String(c).padStart(2,"0")}
function swLoop(){$("#swd").textContent=swfmt(swAcc+(swRun?performance.now()-swT0:0));if(swRun)swId=requestAnimationFrame(swLoop)}
function swToggle(){if(swRun){swAcc+=performance.now()-swT0;swRun=false;$("#swg").textContent="Start"}else{swT0=performance.now();swRun=true;$("#swg").textContent="Stop";swLoop()}beep(600)}
$("#swg").onclick=swToggle;
$("#swl").onclick=()=>{const t=swAcc+(swRun?performance.now()-swT0:0);if(t<=0)return;laps.unshift(swfmt(t));$("#swlaps").textContent="";laps.forEach((l,i)=>{const li=mk("li","");li.append(mk("span","","Lap "+(laps.length-i)),mk("span","",l));$("#swlaps").appendChild(li)})};
$("#swr").onclick=()=>{swRun=false;cancelAnimationFrame(swId);swAcc=0;laps=[];$("#swlaps").textContent="";$("#swg").textContent="Start";$("#swd").textContent="00:00.00"};

/* notes */
const note=$("#note");note.value=store.get("note","");let nt=0;
note.addEventListener("input",()=>{$("#nst").textContent="Saving...";clearTimeout(nt);nt=setTimeout(()=>{store.set("note",note.value);$("#nst").textContent="Saved "+new Date().toLocaleTimeString()},400)});

/* tasks */
let tasks=store.get("tasks",[]);
function drawTasks(){const u=$("#tl");u.textContent="";tasks.forEach((t,i)=>{const li=mk("li",t.d?"done":"");const cb=mk("input");cb.type="checkbox";cb.checked=!!t.d;cb.onchange=()=>{t.d=cb.checked;store.set("tasks",tasks);drawTasks();beep(cb.checked?700:450)};
  const x=mk("button","sm","✕");x.setAttribute("aria-label","Delete task");x.onclick=()=>{tasks.splice(i,1);store.set("tasks",tasks);drawTasks()};li.append(cb,mk("span","",t.t),x);u.appendChild(li)});
  const d=tasks.filter(t=>t.d).length;$("#tc").textContent=tasks.length?d+" of "+tasks.length+" done":"Nothing yet. Add your first task."}
function addTask(){const v=$("#tin").value.trim();if(!v)return;tasks.push({t:v.slice(0,120),d:false});store.set("tasks",tasks);$("#tin").value="";drawTasks();toast("Task added");beep(620)}
$("#tadd").onclick=addTask;$("#tin").addEventListener("keydown",e=>{if(e.key==="Enter")addTask()});drawTasks();

/* gallery */
const ITEMS=SITE.items.map((x,i)=>({n:x[0],c:x[1],d:x[2],i}));let cat="All";
const cats=["All"].concat([...new Set(ITEMS.map(x=>x.c))]);
cats.forEach(c=>{const b=mk("button","chip"+(c===cat?" on":""),c);b.onclick=()=>{cat=c;$$(".chip").forEach(x=>x.classList.toggle("on",x===b));drawG();beep(520)};$("#chips").appendChild(b)});
function art(seed){let h=0;for(const ch of seed)h=(h*31+ch.charCodeAt(0))|0;const r=n=>{h=(h*1103515245+12345)&0x7fffffff;return h%n};const hue=r(360),s=document.createElementNS("http://www.w3.org/2000/svg","svg");s.setAttribute("viewBox","0 0 200 130");s.setAttribute("preserveAspectRatio","xMidYMid slice");
  let x='<defs><linearGradient id="g'+h+'" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="hsl('+hue+',80%,55%)"/><stop offset="1" stop-color="hsl('+(hue+70)+',80%,30%)"/></linearGradient></defs><rect width="200" height="130" fill="url(#g'+h+')"/>';
  for(let k=0;k<6;k++)x+='<circle cx="'+r(200)+'" cy="'+r(130)+'" r="'+(10+r(40))+'" fill="hsla('+(hue+r(120))+',90%,70%,.25)"/>';
  for(let k=0;k<3;k++)x+='<rect x="'+r(160)+'" y="'+r(100)+'" width="'+(20+r(50))+'" height="'+(20+r(50))+'" rx="8" fill="none" stroke="rgba(255,255,255,.4)" transform="rotate('+r(60)+' 100 65)"/>';
  s.innerHTML=x;return s}
function drawG(){const q=$("#q").value.trim().toLowerCase(),so=$("#so").value;let L=ITEMS.filter(x=>(cat==="All"||x.c===cat)&&(!q||(x.n+" "+x.c+" "+x.d).toLowerCase().includes(q)));
  L.sort((a,b)=>so==="a"?a.n.localeCompare(b.n):so==="z"?b.n.localeCompare(a.n):b.i-a.i);const g=$("#ggrid");g.textContent="";
  if(!L.length){g.appendChild(mk("div","empty","No results. Try another search."));return}
  L.forEach(x=>{const c=mk("div","card tilt in");c.tabIndex=0;const a=mk("div","art");a.appendChild(art(x.n));c.append(a,mk("span","tag",x.c),mk("h3","",x.n),mk("p","",x.d));
    const open=()=>{const big=mk("div","art");big.style.height="220px";big.style.margin="0 0 14px";big.appendChild(art(x.n));modal(x.n,[big,x.d,"Category: "+x.c+" - Item #"+(x.i+1)],"Preview");beep(560)};c.onclick=open;c.onkeydown=e=>{if(e.key==="Enter")open()};g.appendChild(c)})}
$("#q").oninput=drawG;$("#so").onchange=drawG;drawG();

/* boot */
applySettings();observeAll();moveInd();onScroll();
let lp=0;const lt=setInterval(()=>{lp=Math.min(100,lp+Math.ceil(Math.random()*22));$("#lp").textContent=lp+"%";if(lp>=100){clearInterval(lt);setTimeout(()=>{$("#loader").classList.add("off");toast("Welcome - press Ctrl+K or / for the command palette");moveInd()},200)}},cfg.calm?10:110);
addEventListener("load",moveInd);
</script>
</body>
</html>
'''


# ═══════════════════ ready-made mini apps (no model needed) ═══════════════════
APP_COLORS = {"cyan": "#22e0ff", "blue": "#4da3ff", "red": "#ff4d6d", "green": "#39ff88", "purple": "#a66bff",
              "violet": "#a66bff", "pink": "#ff6bd6", "orange": "#ff9f43", "yellow": "#ffd93d"}
_APP_KINDS = [
    ("calculator", r"calculator|calc"),
    ("todo", r"to-?do(?:\s+(?:list|app))?|task\s+(?:list|manager)"),
    ("stopwatch", r"stop\s*watch"),
    ("timer", r"countdown(?:\s+timer)?|timer"),
    ("clock", r"clock"),
]
# words that may sit in front of the app name without changing what it is ("glowing calculator")
_PRE_OK = set("a an the web html modern simple glowing glow neon cool basic beautiful responsive nice new stylish sleek "
              "dark light digital mobile working full me my great awesome javascript css futuristic live live-time "
              "online interactive fancy pretty small tiny animated minimal elegant premium colorful colourful "
              "create make build write generate for".split()) | set(APP_COLORS)


def detect_app(text: str):
    """Return 'calculator' / 'todo' / 'stopwatch' / 'timer' / 'clock' for plain requests, else None.
    'birthday calculator' or 'alarm clock' are NOT plain, so they still go to the model."""
    low = (text or "").lower()
    if len(low) > 400:
        return None
    for kind, pat in _APP_KINDS:
        m = re.search(r"\b(%s)\b" % pat, low)
        if not m:
            continue
        before = re.findall(r"[a-z0-9\-]+", low[:m.start()])
        if before and before[-1] not in _PRE_OK:
            continue
        return kind
    return None


def app_accent(text: str, default: str = "#22e0ff") -> str:
    for w in re.findall(r"[a-z]+", (text or "").lower()):
        if w in APP_COLORS:
            return APP_COLORS[w]
    m = re.search(r"#[0-9a-fA-F]{6}\b", text or "")
    return m.group(0) if m else default


def build_app(kind: str, text: str = "", accent: str | None = None) -> str:
    kind = kind if kind in APPS else "calculator"
    acc = accent or app_accent(text)
    title, body, script = APPS[kind]
    out = APP_SHELL.replace("__TITLE__", title).replace("__ACC__", acc).replace("__KIND__", kind)
    return out.replace("__BODY__", body).replace("__SCRIPT__", script)


APP_SHELL = r'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="generator" content="y2b-app:__KIND__:__ACC__">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>__TITLE__</title>
<style>
:root{--ac:__ACC__;--bg:#05070f;--card:rgba(255,255,255,.06);--bd:rgba(255,255,255,.14);--tx:#eaf0ff;--mu:#8b97bd}
*{box-sizing:border-box;margin:0;-webkit-tap-highlight-color:transparent}
html,body{height:100%}
body{min-height:100svh;display:grid;place-items:center;padding:16px;font-family:system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;color:var(--tx);
background:radial-gradient(700px 420px at 20% 0%,color-mix(in srgb,var(--ac) 20%,transparent),transparent),radial-gradient(600px 420px at 100% 100%,color-mix(in srgb,var(--ac) 14%,transparent),#05070f 70%),var(--bg)}
.app{width:min(380px,100%);padding:22px;border-radius:26px;background:var(--card);border:1px solid var(--bd);backdrop-filter:blur(16px);-webkit-backdrop-filter:blur(16px);
box-shadow:0 0 0 1px color-mix(in srgb,var(--ac) 30%,transparent),0 0 38px color-mix(in srgb,var(--ac) 35%,transparent),0 30px 70px rgba(0,0,0,.55);animation:pop .6s cubic-bezier(.2,.9,.2,1) both}
@keyframes pop{from{opacity:0;transform:translateY(18px) scale(.97)}}
h1{font-size:13px;letter-spacing:.28em;text-transform:uppercase;color:var(--ac);margin-bottom:14px;text-shadow:0 0 12px var(--ac)}
button,input{font:inherit;color:inherit}
button{cursor:pointer;border:1px solid var(--bd);background:rgba(255,255,255,.07);border-radius:16px;transition:transform .12s,box-shadow .2s,background .2s}
button:hover{box-shadow:0 0 18px color-mix(in srgb,var(--ac) 55%,transparent);border-color:var(--ac)}
button:active{transform:scale(.94)}
button.pri{background:var(--ac);color:#04060d;font-weight:700;border-color:transparent;box-shadow:0 0 24px color-mix(in srgb,var(--ac) 60%,transparent)}
input[type=text],input[type=number]{width:100%;padding:12px 14px;border-radius:14px;border:1px solid var(--bd);background:rgba(0,0,0,.3);outline:0}
input:focus{border-color:var(--ac);box-shadow:0 0 14px color-mix(in srgb,var(--ac) 50%,transparent)}
.big{font:700 clamp(40px,12vw,56px)/1.1 ui-monospace,Menlo,Consolas,monospace;color:var(--ac);text-shadow:0 0 22px var(--ac);text-align:center;margin:10px 0 18px;letter-spacing:.02em}
.row{display:flex;gap:10px}.row>*{flex:1}
.row button{padding:13px 0}
.mu{color:var(--mu);font-size:14px;text-align:center}
.calc{display:grid;grid-template-columns:repeat(4,1fr);gap:10px}
.calc .scr{grid-column:1/-1;text-align:right;padding:14px 16px;border-radius:18px;background:rgba(0,0,0,.4);border:1px solid var(--bd);min-height:92px;display:grid;align-content:end;overflow:hidden}
.calc .h{color:var(--mu);font-size:14px;min-height:20px;font-family:ui-monospace,Menlo,monospace}
.calc .v{font:700 36px ui-monospace,Menlo,monospace;color:var(--ac);text-shadow:0 0 18px var(--ac);word-break:break-all}
.calc button{height:62px;font-size:22px}.calc .op{color:var(--ac)}
ul{list-style:none;padding:0;display:grid;gap:8px;margin-top:14px;max-height:48vh;overflow:auto}
li{display:flex;align-items:center;gap:10px;padding:10px 12px;border-radius:14px;background:rgba(255,255,255,.05);border:1px solid var(--bd)}
li span{flex:1;word-break:break-word}li.done span{text-decoration:line-through;opacity:.45}
li input{width:20px;height:20px;accent-color:var(--ac)}li button{width:34px;height:34px;border-radius:10px;padding:0}
.ring{display:block;margin:6px auto 4px;width:210px;height:210px}
.ring circle{fill:none;stroke-width:9}.ring .t{stroke:rgba(255,255,255,.09)}.ring .p{stroke:var(--ac);stroke-linecap:round;transform:rotate(-90deg);transform-origin:50% 50%;filter:drop-shadow(0 0 8px var(--ac));transition:stroke-dashoffset .25s linear}
.ring text{fill:var(--ac);font:700 38px ui-monospace,Menlo,monospace;text-anchor:middle;dominant-baseline:central}
.fields{display:flex;gap:10px;margin-bottom:12px}.fields label{flex:1;font-size:12px;color:var(--mu);display:grid;gap:5px}
.clk{width:220px;height:220px;display:block;margin:4px auto 6px}
.clk .f{fill:rgba(0,0,0,.35);stroke:var(--ac);stroke-width:2;filter:drop-shadow(0 0 8px var(--ac))}
.clk .m{stroke:var(--mu);stroke-width:2}.clk .h,.clk .mn{stroke:var(--tx);stroke-linecap:round}.clk .s{stroke:var(--ac);stroke-linecap:round;filter:drop-shadow(0 0 4px var(--ac))}
</style>
</head>
<body>
<main class="app"><h1>__TITLE__</h1>
__BODY__
</main>
<script>
"use strict";
const $=q=>document.querySelector(q);
let AC=null;function beep(f,d){try{AC=AC||new(window.AudioContext||window.webkitAudioContext)();const o=AC.createOscillator(),g=AC.createGain();o.frequency.value=f||520;g.gain.value=.06;o.connect(g);g.connect(AC.destination);o.start();g.gain.exponentialRampToValueAtTime(.0001,AC.currentTime+(d||.08));o.stop(AC.currentTime+(d||.08))}catch(e){}}
const store={get(k,d){try{const v=localStorage.getItem("y2b_app_"+k);return v===null?d:JSON.parse(v)}catch(e){return d}},set(k,v){try{localStorage.setItem("y2b_app_"+k,JSON.stringify(v))}catch(e){}}};
__SCRIPT__
</script>
</body>
</html>
'''

_CALC_BODY = '<div class="calc" id="calc"><div class="scr"><div class="h" id="h">&nbsp;</div><div class="v" id="v">0</div></div></div>'
_CALC_JS = r'''
let cur="0",prev=null,op=null,fresh=true,hist="";
const sym={"*":"×","/":"÷","-":"−","+":"+"};
const fmt=n=>isFinite(n)?String(+n.toPrecision(12)):"Error";
const calc=(a,b,o)=>o==="+"?a+b:o==="-"?a-b:o==="*"?a*b:o==="/"?(b===0?NaN:a/b):b;
function show(){$("#v").textContent=cur.length>13?(+cur).toPrecision(9):cur;$("#h").innerHTML=hist||"&nbsp;"}
function press(k){
  if(cur==="Error"&&k!=="C"){cur="0"}
  if(/^\d$/.test(k)){cur=(fresh||cur==="0")?k:cur+k;fresh=false}
  else if(k==="."){if(fresh){cur="0.";fresh=false}else if(!cur.includes("."))cur+="."}
  else if(k==="C"){cur="0";prev=op=null;fresh=true;hist=""}
  else if(k==="⌫"){cur=(!fresh&&cur.length>1)?cur.slice(0,-1):"0"}
  else if(k==="±"){if(cur!=="0"&&cur!=="Error")cur=cur[0]==="-"?cur.slice(1):"-"+cur}
  else if(k==="%"){cur=fmt(parseFloat(cur)/100);fresh=true}
  else if(k==="="){if(op!==null&&prev!==null){const b=parseFloat(cur);hist=fmt(prev)+" "+sym[op]+" "+fmt(b)+" =";cur=fmt(calc(prev,b,op));prev=op=null;fresh=true}}
  else{if(op!==null&&!fresh){cur=fmt(calc(prev,parseFloat(cur),op))}prev=parseFloat(cur);op=k;fresh=true;hist=fmt(prev)+" "+sym[k]}
  show();beep(480+Math.random()*120,.04);
}
["C","±","%","/","7","8","9","*","4","5","6","-","1","2","3","+","0",".","⌫","="].forEach(k=>{
  const b=document.createElement("button");b.textContent=sym[k]&&k!=="+"?sym[k]:k;if(/[\/*\-+]/.test(k))b.className="op";if(k==="=")b.className="pri";b.onclick=()=>press(k);$("#calc").appendChild(b)});
addEventListener("keydown",e=>{if(e.ctrlKey||e.metaKey)return;const k=e.key==="Enter"?"=":e.key==="Backspace"?"⌫":e.key==="Escape"?"C":e.key;if(/^[0-9.+\-*\/%=C]$|^⌫$/.test(k)){e.preventDefault();press(k)}});
show();
'''
_TODO_BODY = '<div class="row"><input type="text" id="in" placeholder="Add a task..." maxlength="120" style="flex:4"><button class="pri" id="add" style="flex:1">+</button></div><ul id="ls"></ul><p class="mu" id="ct" style="margin-top:12px"></p>'
_TODO_JS = r'''
let tasks=store.get("tasks",[]);
function draw(){const u=$("#ls");u.textContent="";tasks.forEach((t,i)=>{const li=document.createElement("li");if(t.d)li.className="done";
  const c=document.createElement("input");c.type="checkbox";c.checked=!!t.d;c.onchange=()=>{t.d=c.checked;store.set("tasks",tasks);draw();beep(c.checked?700:450)};
  const s=document.createElement("span");s.textContent=t.t;const x=document.createElement("button");x.textContent="✕";x.setAttribute("aria-label","Delete");x.onclick=()=>{tasks.splice(i,1);store.set("tasks",tasks);draw()};
  li.append(c,s,x);u.appendChild(li)});const d=tasks.filter(t=>t.d).length;$("#ct").textContent=tasks.length?d+" of "+tasks.length+" done":"Nothing here yet. Add your first task."}
function add(){const v=$("#in").value.trim();if(!v)return;tasks.push({t:v,d:false});store.set("tasks",tasks);$("#in").value="";draw();beep(620)}
$("#add").onclick=add;$("#in").addEventListener("keydown",e=>{if(e.key==="Enter")add()});draw();
'''
_SW_BODY = '<div class="big" id="d">00:00.00</div><div class="row"><button class="pri" id="go">Start</button><button id="lap">Lap</button><button id="rs">Reset</button></div><ul id="ls"></ul>'
_SW_JS = r'''
let run=false,t0=0,acc=0,raf=0,laps=[];
const f=ms=>{const m=Math.floor(ms/6e4),s=Math.floor(ms/1e3)%60,c=Math.floor(ms/10)%100;return String(m).padStart(2,"0")+":"+String(s).padStart(2,"0")+"."+String(c).padStart(2,"0")};
const now=()=>acc+(run?performance.now()-t0:0);
function loop(){$("#d").textContent=f(now());if(run)raf=requestAnimationFrame(loop)}
$("#go").onclick=()=>{if(run){acc+=performance.now()-t0;run=false;$("#go").textContent="Start"}else{t0=performance.now();run=true;$("#go").textContent="Stop";loop()}beep(600)};
$("#lap").onclick=()=>{const t=now();if(t<=0)return;laps.unshift(f(t));const u=$("#ls");u.textContent="";laps.forEach((l,i)=>{const li=document.createElement("li");const a=document.createElement("span");a.textContent="Lap "+(laps.length-i);const b=document.createElement("span");b.style.cssText="flex:none;color:var(--ac)";b.textContent=l;li.append(a,b);u.appendChild(li)});beep(520)};
$("#rs").onclick=()=>{run=false;cancelAnimationFrame(raf);acc=0;laps=[];$("#ls").textContent="";$("#go").textContent="Start";$("#d").textContent="00:00.00"};
'''
_TIMER_BODY = ('<div class="fields"><label>Minutes<input type="number" id="mi" min="0" max="999" value="5"></label><label>Seconds<input type="number" id="se" min="0" max="59" value="0"></label></div>'
               '<svg class="ring" viewBox="0 0 120 120"><circle class="t" cx="60" cy="60" r="52"/><circle class="p" id="pg" cx="60" cy="60" r="52" stroke-dasharray="326.7" stroke-dashoffset="0"/><text x="60" y="60" id="tx" style="font-size:22px">05:00</text></svg>'
               '<p class="mu" id="st">Set a time and press Start.</p><div class="row" style="margin-top:12px"><button class="pri" id="go">Start</button><button id="rs">Reset</button></div>')
_TIMER_JS = r'''
let total=300,left=300,run=false,end=0,id=0;
const f=s=>String(Math.floor(s/60)).padStart(2,"0")+":"+String(s%60).padStart(2,"0");
function setFromInputs(){total=Math.max(1,(+$("#mi").value||0)*60+(+$("#se").value||0));left=total;if(!run){$("#st").textContent="Set a time and press Start.";$("#go").textContent="Start"}draw()}
function draw(){const s=Math.max(0,left);$("#tx").textContent=f(Math.ceil(s));$("#pg").style.strokeDashoffset=326.7*(1-(total?s/total:0))}
function tick(){left=(end-performance.now())/1000;if(left<=0){left=0;run=false;clearInterval(id);$("#go").textContent="Start";$("#st").textContent="Time is up!";draw();beep(880,.5);setTimeout(()=>beep(880,.5),600);return}draw()}
$("#go").onclick=()=>{if(run){run=false;clearInterval(id);$("#go").textContent="Resume";$("#st").textContent="Paused";return}
  if(left<=0)setFromInputs();end=performance.now()+left*1000;run=true;$("#go").textContent="Pause";$("#st").textContent="Running...";id=setInterval(tick,100);beep(600)};
$("#rs").onclick=()=>{run=false;clearInterval(id);$("#go").textContent="Start";$("#st").textContent="Set a time and press Start.";setFromInputs()};
["#mi","#se"].forEach(s=>$(s).addEventListener("input",()=>{if(!run){setFromInputs()}}));
setFromInputs();
'''
_CLOCK_BODY = ('<svg class="clk" viewBox="0 0 200 200"><circle class="f" cx="100" cy="100" r="94"/><g id="mk"></g>'
               '<line class="h" id="hh" x1="100" y1="100" x2="100" y2="58" stroke-width="6"/><line class="mn" id="mm" x1="100" y1="100" x2="100" y2="36" stroke-width="4"/>'
               '<line class="s" id="ss" x1="100" y1="112" x2="100" y2="26" stroke-width="2"/><circle cx="100" cy="100" r="5" fill="var(--ac)"/></svg>'
               '<div class="big" id="dg">--:--:--</div><p class="mu" id="dt"></p><div class="row" style="margin-top:12px"><button id="fm">24-hour</button></div>')
_CLOCK_JS = r'''
let h24=store.get("h24",true);
for(let i=0;i<60;i++){const a=i*6*Math.PI/180,l=i%5?4:10,x1=100+Math.sin(a)*(88-l),y1=100-Math.cos(a)*(88-l),x2=100+Math.sin(a)*88,y2=100-Math.cos(a)*88;
  const e=document.createElementNS("http://www.w3.org/2000/svg","line");e.setAttribute("class","m");e.setAttribute("x1",x1);e.setAttribute("y1",y1);e.setAttribute("x2",x2);e.setAttribute("y2",y2);$("#mk").appendChild(e)}
function tick(){const d=new Date(),s=d.getSeconds()+d.getMilliseconds()/1000,m=d.getMinutes()+s/60,h=(d.getHours()%12)+m/60;
  $("#ss").setAttribute("transform","rotate("+s*6+" 100 100)");$("#mm").setAttribute("transform","rotate("+m*6+" 100 100)");$("#hh").setAttribute("transform","rotate("+h*30+" 100 100)");
  $("#dg").textContent=d.toLocaleTimeString([],{hour12:!h24});$("#dt").textContent=d.toLocaleDateString([],{weekday:"long",year:"numeric",month:"long",day:"numeric"});$("#fm").textContent=h24?"Switch to 12-hour":"Switch to 24-hour"}
$("#fm").onclick=()=>{h24=!h24;store.set("h24",h24);tick();beep(560)};
setInterval(tick,100);tick();
'''
APPS = {
    "calculator": ("Calculator", _CALC_BODY, _CALC_JS),
    "todo": ("To-Do List", _TODO_BODY, _TODO_JS),
    "stopwatch": ("Stopwatch", _SW_BODY, _SW_JS),
    "timer": ("Countdown Timer", _TIMER_BODY, _TIMER_JS),
    "clock": ("Clock", _CLOCK_BODY, _CLOCK_JS),
}
