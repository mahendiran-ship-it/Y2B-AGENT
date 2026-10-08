"""Run with:  python -m unittest discover -s tests -v"""
import io
import os
import sys
import tempfile
import threading
import unittest
from contextlib import redirect_stdout

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
sys.path.insert(0, HERE)
os.environ["Y2B_HOME"] = tempfile.mkdtemp()

import y2b_agent as y2b  # noqa: E402
import fake_server  # noqa: E402


class StreamFilterTests(unittest.TestCase):
    def run_filter(self, text, step=2):
        f, out = y2b.StreamFilter(), []
        for i in range(0, len(text), step):
            out.append(f.feed(text[i:i + step]))
        out.append(f.flush())
        return "".join(out)

    def test_plain_text_untouched(self):
        self.assertEqual(self.run_filter("hello [world] <b>x</b>"), "hello [world] <b>x</b>")

    def test_hides_write_block_and_tags(self):
        txt = "Creating.\n[write:a.py]\nprint(1)\n[/write]\n[run:python a.py]\nDone."
        out = self.run_filter(txt)
        self.assertNotIn("print(1)", out)
        self.assertNotIn("[run", out)
        self.assertIn("Creating.", out)
        self.assertIn("Done.", out)

    def test_hides_think(self):
        self.assertEqual(self.run_filter("<think>secret plan</think>Answer").strip(), "Answer")

    def test_partial_tag_across_chunks(self):
        for step in (1, 2, 3, 5):
            out = self.run_filter("A[write:x.txt]body[/write]B", step)
            self.assertEqual(out, "AB")


class SpinnerTests(unittest.TestCase):
    def test_frame_never_wraps_on_narrow_screens(self):
        import time
        for cols in (24, 30, 40, 50, 80):
            sp = y2b.Spinner("writing emi_calculator_css.html")
            sp.t0 = time.time() - 31
            sp.info = "284 tok \u00b7 11.2 tok/s"
            for i in range(10):
                plain, _ = sp.frame(i, cols)
                self.assertLessEqual(len(plain), cols - 2, (cols, plain))


class ParserTests(unittest.TestCase):
    def test_events(self):
        r = "ok\n[write:a.py]\nprint(1)\n[run:python a.py]\n[/write]\n[run:python a.py]\n[ls:.]"
        ev = y2b.parse_events(r)
        self.assertEqual([e[0] for e in ev], ["write", "run", "ls"])  # run inside write is content

    def test_placeholders_ignored(self):
        self.assertEqual(y2b.parse_events("[run:COMMAND] [read:FILE]"), [])

    def test_unterminated_write(self):
        ev = y2b.parse_events("[write:a.txt]\nhello")
        self.assertEqual(ev[0][:2], ("write", "a.txt"))

    def test_refusal_regex(self):
        self.assertTrue(y2b.REFUSAL_RE.match("I'm sorry, but I can't assist with that."))
        self.assertFalse(y2b.REFUSAL_RE.match("Sure! Here you go."))

    def test_strip_think(self):
        self.assertEqual(y2b.strip_think("<think>x</think>hi"), "hi")


class ModelInfoTests(unittest.TestCase):
    def test_info(self):
        i = y2b.model_info("/x/qwen2.5-coder-1.5b-instruct-q4_k_m.gguf")
        self.assertEqual((i["family"], i["template"], i["params_b"], i["quant"]), ("qwen", "chatml", 1.5, "Q4_K_M"))
        i = y2b.model_info("/x/Llama-3.2-3B-Instruct-Q4_K_M.gguf")
        self.assertEqual((i["template"], i["params_b"]), ("llama3", 3.0))
        i = y2b.model_info("/x/gemma-2-2b-it-Q4_K_M.gguf")
        self.assertEqual((i["template"], i["params_b"]), ("gemma", 2.0))

    def test_templates(self):
        msgs = [{"role": "system", "content": "S"}, {"role": "user", "content": "U"}]
        p, stop = y2b.format_prompt("chatml", msgs)
        self.assertTrue(p.endswith("<|im_start|>assistant\n"))
        self.assertEqual(stop, ["<|im_end|>"])
        p, _ = y2b.format_prompt("gemma", msgs)
        self.assertIn("S\n\nU", p)  # system merged into first user turn
        p, _ = y2b.format_prompt("llama3", msgs)
        self.assertIn("<|eot_id|>", p)

    def test_auto_ctx_is_sane(self):
        self.assertIn(y2b.auto_ctx(900), (1024, 2048, 4096, 8192))


class AgentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.srv = fake_server.serve(0)
        cls.port = cls.srv.server_address[1]
        threading.Thread(target=cls.srv.serve_forever, daemon=True).start()

    @classmethod
    def tearDownClass(cls):
        cls.srv.shutdown()

    def make_agent(self, fix=3):
        be = y2b.OpenAIBackend("http://127.0.0.1:%d" % self.port)
        be.start()
        llm = y2b.LLM(be, 4096, 256, 0.2)
        work = tempfile.mkdtemp()
        tools = y2b.Tools(work, auto=True)
        return y2b.Agent(llm, tools, {"facts": []}, steps=4, fix=fix), work

    def handle(self, agent, text):
        buf = io.StringIO()
        with redirect_stdout(buf):
            agent.handle(text)
        return buf.getvalue()

    def test_backend_streams(self):
        be = y2b.OpenAIBackend("http://127.0.0.1:%d" % self.port)
        be.start()
        self.assertEqual(be.model_name, "fake-model")
        text = "".join(be.stream([{"role": "user", "content": "hi there"}], 50, 0.2))
        self.assertIn("You said: hi there", text)

    def test_greeting_fast_path(self):
        a, _ = self.make_agent()
        self.assertIn("Y2B", self.handle(a, "hi bro"))

    def test_tool_loop_write_and_run(self):
        a, work = self.make_agent()
        self.handle(a, "make-note please")
        with open(os.path.join(work, "note.txt")) as f:
            self.assertEqual(f.read().strip(), "hello note")

    def test_auto_fix_loop(self):
        a, work = self.make_agent(fix=3)
        out = self.handle(a, "create bug.py that prints something and run it")
        self.assertIn("auto-fix 1/3", out)
        with open(os.path.join(work, "bug.py")) as f:
            self.assertIn("hello from fixed code", f.read())
        self.assertIn("Auto-fixed", out)

    def test_auto_fix_disabled(self):
        a, work = self.make_agent(fix=0)
        out = self.handle(a, "create bug2.py that prints something and run it")
        self.assertNotIn("auto-fix", out)
        self.assertIn("failed", out)

    def test_syntax_check_without_run(self):
        a, work = self.make_agent()
        self.handle(a, "create calc.py with an addition function")  # buggy code is valid syntax -> no fix
        self.assertTrue(os.path.exists(os.path.join(work, "calc.py")))

    def test_refusal_retry(self):
        a, _ = self.make_agent()
        out = self.handle(a, "refuse-me")
        self.assertIn("happy to help", out)
        self.assertNotIn("can't assist", out)

    def test_think_hidden_in_chat(self):
        a, _ = self.make_agent()
        out = self.handle(a, "tell me <think> something")
        self.assertIn("done", out)
        self.assertNotIn("hmm", out)


    def test_infers_file_name_without_one_given(self):
        a, work = self.make_agent()
        self.assertEqual(a.infer_name("create a web based birthday calculator"), "birthday_calculator.html")
        self.assertEqual(a.infer_name("make a simple todo app"), "todo_app.py")
        self.handle(a, "create a web birthday calculator")
        self.assertTrue(os.path.exists(os.path.join(work, "birthday_calculator.html")))

    def test_html_opens_in_browser_when_asked(self):
        a, work = self.make_agent()
        opened = []
        a.open_in_browser = lambda n: opened.append(n) or True
        out = self.handle(a, "create a web birthday calculator and open it in chrome")
        self.assertEqual(opened, ["birthday_calculator.html"])
        self.assertIn("Opened in your browser", out)

    def test_html_not_opened_unless_asked(self):
        a, work = self.make_agent()
        opened = []
        a.open_in_browser = lambda n: opened.append(n) or True
        self.handle(a, "create a web landing page")
        self.assertEqual(opened, [])

    def test_questions_do_not_create_files(self):
        a, work = self.make_agent()
        self.handle(a, "how do I make a game")
        self.assertEqual(os.listdir(work), [])

    def test_local_http_server_serves_workspace(self):
        import urllib.request
        a, work = self.make_agent()
        with open(os.path.join(work, "x.html"), "w") as f:
            f.write("<h1>hi</h1>")
        a.tools.auto = True
        import y2b_agent as m
        orig = m.shutil.which
        m.shutil.which = lambda n: None  # no browser opener -> it just prints the URL
        try:
            buf = io.StringIO()
            with redirect_stdout(buf):
                self.assertTrue(a.open_in_browser("x.html"))
        finally:
            m.shutil.which = orig
        url = [w for w in buf.getvalue().split() if w.startswith("http://127.0.0.1")][0]
        import time
        time.sleep(0.5)
        self.assertIn("<h1>hi</h1>", urllib.request.build_opener(urllib.request.ProxyHandler({})).open(url, timeout=5).read().decode())
        a._http[0].terminate()

    def test_check_html_finds_common_blank_page_causes(self):
        a, work = self.make_agent()
        good = ("<html><body><div id=a></div><style>p{}</style>"
                "<script>document.getElementById('a').innerText='x';</script></body></html>")
        self.assertEqual(a.check_html("x.html", good)[0], 0)
        self.assertIn("missing.css", a.check_html("x.html", '<link rel="stylesheet" href="missing.css">')[1])
        self.assertIn("no element has it", a.check_html("x.html", "<script>document.getElementById('zz')</script>")[1])
        self.assertEqual(a.check_html("x.html", "<script>function f(){ if(1){ }</script>")[0], 1)
        self.assertEqual(a.check_html("x.html", '<script src="https://cdn.x/y.js"></script>')[0], 1)

    def test_broken_page_is_auto_fixed(self):
        a, work = self.make_agent()
        a.open_in_browser = lambda n: True
        out = self.handle(a, "create a broken-html page")
        self.assertIn("auto-fix", out)
        name = [f for f in os.listdir(work) if f.endswith(".html")][0]
        with open(os.path.join(work, name)) as f:
            self.assertNotIn("missing.css", f.read())

    def test_open_it_again_reopens_last_page(self):
        a, work = self.make_agent()
        opened = []
        a.open_in_browser = lambda n: opened.append(n) or True
        self.handle(a, "create a web landing page")
        self.handle(a, "open it again in my chrome")
        self.assertEqual(opened, ["landing_page.html"])

    def test_fix_it_rewrites_last_file_and_reopens(self):
        a, work = self.make_agent()
        opened = []
        a.open_in_browser = lambda n: opened.append(n) or True
        self.handle(a, "create a web landing page")
        out = self.handle(a, "it wont work open it again in my chrome")
        self.assertIn("Updating landing_page.html", out)
        with open(os.path.join(work, "landing_page.html")) as f:
            self.assertIn("hello from fixed code", f.read())
        self.assertEqual(opened, ["landing_page.html"])

    def test_unrelated_chat_does_not_trigger_edit(self):
        a, work = self.make_agent()
        self.handle(a, "create a web landing page")
        path = os.path.join(work, "landing_page.html")
        with open(path) as fh:
            before = fh.read()
        self.handle(a, "add 2 and 3")
        with open(path) as fh:
            self.assertEqual(fh.read(), before)

    def test_workspace_escape_refused(self):
        a, work = self.make_agent()
        r = a.tools.write("../../escape.txt", "x")
        self.assertTrue(r.startswith("REFUSED"))

    def test_history_trimming_alternates_roles(self):
        a, _ = self.make_agent()
        a.llm.ctx, a.llm.gen = 600, 100
        for i in range(30):
            a.hist.append(("user", "x" * 50))
            a.hist.append(("assistant", "y" * 50))
        msgs = a.build_messages()
        self.assertEqual(msgs[0]["role"], "system")
        self.assertEqual(msgs[1]["role"], "user")
        roles = [m["role"] for m in msgs[1:]]
        self.assertTrue(all(roles[i] != roles[i + 1] for i in range(len(roles) - 1)))


if __name__ == "__main__":
    unittest.main()
