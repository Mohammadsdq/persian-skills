#!/usr/bin/env python3
"""Numbers -> Persian words (stdlib only).

Usage
  python num2words_fa.py 1234567                 # یک میلیون و دویست و سی و چهار هزار و پانصد و شصت و هفت
  python num2words_fa.py 2500000 --unit تومان    # ... تومان
  python num2words_fa.py 3.14                    # سه ممیز چهارده صدم
  python num2words_fa.py 21 --ordinal            # بیست و یکم
Accepts Persian/Arabic digits and thousands separators (, ٬ ،).
"""
from __future__ import annotations

import argparse
import sys

ONES = ["", "یک", "دو", "سه", "چهار", "پنج", "شش", "هفت", "هشت", "نه"]
TEENS = ["ده", "یازده", "دوازده", "سیزده", "چهارده", "پانزده", "شانزده", "هفده", "هجده", "نوزده"]
TENS = ["", "", "بیست", "سی", "چهل", "پنجاه", "شصت", "هفتاد", "هشتاد", "نود"]
HUNDREDS = ["", "صد", "دویست", "سیصد", "چهارصد", "پانصد", "ششصد", "هفتصد", "هشتصد", "نهصد"]
SCALES = ["", "هزار", "میلیون", "میلیارد", "تریلیون", "کوادریلیون"]
DENOMINATORS = {1: "دهم", 2: "صدم", 3: "هزارم", 4: "ده‌هزارم", 5: "صدهزارم", 6: "میلیونیم"}
MAX_VALUE = 10 ** (3 * len(SCALES)) - 1


def _below_1000(n: int) -> str:
    parts = []
    if n >= 100:
        parts.append(HUNDREDS[n // 100])
        n %= 100
    if n >= 20:
        parts.append(TENS[n // 10])
        n %= 10
        if n:
            parts.append(ONES[n])
    elif n >= 10:
        parts.append(TEENS[n - 10])
    elif n:
        parts.append(ONES[n])
    return " و ".join(parts)


def cardinal(n: int) -> str:
    """Whole number to words. 1000 is 'هزار' (not 'یک هزار'); 1000000 is 'یک میلیون'."""
    if n < 0:
        return "منفی " + cardinal(-n)
    if n == 0:
        return "صفر"
    if n > MAX_VALUE:
        raise ValueError("number too large")
    groups = []
    i = 0
    while n:
        groups.append(n % 1000)
        n //= 1000
        i += 1
    parts = []
    for idx in range(len(groups) - 1, -1, -1):
        g = groups[idx]
        if not g:
            continue
        if idx == 0:
            parts.append(_below_1000(g))
        elif idx == 1 and g == 1:
            parts.append("هزار")
        else:
            parts.append(f"{_below_1000(g)} {SCALES[idx]}")
    return " و ".join(parts)


def ordinal(n: int) -> str:
    if n < 0:
        raise ValueError("ordinals need a non-negative number")
    if n == 1:
        return "اول"
    words = cardinal(n)
    if words.endswith("سه"):
        return words[:-2] + "سوم"
    if words.endswith("ی"):  # سی -> سی‌ام
        return words + "‌ام"
    return words + "م"


def decimal(text: str) -> str:
    sign = ""
    if text.startswith("-"):
        sign, text = "منفی ", text[1:]
    whole, _, frac = text.partition(".")
    frac = frac.rstrip("0")
    out = cardinal(int(whole or "0"))
    if frac:
        if len(frac) > max(DENOMINATORS):
            raise ValueError(f"at most {max(DENOMINATORS)} decimal places are supported")
        out += f" ممیز {cardinal(int(frac))} {DENOMINATORS[len(frac)]}"
    return sign + out


def clean_number(text: str) -> str:
    text = text.translate(str.maketrans("۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩", "01234567890123456789"))
    for sep in (",", "٬", "،", " "):
        text = text.replace(sep, "")
    return text.replace("٫", ".")


def to_words(text: str, unit: str = "", as_ordinal: bool = False) -> str:
    text = clean_number(text)
    if as_ordinal:
        out = ordinal(int(text))
    elif "." in text:
        out = decimal(text)
    else:
        out = cardinal(int(text))
    return f"{out} {unit}".strip()


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description="Numbers to Persian words")
    p.add_argument("number")
    p.add_argument("--unit", default="", help="e.g. تومان or ریال")
    p.add_argument("--ordinal", action="store_true", help="اول، دوم، سوم ...")
    args = p.parse_args(argv)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    try:
        print(to_words(args.number, args.unit, args.ordinal))
    except ValueError as e:
        print(f"error: {e}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
