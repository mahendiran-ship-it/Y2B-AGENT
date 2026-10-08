#!/usr/bin/env python3
"""
Tiny fake OpenAI-compatible model server used by the tests (and handy for developing
Y2B Agent without loading a real model).

    python tests/fake_server.py 8099
"""
import json
import sys
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

BUGGY = "```python\nprint(undefined_name)\n```"
FIXED = "```python\nprint('hello from fixed code')\n```"
BADHTML = ('```html\n<html><head><link rel="stylesheet" href="missing.css"></head>\n'
           '<body><script>document.getElementById("nope").innerText=1;</script></body></html>\n```')


def reply_for(messages):
    system = messages[0]["content"] if messages and messages[0]["role"] == "system" else ""
    last = messages[-1]["content"]
    if "code" in system.lower() and "programmer" in system.lower():
        if "failed" in last.lower() or "change requested" in last.lower():
            return FIXED
        if "broken-html" in last.lower():
            return BADHTML
        if "always-ok" in last.lower():
            return "```python\nprint('ok')\n```"
        return BUGGY
    if "<think>" in last:
        return "<think>hmm</think>done"
    if "make-note" in last:
        return "Creating it.\n[write:note.txt]\nhello note\n[/write]\n[run:cat note.txt]\n"
    if "TOOL RESULT" in last:
        return "All done, the note says hello."
    if "refuse-me" in last and "harmless" not in system:
        return "I'm sorry, but I can't assist with that request at all."
    if "refuse-me" in last:
        return "Sure, happy to help!"
    return "I am a fake model. You said: " + last[:40]


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def _json(self, code, obj):
        data = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        if self.path == "/health":
            return self._json(200, {"status": "ok"})
        if self.path == "/v1/models":
            return self._json(200, {"data": [{"id": "fake-model"}]})
        self._json(404, {})

    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))) or b"{}")
        if self.path != "/v1/chat/completions":
            return self._json(404, {})
        text = reply_for(body["messages"])
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.end_headers()
        # stream in small pieces so tag-splitting across chunks gets exercised
        for i in range(0, len(text), 3):
            piece = text[i:i + 3]
            self.wfile.write(("data: " + json.dumps({"choices": [{"delta": {"content": piece}}]}) + "\n\n").encode())
            self.wfile.flush()
            time.sleep(0.002)
        self.wfile.write(b"data: [DONE]\n\n")
        self.wfile.flush()


def serve(port):
    srv = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    return srv


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8099
    print("fake model server on http://127.0.0.1:%d" % port)
    serve(port).serve_forever()
