# Layout specification

This is the brief the generators were written to. It is worded as instructions
to an assistant ("when I ask for a sheet...") because that is how it was used,
but it doubles as the specification of the page and as the rules for choosing
content. The scripts implement the page layout; choosing content, splitting it
across pages and checking the result are up to whoever writes the JSON file.

Where it says `claude/handwriting_sheet.py` and
`claude/handwriting_sheet_arabic.py`, read `handwriting_sheet.py` and
`handwriting_sheet_arabic.py` in this repository.

The scripts differ from the brief in a few places:

- The `scale` option (for example lines 75% as tall) is an addition that is
  not in this brief; it is described in the README.
- Content that doesn't fit flows onto further pages, two sections per page,
  so a sheet is not limited to a single page.
- For Arabic, "one section filling the whole page (up to 14 rows)" is done as
  two half-page sections of up to 7 rows each, as on the Latin sheets.
- The scripts take their content from a JSON file passed on the command line;
  editing the built-in `SPEC` still works but isn't necessary.

---

# Handwriting practice sheet generator

When I ask for a handwriting practice sheet, produce a single-page, US Letter
(8.5 x 11 in, portrait) PDF in the style below. I'll tell you the content
(letters, words, names, or short phrases); everything else follows this spec
unless I say otherwise.

## Content I'll provide
- The letters, words, or phrases to practice. If I give only a topic (e.g.
  "consonants b through h", "days of the week"), choose the items yourself.
- Optionally: print only, cursive only, or both. Default is both: print on the
  upper half, cursive on the lower half, same content in each.
- If the content doesn't fit on one page at the standard line size, split it
  across more pages rather than shrinking the lines. Tell me how you split it.

## Page layout
- Margins: 40 pt left and right.
- Top of page: "Name: ______" on the left, "Date: ______" on the right,
  10 pt Helvetica.
- Each half starts with a bold 13 pt heading ("Print ..." / "Cursive ...",
  naming the content) and, right-aligned on the same line, the small gray
  instruction: "Look at the dark letters, trace the gray ones, then write
  your own."
- A faint dotted rule separates the two halves.
- 7 practice rows per half, 47 pt apart.

## Each practice row
- Three guide lines spanning the full width between margins:
  - top line: solid light blue, at capital-letter height
  - midline: dashed light blue, at lowercase x-height
  - baseline: solid light red
- Height from baseline to top line: 24 pt. Scale the font so its capital
  letters exactly reach the top line, and place the midline at that font's
  real lowercase height (measure the glyphs; don't trust font metadata).
- Left to right: a dark model, then gray copies to trace, then blank ruled
  space. Keep at least the right-hand third of every row blank for freehand
  writing.
- Colors: model in dark navy-gray (about RGB 0.13, 0.15, 0.20); tracing copies
  in medium gray (about 0.66, 0.68, 0.73), dark enough to survive a home
  printer.

## Row content pattern
- Single-letter rows: uppercase and lowercase side by side ("B b") as the dark
  model, followed by three gray copies of the pair.
- Word or letter-group rows: dark model, then one or two gray copies, repeated
  for two to four items per row as width allows.
- Order rows from simple to combined: individual letters first, then letter
  groups or words that use them. If I give only letters, use any leftover rows
  for short combinations or simple words built from those letters.

## Fonts
- Print: Edu SA Beginner, weight 500 (a hand-printed school style, not a
  geometric typeface).
- Cursive: Playwrite US Trad, weight 400 (traditional American cursive).
- Both are available as npm packages (@fontsource/edu-sa-beginner and
  @fontsource/playwrite-us-trad); convert the .woff files to .ttf.
- If I name a different handwriting method (D'Nealian, Zaner-Bloser, etc.),
  pick the closest available font and tell me what you used.

## Build requirements
- Cursive letters within a word must actually join. That needs text shaping:
  shape each string with HarfBuzz (uharfbuzz) and draw the resulting glyph
  outlines into the PDF. Do not place cursive text with a plain PDF text call,
  which leaves the letters unconnected.
- Before sending, render the page to an image and check it: letters sit on the
  baseline and reach the correct guide lines, nothing overlaps or runs past
  the margin, cursive joins are connected, and the page count is what you
  intended.

## Delivery
- Send the PDF with a short note saying what's on it. Flag any letterforms
  that differ between cursive methods (for example the looped capital I and O)
  so I can ask for a different style.

## Generators:
- Use claude/handwriting_sheet.py for Latin-script sheets and
  claude/handwriting_sheet_arabic.py for Arabic. Read the script, change only
  the SPEC content, and run it rather than writing a new script.

## Arabic sheets
When the content is Arabic, everything above applies except as noted here.

- Direction: rows run right to left. Dark model at the right margin, gray
  copies to its left, and the left-hand third of each row blank.
- Sections: there is no print/cursive split. Use one section filling the whole
  page (up to 14 rows) unless I ask for two. If I ask for two, split the page
  in halves as on the English sheets (for example letters on top, words below).
- Heading: bold 13 pt in English, naming the content. Instruction text:
  "Start at the right: look at the dark letters, trace the gray ones, then
  write your own."
- Font: Scheherazade New, weight 400 (@fontsource/scheherazade-new). If I ask
  for a mushaf style, use Amiri Quran and tell me how many rows fit, since its
  stacked letters and high vowel marks need taller rows.
- Guide lines: top line at alif height (24 pt above the baseline); dashed
  midline at the measured height of the head of waw; baseline red.
- Row patterns:
  - Single letter: isolated form as the dark model, then three gray copies.
  - Joined forms: the letter three times in a row (ببب) so the initial, medial
    and final shapes appear together; skip this for letters that don't join
    to the left (ا د ذ ر ز و).
  - Words: two or three per row, each followed by one or two gray copies.
- Vowel marks: words are fully vocalized unless I say otherwise; single
  letters and joined runs are unmarked.
- If I give only letters, choose simple words that use only those letters,
  preferring words found in the Qur'an.
- Extra check before sending: vowel marks and descenders from neighbouring
  rows must not touch. Reorder words to fix it rather than shrinking anything.
- In the delivery note, list the words with English meanings and mention any
  letterforms that vary by region or style.
