# Handwriting practice sheet generators

Developed using Claude AI and Claude Code directed by Randall Desmond, rdesmond@rmd3.com

Two small Python scripts that turn a JSON description of what to practice into
a printable US Letter PDF worksheet: ruled rows with a dark model to look at,
gray copies to trace, and blank ruled space to write in.

- `handwriting_sheet.py` makes Latin-script sheets (print and cursive).
- `handwriting_sheet_arabic.py` makes Arabic sheets (right to left).

You choose the content. The layout (page size, margins, guide lines, colors,
fonts) is fixed in the scripts; the full layout specification is in
[LAYOUT_SPEC.md](LAYOUT_SPEC.md).

## Contents

| File | What it is |
|---|---|
| `handwriting_sheet.py` | Latin generator: print (Edu SA Beginner) and cursive (Playwrite US Trad). |
| `handwriting_sheet_arabic.py` | Arabic generator: Naskh (Scheherazade New), rows run right to left. |
| `preview.py` | Optional helper: renders a PDF to PNG images so you can check it before printing. |
| `requirements.txt` | Python packages. |
| `package.json` | The three font packages, fetched with npm. No font files are committed. |
| `.gitignore` | Ignores `node_modules/`, `.venv/`, generated PDFs and preview images. |
| `LAYOUT_SPEC.md` | The layout specification the scripts implement, and the rules for choosing content. |
| `LICENSE` | MIT licence for the code. |
| `examples/` | Sample input files, with the PDFs they make in `examples/rendered/` (see [Examples](#examples)). |

## Requirements

- Python 3 (developed on 3.13, tested on 3.14).
- Node.js with npm. npm is used only to download the fonts; nothing runs in Node.

## Setup

Run these once, from the repository folder:

```sh
npm install                       # fonts -> node_modules/@fontsource/
pip install -r requirements.txt   # reportlab, fonttools, uharfbuzz, pymupdf
```

A virtual environment (`python3 -m venv .venv`, then `.venv/bin/pip install
-r requirements.txt`) keeps these packages out of your system Python.

`pymupdf` is needed only by `preview.py`. Leave it out if you don't want the
preview helper.

### Where the scripts look for fonts

Each script searches for a `node_modules/@fontsource` folder in this order:

1. the folder named by the `FONTSOURCE_DIR` environment variable, if set
2. the current working directory
3. the folder the script is in

If you run `npm install` in the repository folder, case 3 always works, so you
can run the scripts from anywhere. If no fonts are found, the script exits with
the `npm i ...` command to run.

The fonts are licensed under the SIL Open Font License 1.1 (as stated in each
`@fontsource` package).

## Making a sheet

```sh
python3 handwriting_sheet.py spec.json out.pdf
python3 handwriting_sheet_arabic.py spec.json out.pdf
```

- The first argument is the input JSON file. Without it, the script builds its
  built-in sheet (the `SPEC` dictionary near the top of the script): a vowel
  sheet for Latin, a seven-letter starter sheet for Arabic.
- The second argument is the output PDF. Without it, the output is
  `handwriting-practice.pdf` (Latin) or `arabic-handwriting-practice.pdf`
  (Arabic) in the current folder.

Try it:

```sh
python3 handwriting_sheet.py               # writes handwriting-practice.pdf
python3 handwriting_sheet_arabic.py        # writes arabic-handwriting-practice.pdf
python3 preview.py handwriting-practice.pdf   # writes handwriting-practice-p1.png
```

or make one of the [examples](#examples):

```sh
python3 handwriting_sheet.py examples/latin-print-cursive.json latin.pdf
python3 handwriting_sheet_arabic.py examples/arabic.json arabic.pdf
```

Print at 100% ("actual size"), not "fit to page", or the line heights come out
slightly off.

## The input file

The input is one JSON file per sheet. Save it as UTF-8.

### Latin example

```json
{
  "title": "Cursive Practice: Desmond",
  "sections": [
    {"font": "Cursive", "heading": "Cursive: Desmond",
     "rows": [
       {"pair": "Dd"},
       {"items": ["Desmond"], "traces": 1},
       {"items": ["ea", "ou", "ie", "oi"]}
     ]},
    {"font": "Cursive", "heading": "Cursive: Desmond (75% size)", "scale": 0.75,
     "rows": [
       {"items": ["Desmond"], "traces": 2}
     ]}
  ]
}
```

### Arabic example

```json
{
  "title": "Arabic Handwriting Practice",
  "sections": [
    {"heading": "Arabic letters on their own",
     "rows": [
       {"items": ["ب"], "traces": 3},
       {"items": ["ببب", "ننن"]}
     ]},
    {"heading": "Words", "scale": 0.75,
     "rows": [
       {"items": ["بَاب", "نَار"], "traces": 2}
     ]}
  ]
}
```

### Field reference

Top level:

| Field | Required | Meaning |
|---|---|---|
| `title` | no | The PDF's document title (shown in the viewer's title bar, not printed on the page). |
| `sections` | yes | A list of sections. Each section is half a page. |

Each section:

| Field | Required | Meaning |
|---|---|---|
| `font` | Latin only, yes | `"Print"` or `"Cursive"`. The Arabic script has a single font and ignores this field. |
| `heading` | yes | Bold heading printed above the section. Keep it short (see [Things to watch](#things-to-watch)). |
| `scale` | no | Line size relative to standard. `0.75` makes the lines 75% as tall, for smaller writing. Default `1`. |
| `rows` | yes | The practice rows, top to bottom. |

Each row is one of two kinds:

| Row | Meaning |
|---|---|
| `{"items": ["word", ...], "traces": 1}` | Word or letter-group row. Each item is drawn dark, then followed by `traces` gray copies. `traces` defaults to 1. Any text works: a single letter, a letter group, a word, a name, a short phrase. |
| `{"pair": "Bb", "traces": 3}` | Letter row, Latin only. The first character is the uppercase letter and the rest is the lowercase; they are drawn side by side ("B b") as the dark model, followed by `traces` gray copies of the pair. `traces` defaults to 3. |

### Sections, rows and pages

- Two sections fit on a page: the first is the top half, the second the bottom
  half, with a faint dotted rule between them.
- More than two sections flow onto further pages, two per page. A sheet with
  one section leaves the bottom half of the page empty.
- A section holds up to 7 rows at standard size. With `scale`, the limit is
  7 divided by the scale, rounded down: 9 rows at `0.75`, 5 rows at `1.25`.
  Each section always occupies the same half-page whatever its scale.
- If a section has too many rows, the script stops and tells you to split it
  into another section.
- Two halves of one page can use different scales, as in the
  [Latin example](#latin-example): standard size on top, 75% below.

### What `scale` changes

At `"scale": 0.75` the distance from the baseline to the top line goes from
24 pt to 18 pt, and the spacing between rows from 47 pt to 35.25 pt. The
letters, and the thickness of their strokes, shrink with the lines; the dashed
midline stays at the font's real lowercase height. The fixed gaps between a
model and its gray copies do not shrink.

Because the letters are narrower, more copies fit in a row. "Desmond" fits one
gray copy per row at standard size and two at 75%.

### How wide a row can be

At least a third of every row must stay blank for freehand writing: the
right-hand third on Latin sheets, the left-hand third on Arabic sheets. If a
row's models and gray copies run past the two-thirds mark, the script prints

```
warning: row 1 of 'Cursive: Desmond' leaves less than a third of the line blank; move an item to another row.
```

and still writes the PDF. Fix it by lowering `traces` or moving an item to
another row. Do not fix it by shrinking the lines.

### Arabic input

- Type the words in Arabic, with the vowel marks (harakat) in the text if you
  want them on the sheet. The script draws exactly what is in the file.
- Rows run right to left: the first item in `items` is at the right margin.
- For joined-form practice, repeat a letter three times (`"ببب"`) so its
  initial, medial and final shapes appear together. This doesn't work for
  letters that don't join to the left (ا د ذ ر ز و).
- There are no `pair` rows and no `font` field.
- The top guide line is at the height of alif; the dashed midline is at the
  height of the head of waw.

## Checking a sheet before you print

The only thing the scripts check for you is the blank-third rule above.
Everything else needs a look at the rendered page. `preview.py` makes that
quick:

```sh
python3 preview.py out.pdf          # out-p1.png, out-p2.png, ... at 150 dpi
python3 preview.py out.pdf 300      # higher resolution for a closer look
```

Check that:

- the page count is what you intended;
- letters sit on the red baseline and reach the right guide lines (capitals
  and tall letters to the top line, small letters to the dashed midline);
- nothing overlaps or runs past the margins;
- no heading runs into the gray instruction text on the same line;
- cursive and Arabic letters within a word are actually joined;
- on Arabic sheets, vowel marks and descenders from neighbouring rows don't
  touch. If they do, reorder the words; don't shrink anything.

## Things to watch

- **Heading length.** The heading and the small gray instruction share one
  line, and the script does not check that they fit. Keep headings to roughly
  35 characters on Latin sheets and 27 on Arabic sheets (whose instruction
  text is longer). "Cursive: Desmond (more of your own)" fits;
  "Cursive: Desmond (75% size, more of your own)" collides.
- **Letterforms differ between handwriting methods.** Playwrite US Trad is
  traditional American cursive: a rounded capital A, a looped capital D, a
  capital H that doesn't join the next letter, a pointed lowercase s. Methods
  such as Zaner-Bloser and D'Nealian draw some of these differently.
  Scheherazade New is a Naskh (book) style; everyday Arabic handwriting is
  often closer to Ruq'ah, where for example the two dots of ت become a dash.
- **Joins need text shaping.** Both scripts shape each string with HarfBuzz
  and draw the glyph outlines. Don't replace that with a plain PDF text call:
  cursive letters would come out unconnected and Arabic would come out as
  separate left-to-right letters.
- **Overlapping joins are filled solid.** The outlines of joined letters
  overlap slightly. The scripts fill them with the non-zero rule
  (`fillMode=1` in the `drawPath` call) so the overlaps print solid. With
  reportlab's default fill rule they show as hairline white slivers; keep
  `fillMode=1` if you edit that line.

## Changing the layout

The layout constants are at the top of each script, under `# layout`:

| Constant | Value | Meaning |
|---|---|---|
| `MARGIN` | 40 | Left and right margin, pt. |
| `CAP` | 24 | Baseline to top guide line at standard size, pt. |
| `ROW_PITCH` | 47 | Distance between rows at standard size, pt. |
| `ROWS_PER_SECTION` | 7 | Rows per half page at standard size. |
| `BLANK_FRACTION` | 1/3 | Share of each row kept blank. |
| `INK`, `TRACE` | | Colors of the dark model and the gray copies. |
| `BLUE`, `RED` | | Colors of the guide lines. |
| `NOTE` | | The instruction text printed beside each heading. |
| `FONT_FILES` / `FONT_FILE` | | Which font files to load from `node_modules/@fontsource`. |

To use a different font, add its `@fontsource` package to `package.json` and
point `FONT_FILES` (Latin) or `FONT_FILE` (Arabic) at its `.woff` file. The
scripts measure the real glyph heights to size the text, so no other change is
needed. For a mushaf-style Arabic font such as Amiri Quran, expect to need
taller rows: its stacked letters and high vowel marks don't fit the standard
row pitch.

## Examples

Each input file in `examples/` has its finished PDF in `examples/rendered/`,
so you can see the result without installing anything.

| Input | Script | Sheet |
|---|---|---|
| `examples/latin-print-cursive.json` | Latin | Letters a to e: print on top, cursive below, each with five letter rows and two word rows. Standard size. |
| `examples/latin-print-cursive-75.json` | Latin | Letters f to l, laid out the same way, at 75% size, which fits 9 rows per half: seven letters and two word rows. |
| `examples/arabic.json` | Arabic | Seven letters (س ف ق ك ع ه ي) on top; joined forms and vocalized words below. Standard size. |
| `examples/arabic-75.json` | Arabic | Seven letters (ج ح خ د ر ط ص) and joined forms on top; nine rows of vocalized words below. 75% size. |

The Arabic words, with their meanings:

- `arabic.json`: سَمَك fish, قَلَم pen, عَسَل honey, قَمَر moon, فِيل elephant,
  كَلْب dog, بَيْت house, سَيْف sword.
- `arabic-75.json`: جَمَل camel, حَجَر stone, خُبْز bread, دَار home, طِفْل child,
  صَبْر patience, رِجْل leg, ذَهَب gold, زَيْت oil, وَرْد roses, مَاء water,
  نُور light, شَجَرَة tree, بَحْر sea, صَدِيق friend, طَرِيق road, خَيْر good,
  حُبّ love.

To rebuild the rendered PDFs after changing a script:

```sh
for n in latin-print-cursive latin-print-cursive-75; do
  python3 handwriting_sheet.py examples/$n.json examples/rendered/$n.pdf; done
for n in arabic arabic-75; do
  python3 handwriting_sheet_arabic.py examples/$n.json examples/rendered/$n.pdf; done
```

## License

The code is released under the [MIT License](LICENSE). The fonts are not part
of this repository: npm downloads them, and each is licensed under the SIL Open
Font License 1.1 by its authors.
