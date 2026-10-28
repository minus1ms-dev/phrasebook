#!/usr/bin/env python3
"""Phrasebook: a Claude Code hook that bans phrases you're tired of reading.

Stop mode (default): if Claude's final reply uses a banned phrase, the stop is
blocked once and Claude restates the reply without it.
PostToolUse mode (--edits): if a Write/Edit puts a banned phrase into a file,
Claude is told which phrase and file so it can reword it.

Phrases come from $PHRASEBOOK_FILE, else ~/.claude/phrasebook.txt, else the
built-in list. One phrase per line; '#' starts a comment; a line starting with
're:' is a regular expression. Matching is case-insensitive on word boundaries.
Set PHRASEBOOK_DISABLE=1 to turn it off.
"""
import json, os, pathlib, re, sys

DEFAULTS = """\
load-bearing
you're absolutely right
you are absolutely right
delve
delving
tapestry
it's worth noting
i hope this helps
great question
"""


def load_phrases():
    src = os.environ.get("PHRASEBOOK_FILE") or str(pathlib.Path.home() / ".claude" / "phrasebook.txt")
    text = pathlib.Path(src).read_text() if os.path.isfile(src) else DEFAULTS
    pats = []
    for line in text.splitlines():
        line = line.split("#", 1)[0].strip() if not line.lstrip().startswith("re:") else line.strip()
        if not line:
            continue
        if line.startswith("re:"):
            pats.append((line[3:].strip(), re.compile(line[3:].strip(), re.I)))
        else:
            words = r"[\s\-]+".join(re.escape(w) for w in re.split(r"[\s\-]+", line.replace("’", "'")))
            pats.append((line, re.compile(rf"(?<![\w-]){words}(?![\w-])".replace("'", "['’]"), re.I)))
    return pats


def find(text, pats):
    return [label for label, rx in pats if rx.search(text or "")]


def last_reply(hook):
    msg = hook.get("last_assistant_message")
    if msg:
        return msg
    try:
        lines = pathlib.Path(hook["transcript_path"]).read_text().splitlines()
    except (KeyError, OSError):
        return ""
    for line in reversed(lines):
        try:
            e = json.loads(line)
        except ValueError:
            continue
        if e.get("type") == "assistant":
            parts = [b.get("text", "") for b in e.get("message", {}).get("content", []) if b.get("type") == "text"]
            if any(parts):
                return "\n".join(parts)
    return ""


def edited_text(hook):
    ti = hook.get("tool_input") or {}
    chunks = [ti.get("content"), ti.get("new_string")] + [e.get("new_string") for e in ti.get("edits") or []]
    return ti.get("file_path", "?"), "\n".join(c for c in chunks if c)


def main():
    if os.environ.get("PHRASEBOOK_DISABLE"):
        return 0
    hook = json.load(sys.stdin)
    pats = load_phrases()
    if "--edits" in sys.argv:
        path, text = edited_text(hook)
        hits = find(text, pats)
        if hits:
            print(f"Phrasebook: {path} now contains banned phrase(s): {', '.join(hits)}. "
                  "Reword those spots with plain language; change nothing else.", file=sys.stderr)
            return 2
        return 0
    if hook.get("stop_hook_active"):  # one rewrite per stop, never a loop
        return 0
    hits = find(last_reply(hook), pats)
    if hits:
        print(json.dumps({"decision": "block", "reason":
            f"Phrasebook: your last reply used banned phrase(s): {', '.join(hits)}. "
            "Send the same reply again, reworded without them. Don't redo any work or tool calls."}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
