"""Shared code for the Serenity tracker scripts.

config      settings shared by every step (aliases, stances, paths)
text        small text and time helpers
normalize   cleans data/classified.json before it goes on the page   (data)
claude_cli  calls the `claude` CLI with retries and JSON parsing     (data)
page        turns clean posts into index.html                         (page)
The page's own calculations live in web/calc.js, its drawing in web/view.js.
"""
