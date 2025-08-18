
# Example flows

## Build lesson from YouTube
1. `transcript.get(url)`
2. `vocab.extract(text, limit=15)`
3. `grammar.check(text, language='de')`
4. For each vocab item -> `anki.add_note(front, back, deck, tags)`
5. Optionally -> `tts.speak(example)` to produce audio for each card

## Build lesson from pasted text
Same as above, replace step 1 with input text.
