# Contributing to Y2B Agent

Thanks for helping! Y2B Agent is intentionally **one file, zero dependencies** so it installs anywhere in seconds.

## Ground rules
- Python standard library only (3.8+). No `pip install` requirements.
- Keep it Termux-friendly: small screens, no heavy output, no assumptions about root.
- Anything that writes files or runs commands must ask for confirmation (unless `--auto`).

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
