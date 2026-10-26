# IEEE conference paper (HYDRO RAIN GUARD)

A two-column IEEE conference paper on the same implementation as the Stage-II
report, written as a standalone submission.

## Files

| File | What it is |
|---|---|
| `HydroRainGuard_IEEE_Conference_Paper.docx` | Editable Word file, IEEE two-column layout |
| `HydroRainGuard_IEEE_Conference_Paper.pdf` | Print-ready A4 PDF, 7 pages (submission / PDF eXpress) |
| `HydroRainGuard_IEEE_Paper.txt` | Plain text of the whole paper, for pasting anywhere |
| `figures/` | 7 colour figures at 400 dpi, sized for a single 3.5 in column |
| `preview/` | Page images of the PDF, one PNG per page |

## Template compliance

- A4, margins 19 mm top, 43 mm bottom, 14.32 mm left/right (IEEE conference).
- Title 24 pt, author block full width, body **two columns, 3.49 in each**.
- Body 10 pt Times New Roman, justified, first-line indent 0.2 in, single
  spacing; section heads small caps centred; subsection heads italic.
- Figures single-column with 8 pt "Fig. n." captions below; tables with
  8 pt small-caps caption above, rules above/below only (no vertical rules).
- Equations centred with flush-right numbers, italic variables, subscripts.
- References 8 pt, IEEE style, numbered in order of first citation.
- No page numbers, no headers, no footers, matching the template.

## Figures

Colour, because the request was for colour rather than the institute's
black-and-white rule (the Stage-II report stays greyscale; this paper does not).

1. `fig2_arch.png` - four-layer system architecture (drawn)
2. `fig3_wizard.png` - roof step of the wizard with the rainfall provenance card
3. `fig4_results.png` - results dashboard for the reference case
4. `fig7_xr_panel.png` - 3D/AR preview panel with ranked structures and dimensions
5. `fig5_monthly.png` - monthly rainfall vs the two runoff models (drawn)
6. `fig9_scenarios.png` - normalised yield and payback across five sites (drawn)
7. `fig8_cost.png` - cost-benefit tab with the negative-payback warning

## Rebuilding

From the repository root:

```bash
.venv/bin/python report/paper/make_figures.py     # figures/  (needs matplotlib, pillow)
.venv/bin/python report/paper/build_paper.py      # .docx
.venv/bin/python report/paper/build_paper_pdf.py  # .pdf + preview/
```

`build_paper_pdf.py` rebuilds at several figure scales and keeps the version
with the fewest pages and the least white space at the foot of a column.

## Content notes

- All numbers come from `report/data/scenarios.json`, i.e. from the running
  API, not from an earlier draft.
- The negative result (payback 60.6 years at INR 35/kL) is reported as a
  finding, together with the break-even tariff, rather than hidden.
- References [1]-[11] are the technical works actually used; [12]-[20] are the
  software and dataset documentation. Every reference is cited in the text.

## Before submitting

- Fill in the roll numbers in the author block (`roll no. ______`).
- Add the guide's e-mail / ORCID if the conference requires it.
- IEEE PDF eXpress will check the PDF; embed the Times font (already base-14)
  and keep the file under the size limit.
