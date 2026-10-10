# Contributing to Y2B Agent

Thanks for helping! The Y2B Agent core (`y2b_agent.py`) is intentionally **one file with zero dependencies** so it installs anywhere in seconds.
The optional offline document tools live in a separate module, `y2b_docs.py`.

## Ground rules
- `y2b_agent.py`: Python standard library only (3.8+). No `pip install` requirements.
- `y2b_docs.py` may import only reportlab, python-docx, python-pptx and openpyxl, and only lazily inside functions, so Y2B still starts when they are missing. No image libraries, no network calls.
- Keep it Termux-friendly: small screens, no heavy output, no assumptions about root.
- Anything that writes files or runs commands must ask for confirmation (unless `--auto`).
- Never run model-written code to build a document; the model only produces Markdown that is parsed as data.

## Dev setup
```bash
git clone https://github.com/mahendiran-ship-it/Y2B-AGENT && cd Y2B-AGENT
python -m unittest discover -s tests -v     # runs against a fake model server, no GPU/model needed
python tests/fake_server.py 8099 &          # fake OpenAI-compatible model
python y2b_agent.py --url http://127.0.0.1:8099
```

## Good first contributions
- Add a chat template for another model family (`format_prompt` + `FAMILIES`).
- More instant "no-model" commands (battery, time, notes ...).
- Better diff view before overwriting files.
- Translations of the README.

## Reporting a bug
Run `y2b --doctor` and paste the output, plus your model file name and the last lines of `~/.y2b/server.log`.

Made by : Mahzend
