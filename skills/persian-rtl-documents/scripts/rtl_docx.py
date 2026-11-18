#!/usr/bin/env python3
"""Build right-to-left Persian Word (.docx) files with python-docx.

A normal python-docx document is left-to-right: Persian text sticks to the left edge, lists and tables
are mirrored wrongly, punctuation jumps around. This helper sets everything Word needs for RTL:
paragraph direction (w:bidi), run direction (w:rtl), the complex-script font and size (w:cs / w:szCs),
mirrored tables (w:bidiVisual), the section direction and the proofing language (fa-IR).

Command line (Markdown -> .docx):
  python rtl_docx.py report.md report.docx
  python rtl_docx.py report.md report.docx --font Vazirmatn --size 12 --page-numbers
  python rtl_docx.py --demo demo.docx

Supported Markdown: # ## ### headings, paragraphs, - bullet lists, 1. numbered lists (typed numbers are
kept), | pipe | tables |, **bold**, and <!-- pagebreak -->.

As a library:
  from rtl_docx import new_document, add_heading, add_paragraph, add_bullets, add_table, save
Requires: pip install python-docx
"""
from __future__ import annotations

import argparse
import re
import sys

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, RGBColor

DEFAULT_FONT = "Tahoma"  # ships with Windows Office and has full Persian support; Vazirmatn is nicer if installed
LANG = "fa-IR"

PPR_AFTER_BIDI = ["w:adjustRightInd", "w:snapToGrid", "w:spacing", "w:ind", "w:contextualSpacing",
                  "w:mirrorIndents", "w:suppressOverlap", "w:jc", "w:textDirection", "w:textAlignment",
                  "w:textboxTightWrap", "w:outlineLvl", "w:divId", "w:cnfStyle", "w:rPr", "w:sectPr",
                  "w:pPrChange"]
RPR_ORDER = ["w:rStyle", "w:rFonts", "w:b", "w:bCs", "w:i", "w:iCs", "w:caps", "w:smallCaps", "w:strike",
             "w:dstrike", "w:outline", "w:shadow", "w:emboss", "w:imprint", "w:noProof", "w:snapToGrid",
             "w:vanish", "w:webHidden", "w:color", "w:spacing", "w:w", "w:kern", "w:position", "w:sz",
             "w:szCs", "w:highlight", "w:u", "w:effect", "w:bdr", "w:shd", "w:fitText", "w:vertAlign",
             "w:rtl", "w:cs", "w:em", "w:lang", "w:eastAsianLayout", "w:specVanish", "w:oMath"]
TBLPR_AFTER_BIDI_VISUAL = ["w:tblStyleRowBandSize", "w:tblStyleColBandSize", "w:tblW", "w:jc",
                           "w:tblCellSpacing", "w:tblInd", "w:tblBorders", "w:shd", "w:tblLayout",
                           "w:tblCellMar", "w:tblLook", "w:tblCaption", "w:tblDescription"]
TCPR_AFTER_SHD = ["w:noWrap", "w:tcMar", "w:textDirection", "w:tcFitText", "w:vAlign", "w:hideMark"]
SECTPR_AFTER_BIDI = ["w:rtlGutter", "w:docGrid", "w:printerSettings", "w:sectPrChange"]


# ── low-level XML helpers (Word is strict about the order of child elements) ──────────────────
def _get_or_add(parent, tag: str, successors: list):
    found = parent.find(qn(tag))
    if found is not None:
        return found
    el = OxmlElement(tag)
    for name in successors:
        nxt = parent.find(qn(name))
        if nxt is not None:
            nxt.addprevious(el)
            return el
    parent.append(el)
    return el


def _after(tag: str) -> list:
    return RPR_ORDER[RPR_ORDER.index(tag) + 1:]


def _style_run_props(rpr, font: str, size: float | None = None, bold: bool = False) -> None:
    fonts = _get_or_add(rpr, "w:rFonts", _after("w:rFonts"))
    for attr in list(fonts.attrib):  # theme fonts (headings) would override the explicit name
        if attr.endswith("Theme"):
            del fonts.attrib[attr]
    for attr in ("w:ascii", "w:hAnsi", "w:cs", "w:eastAsia"):
        fonts.set(qn(attr), font)
    if size:
        half = str(int(round(size * 2)))
        _get_or_add(rpr, "w:sz", _after("w:sz")).set(qn("w:val"), half)
        _get_or_add(rpr, "w:szCs", _after("w:szCs")).set(qn("w:val"), half)
    if bold:
        _get_or_add(rpr, "w:b", _after("w:b"))
        _get_or_add(rpr, "w:bCs", _after("w:bCs"))
    _get_or_add(rpr, "w:rtl", _after("w:rtl"))
    _get_or_add(rpr, "w:lang", _after("w:lang")).set(qn("w:bidi"), LANG)


