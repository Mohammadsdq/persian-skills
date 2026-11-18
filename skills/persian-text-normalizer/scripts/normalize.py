#!/usr/bin/env python3
"""Normalize Persian text (stdlib only).

What it fixes
  * Arabic letters typed instead of Persian ones:  ي ى -> ی,  ك -> ک
  * Arabic-Indic digits -> Persian digits (and optionally all digits -> Persian / Latin)
  * Arabic punctuation marks next to Persian text:  , ; ? -> ، ؛ ؟
  * tatweel (kashida), repeated spaces, stray spaces around punctuation and brackets
  * half-spaces (ZWNJ): می‌کنم  کتاب‌ها  (only the safe, unambiguous cases)

What it never touches: fenced code, `inline code`, URLs and e-mail addresses.

Usage
  python normalize.py file.txt                # print the result
  python normalize.py file.txt --in-place
  echo "كتاب ها ي من" | python normalize.py -
  python normalize.py text.md --digits fa     # all digits -> Persian
"""
from __future__ import annotations

import argparse
import re
import sys

ZWNJ = "‌"
FA = "؀-ۿ"  # Arabic block (covers Persian letters)
PERSIAN_LETTER = "ء-غف-يپچژکگیۀ"

LETTER_MAP = {
    "ي": "ی",  # ي -> ی
    "ى": "ی",  # ى -> ی
    "ك": "ک",  # ك -> ک
}
AR_DIGITS = "٠١٢٣٤٥٦٧٨٩"
FA_DIGITS = "۰۱۲۳۴۵۶۷۸۹"
LATIN_DIGITS = "0123456789"
DIACRITICS = re.compile("[ً-ْٰ]")

# Parts that must be left alone. Restored after processing.
PROTECT = re.compile(
    r"```.*?```"  # fenced code
    r"|`[^`\n]+`"  # inline code
    r"|https?://[^\s)>\]]+"  # URLs
    r"|www\.[^\s)>\]]+"
    r"|[\w.+-]+@[\w-]+(?:\.[\w-]+)+",  # e-mail
    re.S,
)
OPEN, CLOSE = "", ""


def _protect(text: str):
    saved: list = []

    def keep(m: re.Match) -> str:
        saved.append(m.group(0))
        return f"{OPEN}{len(saved) - 1}{CLOSE}"

    return PROTECT.sub(keep, text), saved


def _restore(text: str, saved: list) -> str:
    return re.sub(f"{OPEN}(\\d+){CLOSE}", lambda m: saved[int(m.group(1))], text)


def fix_letters(text: str) -> str:
    return text.translate(str.maketrans(LETTER_MAP))


def fix_digits(text: str, mode: str = "fix") -> str:
    """mode: 'fix' (Arabic-Indic -> Persian only), 'fa' (all -> Persian), 'en' (all -> Latin), 'keep'."""
    if mode == "keep":
        return text
    if mode == "en":
        return text.translate(str.maketrans(AR_DIGITS + FA_DIGITS, LATIN_DIGITS * 2))
    table = AR_DIGITS + (LATIN_DIGITS if mode == "fa" else "")
    return text.translate(str.maketrans(table, FA_DIGITS * (2 if mode == "fa" else 1)))


def fix_punctuation(text: str) -> str:
    # Only after a Persian letter, so "1,000" or "a, b" in English text stay untouched.
    # (a stray space before the mark is dropped too: "سلام ,من" -> "سلام،من", spaced later)
    # a comma between two digits (۳,۵ / 1,000) is a number separator, not punctuation
    text = re.sub(rf"(?:(?<=[{PERSIAN_LETTER}])[ \t]*|(?<=[۰-۹])),(?![0-9۰-۹])", "،", text)
    text = re.sub(rf"(?<=[{PERSIAN_LETTER}۰-۹])[ \t]*;", "؛", text)
    text = re.sub(rf"(?<=[{PERSIAN_LETTER}۰-۹])[ \t]*\?", "؟", text)
    text = re.sub(rf"([،؛؟])(?=[{PERSIAN_LETTER}])", r"\1 ", text)
    return text


def fix_spacing(text: str) -> str:
    text = text.replace("ـ", "")  # tatweel
    text = re.sub(r"[ \t ]{2,}", " ", text)
    text = re.sub(r"[ \t]+(?=[،؛؟)\]»])", "", text)  # no space before closing marks
    # a space before . : ! is only wrong at the end of a sentence (keeps " .git", " .py" intact)
    text = re.sub(r"[ \t]+(?=[.:!](?=[ \t\n]|$))", "", text)
    text = re.sub(r"(?<=[(\[«])[ \t]+", "", text)  # no space after opening marks
    text = re.sub(r"[ \t]+$", "", text, flags=re.M)
    return text


def fix_zwnj(text: str) -> str:
    # می / نمی + verb:  "می کنم" -> "می‌کنم"
    text = re.sub(
        rf"(?<![{FA}{ZWNJ}])(ن?می)[ \t]+(?=[{PERSIAN_LETTER}])", rf"\1{ZWNJ}", text
    )
    # plural / possessive: "کتاب ها" -> "کتاب‌ها", "کتاب های من" -> "کتاب‌های من"
    text = re.sub(
        rf"(?<=[{PERSIAN_LETTER}])[ \t]+(ها(?:ی|یی|یم|یت|یش|مان|تان|شان)?)(?![{FA}])",
        rf"{ZWNJ}\1",
        text,
    )
    # detached ezafe ye: "خانه ی من" -> "خانه‌ی من", "کتاب‌ها ی من" -> "کتاب‌ها‌ی من"
    # (only after ه / ها, so a letter name like "حرف ی" is left alone)
    text = re.sub(rf"(?:(?<=ه)|(?<=ها))[ \t]+ی(?![{FA}])", f"{ZWNJ}ی", text)
    # clean up stray half-spaces
    text = re.sub(f"{ZWNJ}{{2,}}", ZWNJ, text)
    text = re.sub(rf"{ZWNJ}+(?=[ \t\n]|$)", "", text)
    text = re.sub(rf"(?<=[ \t\n]){ZWNJ}+", "", text)
    text = re.sub(rf"^{ZWNJ}+", "", text)
    return text


def normalize(text: str, digits: str = "fix", strip_diacritics: bool = False) -> str:
    text, saved = _protect(text)
    text = fix_letters(text)
    text = fix_digits(text, digits)
    if strip_diacritics:
        text = DIACRITICS.sub("", text)
    text = fix_spacing(text)
    text = fix_punctuation(text)
    text = fix_zwnj(text)
    return _restore(text, saved)


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description="Normalize Persian text.")
    p.add_argument("path", help="text file, or - for stdin")
    p.add_argument("--digits", choices=["fix", "fa", "en", "keep"], default="fix",
                   help="fix: Arabic-Indic -> Persian (default); fa: all -> Persian; en: all -> Latin; keep")
    p.add_argument("--strip-diacritics", action="store_true", help="remove harakat (fatha, kasra, ...)")
    p.add_argument("--in-place", action="store_true", help="rewrite the file instead of printing")
    args = p.parse_args(argv)

    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")  # Windows consoles
    if args.path == "-":
        source = sys.stdin.read()
    else:
        with open(args.path, encoding="utf-8") as f:
            source = f.read()

    result = normalize(source, args.digits, args.strip_diacritics)

    if args.in_place and args.path != "-":
        with open(args.path, "w", encoding="utf-8", newline="") as f:
            f.write(result)
        print(f"normalized {args.path}", file=sys.stderr)
    else:
        sys.stdout.write(result)
    return 0


if __name__ == "__main__":
    sys.exit(main())
