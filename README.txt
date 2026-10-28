Phrasebook
==========

Tired of reading "load-bearing" in every other Claude Code reply? Or "You're
absolutely right", "delve", "it's worth noting"? Asking nicely in CLAUDE.md
doesn't stick (see anthropics/claude-code#53454). Phrasebook enforces it with
hooks instead.

  * Replies: if Claude's final message uses a banned phrase, the stop is
    blocked once and Claude sends the same reply again, reworded. It's told
    not to redo any work, and it gets at most one retry per reply, so it
    can never loop.
  * Files: if a Write or Edit puts a banned phrase into a file, Claude is
    told which phrase and file, and it rewords just that spot.

One file of plain Python, no dependencies, MIT.

Install
-------
Inside Claude Code (2.1.275 or later):

  /plugin install phrasebook --marketplace minus1ms-dev/phrasebook

Choose your phrases
-------------------
Create ~/.claude/phrasebook.txt, one phrase per line:

  # my banned list
  load-bearing
  you're absolutely right
  delve
  re:\bleverag(e|es|ing)\b      # lines starting with re: are regexes

Matching ignores case, treats "load bearing" and "load-bearing" alike, accepts
both ' and ’, and only matches whole words. Without the file, the built-in
list is used: load-bearing, you're/you are absolutely right, delve/delving,
tapestry, it's worth noting, I hope this helps, great question.

Settings (environment variables)
--------------------------------
  PHRASEBOOK_FILE=/path/list.txt   use another phrase list
  PHRASEBOOK_DISABLE=1             turn it off for a session

Cost
----
Nothing extra when Claude behaves. When a phrase slips into a reply, the
rewording costs one short extra response.

Test
----
  python3 -m unittest discover -s tests -v

Support
-------
Phrasebook is free. If it saves your sanity, you can chip in:
https://minus1ms.gumroad.com/l/phrasebook
