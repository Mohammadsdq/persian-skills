#!/usr/bin/env python3
"""Jalali (Persian / Solar Hijri) <-> Gregorian dates (stdlib only).

Uses the same arithmetic as the widely used `jalaali-js` library (valid for Jalali years -61..3177).
Official holidays that follow the lunar calendar are NOT computed here.

Usage
  python jalali.py today
  python jalali.py to-jalali 2026-11-18
  python jalali.py to-gregorian 1405/08/27
  python jalali.py diff 1405/01/01 1405/12/29        # days between two dates
  python jalali.py add 1405/08/27 100                # date + N days (N may be negative)
  python jalali.py month 1405 8                      # a month calendar, Saturday first
  Add --fa to print Persian digits.  Dates are auto-detected: year >= 1700 means Gregorian.
"""
from __future__ import annotations

import argparse
import re
import sys
from datetime import date, timedelta

MONTHS = ["فروردین", "اردیبهشت", "خرداد", "تیر", "مرداد", "شهریور",
          "مهر", "آبان", "آذر", "دی", "بهمن", "اسفند"]
# index = Python's date.weekday() (Monday = 0)
WEEKDAYS = ["دوشنبه", "سه‌شنبه", "چهارشنبه", "پنجشنبه", "جمعه", "شنبه", "یکشنبه"]
BREAKS = [-61, 9, 38, 199, 426, 686, 756, 818, 1111, 1181, 1210,
          1635, 2060, 2097, 2192, 2262, 2324, 2394, 2456, 3178]
FA_DIGITS = "۰۱۲۳۴۵۶۷۸۹"


def _div(a: int, b: int) -> int:
    """Integer division truncating toward zero (like JavaScript), NOT Python's floor division."""
    q = abs(a) // abs(b)
    return q if (a < 0) == (b < 0) else -q


def _mod(a: int, b: int) -> int:
    """Remainder with the sign of `a` (like JavaScript's %), NOT Python's modulo."""
    return a - _div(a, b) * b


def _jal_cal(jy: int, without_leap: bool = False):
    """Return (leap, gy, march) for Jalali year jy."""
    bl = len(BREAKS)
    gy = jy + 621
    leap_j = -14
    jp = BREAKS[0]
    if jy < jp or jy >= BREAKS[bl - 1]:
        raise ValueError(f"Invalid Jalali year {jy}")
    jump = 0
    for i in range(1, bl):
        jm = BREAKS[i]
        jump = jm - jp
        if jy < jm:
            break
        leap_j += _div(jump, 33) * 8 + _div(_mod(jump, 33), 4)
        jp = jm
    n = jy - jp
    leap_j += _div(n, 33) * 8 + _div(_mod(n, 33) + 3, 4)
    if _mod(jump, 33) == 4 and jump - n == 4:
        leap_j += 1
    leap_g = _div(gy, 4) - _div((_div(gy, 100) + 1) * 3, 4) - 150
    march = 20 + leap_j - leap_g
    if without_leap:
        return None, gy, march
    if jump - n < 6:
        n = n - jump + _div(jump + 4, 33) * 33
    leap = _mod(_mod(n + 1, 33) - 1, 4)
    if leap == -1:
        leap = 4
    return leap, gy, march


def is_leap_jalali(jy: int) -> bool:
    return _jal_cal(jy)[0] == 0


def jalali_month_length(jy: int, jm: int) -> int:
    if jm <= 6:
        return 31
    if jm <= 11:
        return 30
    return 30 if is_leap_jalali(jy) else 29


def _g2d(gy: int, gm: int, gd: int) -> int:
    d = _div((gy + _div(gm - 8, 6) + 100100) * 1461, 4) + _div(153 * _mod(gm + 9, 12) + 2, 5) + gd - 34840408
    d -= _div(_div(gy + 100100 + _div(gm - 8, 6), 100) * 3, 4) - 752
    return d


def _d2g(jdn: int):
    j = 4 * jdn + 139361631
    j += _div(_div(4 * jdn + 183187720, 146097) * 3, 4) * 4 - 3908
    i = _div(_mod(j, 1461), 4) * 5 + 308
    gd = _div(_mod(i, 153), 5) + 1
    gm = _mod(_div(i, 153), 12) + 1
    gy = _div(j, 1461) - 100100 + _div(8 - gm, 6)
    return gy, gm, gd