def _rtl_paragraph_props(paragraph, align: str = "start") -> None:
    _get_or_add(paragraph._p.get_or_add_pPr(), "w:bidi", PPR_AFTER_BIDI)
    # In a bidi paragraph the default alignment ("start") is already the right edge.
    if align == "center":
        paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    elif align == "justify":
        paragraph.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    elif align != "start":
        raise ValueError("align must be 'start', 'center' or 'justify'")


def _style_rtl(style, font: str, size: float | None = None, bold: bool = False) -> None:
    el = style.element
    _get_or_add(el.get_or_add_pPr(), "w:bidi", PPR_AFTER_BIDI)
    _style_run_props(el.get_or_add_rPr(), font, size, bold)


# ── public API ───────────────────────────────────────────────────────────────────────────
def new_document(font: str = DEFAULT_FONT, size: float = 12, margin_cm: float = 2.5):
    """A blank A4 document set up for Persian: RTL section, Persian styles and fonts."""
    doc = Document()
    section = doc.sections[0]
    section.page_width, section.page_height = Cm(21.0), Cm(29.7)
    for side in ("left_margin", "right_margin", "top_margin", "bottom_margin"):
        setattr(section, side, Cm(margin_cm))
    _get_or_add(section._sectPr, "w:bidi", SECTPR_AFTER_BIDI)

    _style_rtl(doc.styles["Normal"], font, size)
    heading_sizes = {"Title": 22, "Heading 1": 18, "Heading 2": 15, "Heading 3": 13}
    for name, pt in heading_sizes.items():
        st = doc.styles[name]
        _style_rtl(st, font, pt, bold=True)
        st.font.color.rgb = RGBColor(0x1F, 0x29, 0x37)
    for name in ("List Bullet", "List Number"):
        _style_rtl(doc.styles[name], font, size)
    doc._rtl_font, doc._rtl_size = font, size  # remembered for runs created later
    return doc


def _add_runs(paragraph, text: str, doc, bold: bool = False, size: float | None = None) -> None:
    """Add text to a paragraph; **double stars** make bold runs. Backticks are dropped."""
    text = text.replace("`", "")
    for part in re.split(r"(\*\*[^*]+\*\*)", text):
        if not part:
            continue
        is_bold = bold
        if len(part) > 4 and part.startswith("**") and part.endswith("**"):
            part, is_bold = part[2:-2], True
        run = paragraph.add_run(part)
        _style_run_props(run._r.get_or_add_rPr(), doc._rtl_font, size or doc._rtl_size, is_bold)


def add_heading(doc, text: str, level: int = 1):
    p = doc.add_heading(level=min(max(level, 1), 3))
    _rtl_paragraph_props(p)
    _add_runs(p, text, doc, bold=True, size={1: 18, 2: 15, 3: 13}[min(max(level, 1), 3)])
    return p


def add_paragraph(doc, text: str = "", bold: bool = False, align: str = "start", size: float | None = None):
    p = doc.add_paragraph()
    _rtl_paragraph_props(p, align)
    _add_runs(p, text, doc, bold, size)
    return p


def add_bullets(doc, items: list):
    out = []
    for item in items:
        p = doc.add_paragraph(style="List Bullet")
        _rtl_paragraph_props(p)
        _add_runs(p, item, doc)
        out.append(p)
    return out


def add_page_break(doc) -> None:
    doc.add_paragraph().add_run().add_break(WD_BREAK.PAGE)


def add_table(doc, rows: list, header: bool = True, style: str = "Table Grid"):
    """rows: list of lists of strings. Columns run right-to-left, like Persian text."""
    ncols = max(len(r) for r in rows)
    table = doc.add_table(rows=len(rows), cols=ncols)
    table.style = style
    _get_or_add(table._tbl.tblPr, "w:bidiVisual", TBLPR_AFTER_BIDI_VISUAL)
    for r, row in enumerate(rows):
        for c in range(ncols):
            cell = table.cell(r, c)
            para = cell.paragraphs[0]
            _rtl_paragraph_props(para)
            _add_runs(para, row[c] if c < len(row) else "", doc, bold=header and r == 0)
            if header and r == 0:
                shd = _get_or_add(cell._tc.get_or_add_tcPr(), "w:shd", TCPR_AFTER_SHD)
                shd.set(qn("w:val"), "clear")
                shd.set(qn("w:color"), "auto")
                shd.set(qn("w:fill"), "E5E7EB")
    doc.add_paragraph()  # breathing room after the table
    return table


