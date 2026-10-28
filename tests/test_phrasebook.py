"""Tests for Phrasebook: run the hook script as Claude Code would."""
import json, os, pathlib, subprocess, sys, tempfile, unittest

HOOK = pathlib.Path(__file__).resolve().parent.parent / "phrasebook" / "phrasebook.py"


def run(payload, *args, phrases=None):
    env = {**os.environ, "HOME": tempfile.mkdtemp()}
    env.pop("PHRASEBOOK_DISABLE", None)
    if phrases is not None:
        f = pathlib.Path(env["HOME"]) / "p.txt"; f.write_text(phrases); env["PHRASEBOOK_FILE"] = str(f)
    p = subprocess.run([sys.executable, str(HOOK), *args], input=json.dumps(payload), text=True, capture_output=True, env=env)
    return p.returncode, p.stdout, p.stderr


class StopMode(unittest.TestCase):
    def test_blocks_default_phrase(self):
        code, out, _ = run({"last_assistant_message": "This is the load-bearing part.", "stop_hook_active": False})
        self.assertEqual(json.loads(out)["decision"], "block")
        self.assertIn("load-bearing", json.loads(out)["reason"])

    def test_variants_match(self):
        for text in ("Load bearing wall", "You’re ABSOLUTELY right!", "let's delve in"):
            self.assertTrue(run({"last_assistant_message": text})[1], text)

    def test_clean_reply_passes(self):
        self.assertEqual(run({"last_assistant_message": "Done. Tests pass."})[1], "")

    def test_no_partial_word_match(self):
        self.assertEqual(run({"last_assistant_message": "non-load-bearingness and delveopment"})[1], "")

    def test_only_one_rewrite(self):
        self.assertEqual(run({"last_assistant_message": "load-bearing", "stop_hook_active": True})[1], "")

    def test_reads_transcript_when_no_message(self):
        t = pathlib.Path(tempfile.mkdtemp()) / "t.jsonl"
        t.write_text(json.dumps({"type": "assistant", "message": {"content": [{"type": "text", "text": "Great question!"}]}}) + "\n")
        self.assertIn("great question", run({"transcript_path": str(t)})[1])

    def test_custom_list_and_regex(self):
        phrases = "# mine\nsynergy\nre:\\bleverag(e|ing)\\b\n"
        self.assertTrue(run({"last_assistant_message": "We leverage it."}, phrases=phrases)[1])
        self.assertEqual(run({"last_assistant_message": "load-bearing"}, phrases=phrases)[1], "")

    def test_disable(self):
        env_payload = {"last_assistant_message": "load-bearing"}
        os.environ["PHRASEBOOK_DISABLE"] = "1"
        try:
            p = subprocess.run([sys.executable, str(HOOK)], input=json.dumps(env_payload), text=True, capture_output=True)
            self.assertEqual(p.stdout, "")
        finally:
            del os.environ["PHRASEBOOK_DISABLE"]


class EditMode(unittest.TestCase):
    def test_write_with_phrase_exits_2(self):
        code, _, err = run({"tool_name": "Write", "tool_input": {"file_path": "a.py", "content": "# delve into it\n"}}, "--edits")
        self.assertEqual(code, 2); self.assertIn("a.py", err); self.assertIn("delve", err)

    def test_multiedit(self):
        code, _, _ = run({"tool_input": {"file_path": "b", "edits": [{"new_string": "ok"}, {"new_string": "load bearing"}]}}, "--edits")
        self.assertEqual(code, 2)

    def test_clean_edit_passes(self):
        self.assertEqual(run({"tool_input": {"file_path": "c", "new_string": "x = 1"}}, "--edits")[0], 0)


if __name__ == "__main__":
    unittest.main()