def to_jalali(gy: int, gm: int, gd: int):
    date(gy, gm, gd)  # validates
    jdn = _g2d(gy, gm, gd)
    jy = _d2g(jdn)[0] - 621
    leap, gy2, march = _jal_cal(jy)
    jdn1f = _g2d(gy2, 3, march)
    k = jdn - jdn1f
    if k >= 0:
        if k <= 185:
            return jy, 1 + _div(k, 31), _mod(k, 31) + 1
        k -= 186
    else:
        jy -= 1
        k += 179
        if leap == 1:
            k += 1
    return jy, 7 + _div(k, 30), _mod(k, 30) + 1


def to_gregorian(jy: int, jm: int, jd: int) -> date:
    if not (1 <= jm <= 12) or not (1 <= jd <= jalali_month_length(jy, jm)):
        raise ValueError(f"Invalid Jalali date {jy}/{jm}/{jd}")
    _, gy, march = _jal_cal(jy, True)
    jdn = _g2d(gy, 3, march) + (jm - 1) * 31 - _div(jm, 7) * (jm - 7) + jd - 1
    return date(*_d2g(jdn))


def digits(text: str, fa: bool) -> str:
    return text.translate(str.maketrans("0123456789", FA_DIGITS)) if fa else text


def parse(text: str):
    """Return ('g', date) or ('j', (y, m, d)). Accepts Persian/Arabic digits and - / . separators."""
    text = text.translate(str.maketrans("۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩", "01234567890123456789"))
    m = re.fullmatch(r"\s*(\d{3,4})[-/.](\d{1,2})[-/.](\d{1,2})\s*", text)
    if not m:
        raise ValueError(f"Cannot read date: {text!r} (use YYYY-MM-DD or YYYY/MM/DD)")
    y, mo, d = map(int, m.groups())
    if y >= 1700:
        return "g", date(y, mo, d)
    to_gregorian(y, mo, d)  # validates
    return "j", (y, mo, d)


def as_gregorian(text: str) -> date:
    kind, val = parse(text)
    return val if kind == "g" else to_gregorian(*val)


def format_jalali(jy: int, jm: int, jd: int, weekday: int | None = None, fa: bool = False) -> str:
    out = f"{jd} {MONTHS[jm - 1]} {jy}"
    if weekday is not None:
        out = f"{WEEKDAYS[weekday]} {out}"
    return digits(out, fa)


def describe(g: date, fa: bool) -> str:
    jy, jm, jd = to_jalali(g.year, g.month, g.day)
    return (
        f"شمسی:   {format_jalali(jy, jm, jd, g.weekday(), fa)}   "
        f"({digits(f'{jy}/{jm:02d}/{jd:02d}', fa)})\n"
        f"میلادی: {g.isoformat()}"
    )


def month_calendar(jy: int, jm: int, fa: bool) -> str:
    first = to_gregorian(jy, jm, 1)
    offset = (first.weekday() - 5) % 7  # Saturday = column 0
    names = ["ش", "ی", "د", "س", "چ", "پ", "ج"]
    lines = [f"{MONTHS[jm - 1]} {jy}".center(27), " ".join(f"{n:>3}" for n in names)]
    cells = [""] * offset + [str(d) for d in range(1, jalali_month_length(jy, jm) + 1)]
    for i in range(0, len(cells), 7):
        lines.append(" ".join(f"{c:>3}" for c in cells[i:i + 7]))
    return digits("\n".join(lines), fa)


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description="Jalali <-> Gregorian helper")
    p.add_argument("--fa", action="store_true", help="print Persian digits")
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("today")
    for name in ("to-jalali", "to-gregorian"):
        sub.add_parser(name).add_argument("date")
    d = sub.add_parser("diff")
    d.add_argument("a")
    d.add_argument("b")
    a = sub.add_parser("add")
    a.add_argument("date")
    a.add_argument("days", type=int)
    m = sub.add_parser("month")
    m.add_argument("year", type=int)
    m.add_argument("month", type=int)
    args = p.parse_args(argv)

    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    try:
        if args.cmd == "today":
            print(describe(date.today(), args.fa))
        elif args.cmd in ("to-jalali", "to-gregorian"):
            print(describe(as_gregorian(args.date), args.fa))
        elif args.cmd == "diff":
            n = (as_gregorian(args.b) - as_gregorian(args.a)).days
            print(digits(f"{n} روز", args.fa))
        elif args.cmd == "add":
            print(describe(as_gregorian(args.date) + timedelta(days=args.days), args.fa))
        elif args.cmd == "month":
            print(month_calendar(args.year, args.month, args.fa))
    except ValueError as e:
        print(f"error: {e}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