def add_page_numbers(doc) -> None:
    """Centered page number in the footer."""
    para = doc.sections[0].footer.paragraphs[0]
    _rtl_paragraph_props(para, "center")
    for kind, text in (("begin", None), (None, " PAGE "), ("end", None)):
        run = para.add_run()
        if kind:
            fld = OxmlElement("w:fldChar")
            fld.set(qn("w:fldCharType"), kind)
            run._r.append(fld)
        else:
            instr = OxmlElement("w:instrText")
            instr.set(qn("xml:space"), "preserve")
            instr.text = text
            run._r.append(instr)


def save(doc, path: str) -> None:
    doc.save(path)


# ── Markdown ─────────────────────────────────────────────────────────────────────────────
_SPECIAL = re.compile(r"^(\s*#{1,3}\s|\s*[-*•]\s|\s*\d+[.)]\s|\s*\||\s*<!--)")


def build_from_markdown(markdown: str, doc=None, **kwargs):
    doc = doc or new_document(**kwargs)
    lines = markdown.replace("\r\n", "\n").split("\n")
    i = 0
    while i < len(lines):
        line = lines[i]
        if not line.strip() or re.fullmatch(r"\s*(-{3,}|\*{3,})\s*", line):
            i += 1
        elif m := re.match(r"^\s*(#{1,3})\s+(.*)$", line):
            add_heading(doc, m.group(2).strip(), len(m.group(1)))
            i += 1
        elif re.match(r"^\s*<!--\s*pagebreak\s*-->\s*$", line):
            add_page_break(doc)
            i += 1
        elif line.lstrip().startswith("|"):
            rows = []
            while i < len(lines) and lines[i].lstrip().startswith("|"):
                cells = [c.strip() for c in lines[i].strip().strip("|").split("|")]
                if not all(re.fullmatch(r":?-{2,}:?", c) for c in cells if c):
                    rows.append(cells)
                i += 1
            if rows:
                add_table(doc, rows)
        elif re.match(r"^\s*[-*•]\s+", line):
            items = []
            while i < len(lines) and re.match(r"^\s*[-*•]\s+", lines[i]):
                items.append(re.sub(r"^\s*[-*•]\s+", "", lines[i]).strip())
                i += 1
            add_bullets(doc, items)
        elif re.match(r"^\s*\d+[.)]\s+", line):
            while i < len(lines) and re.match(r"^\s*\d+[.)]\s+", lines[i]):
                add_paragraph(doc, lines[i].strip())
                i += 1
        else:
            chunk = []
            while i < len(lines) and lines[i].strip() and not _SPECIAL.match(lines[i]):
                chunk.append(lines[i].strip())
                i += 1
            if not chunk:  # a line that merely looked special; avoid an endless loop
                chunk, i = [lines[i].strip()], i + 1
            add_paragraph(doc, " ".join(chunk))
    return doc


DEMO = """# گزارش نمونه

این یک **سند فارسی** است که راست‌چین ساخته شده؛ اعداد مثل ۱۲۳ و کلمات انگلیسی مثل Excel و Word درست کنار متن می‌نشینند.

## فهرست کارها

- کار اول: نصب نرم‌افزار (Python 3.12)
- کار دوم: نوشتن گزارش
- کار سوم: بررسی نهایی

## جدول نمره‌ها

| نام | درس | نمره |
| --- | --- | --- |
| علی | Word | ۱۸ |
| مریم | Excel | ۱۹٫۵ |

## مراحل

1. فایل را باز کن.
2. تغییرات را ذخیره کن.
"""


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description="Markdown -> right-to-left Persian .docx")
    p.add_argument("input", nargs="?", help="Markdown file")
    p.add_argument("output", nargs="?", help=".docx file to write")
    p.add_argument("--font", default=DEFAULT_FONT)
    p.add_argument("--size", type=float, default=12)
    p.add_argument("--page-numbers", action="store_true")
    p.add_argument("--demo", metavar="OUT.docx", help="write a small sample document")
    args = p.parse_args(argv)

    if args.demo:
        source, target = DEMO, args.demo
    elif args.input and args.output:
        with open(args.input, encoding="utf-8") as f:
            source, target = f.read(), args.output
    else:
        p.error("give INPUT.md OUTPUT.docx, or --demo OUT.docx")
    doc = build_from_markdown(source, font=args.font, size=args.size)
    if args.page_numbers or args.demo:
        add_page_numbers(doc)
    save(doc, target)
    print(f"wrote {target}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
