import contextlib
import io
import sys
import unittest
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
for name in ("persian-text-normalizer", "jalali-date", "persian-number-words"):
    sys.path.insert(0, str(ROOT / "skills" / name / "scripts"))

import jalali  # noqa: E402
import normalize  # noqa: E402
import num2words_fa as n2w  # noqa: E402

ZWNJ = "‌"


class NormalizeTests(unittest.TestCase):
    def test_arabic_letters(self):
        self.assertEqual(normalize.normalize("كتاب يك"), "کتاب یک")

    def test_digits_modes(self):
        self.assertEqual(normalize.normalize("١٢٣ 45"), "۱۲۳ 45")
        self.assertEqual(normalize.normalize("١٢٣ 45", digits="fa"), "۱۲۳ ۴۵")
        self.assertEqual(normalize.normalize("۱۲۳ ٤٥", digits="en"), "123 45")
        self.assertEqual(normalize.normalize("١٢٣", digits="keep"), "١٢٣")

    def test_mi_prefix_and_plural(self):
        self.assertEqual(normalize.normalize("می خواهم"), f"می{ZWNJ}خواهم")
        self.assertEqual(normalize.normalize("نمی دانم"), f"نمی{ZWNJ}دانم")
        self.assertEqual(normalize.normalize("کتاب ها"), f"کتاب{ZWNJ}ها")
        self.assertEqual(normalize.normalize("کتاب های من"), f"کتاب{ZWNJ}های من")

    def test_mi_inside_another_word_is_untouched(self):
        self.assertEqual(normalize.normalize("اسمی خوب"), "اسمی خوب")

    def test_detached_ye(self):
        self.assertEqual(normalize.normalize("خانه ی من"), f"خانه{ZWNJ}ی من")
        self.assertEqual(normalize.normalize("حرف ی"), "حرف ی")  # a letter name stays

    def test_punctuation(self):
        self.assertEqual(normalize.normalize("سلام ,من"), "سلام، من")
        self.assertEqual(normalize.normalize("چرا ?"), "چرا؟")
        self.assertEqual(normalize.normalize("الف ;ب"), "الف؛ ب")

    def test_numbers_and_english_are_not_mangled(self):
        self.assertEqual(normalize.normalize("۳,۵ و 1,000"), "۳,۵ و 1,000")
        self.assertEqual(normalize.normalize("a, b; c?"), "a, b; c?")
        self.assertEqual(normalize.normalize("ساعت ۱۲:۳۰"), "ساعت ۱۲:۳۰")

    def test_spacing(self):
        self.assertEqual(normalize.normalize("( متن )"), "(متن)")
        self.assertEqual(normalize.normalize("جمله ."), "جمله.")
        self.assertEqual(normalize.normalize("پوشه .git"), "پوشه .git")
        self.assertEqual(normalize.normalize("ســلام"), "سلام")
        self.assertEqual(normalize.normalize("الف    ب"), "الف ب")

    def test_protected_regions(self):
        src = "`می خواهم` و https://a.com/x,y?z=1 و me_x@mail.com و كتاب"
        out = normalize.normalize(src)
        self.assertIn("`می خواهم`", out)
        self.assertIn("https://a.com/x,y?z=1", out)
        self.assertIn("me_x@mail.com", out)
        self.assertTrue(out.endswith("کتاب"))
        fenced = "```\nمی خواهم كتاب\n```"
        self.assertEqual(normalize.normalize(fenced), fenced)

    def test_idempotent(self):
        src = "سلام ,من ديروز كتاب ها ي زيادي  خريدم . می خواهم ( تست ) ؟"
        once = normalize.normalize(src)
        self.assertEqual(normalize.normalize(once), once)

    def test_diacritics_only_when_asked(self):
        self.assertIn("َ", normalize.normalize("سَلام"))
        self.assertEqual(normalize.normalize("سَلام", strip_diacritics=True), "سلام")


class JalaliTests(unittest.TestCase):
    def test_nowruz_anchors(self):
        anchors = {1399: (2020, 3, 20), 1400: (2021, 3, 21), 1401: (2022, 3, 21), 1402: (2023, 3, 21),
                   1403: (2024, 3, 20), 1404: (2025, 3, 21), 1405: (2026, 3, 21), 1407: (2028, 3, 20)}
        for jy, g in anchors.items():
            self.assertEqual(jalali.to_gregorian(jy, 1, 1), date(*g), jy)

    def test_known_dates(self):
        self.assertEqual(jalali.to_jalali(2026, 11, 18), (1405, 8, 27))
        self.assertEqual(jalali.to_gregorian(1357, 11, 22), date(1979, 2, 11))
        self.assertEqual(jalali.to_gregorian(1404, 10, 1), date(2025, 12, 22))

    def test_leap_years(self):
        self.assertEqual([y for y in range(1395, 1415) if jalali.is_leap_jalali(y)], [1395, 1399, 1403, 1408, 1412])
        self.assertEqual(jalali.jalali_month_length(1403, 12), 30)
        self.assertEqual(jalali.jalali_month_length(1404, 12), 29)

    def test_round_trip_and_sequence(self):
        d, prev = date(1990, 1, 1), None
        while d < date(2050, 1, 1):
            j = jalali.to_jalali(d.year, d.month, d.day)
            self.assertEqual(jalali.to_gregorian(*j), d)
            if prev:
                py, pm, pd = prev
                if pd < jalali.jalali_month_length(py, pm):
                    expected = (py, pm, pd + 1)
                else:
                    expected = (py, pm + 1, 1) if pm < 12 else (py + 1, 1, 1)
                self.assertEqual(j, expected, d)
            prev, d = j, date.fromordinal(d.toordinal() + 1)

    def test_invalid_dates(self):
        with self.assertRaises(ValueError):
            jalali.to_gregorian(1405, 13, 1)
        with self.assertRaises(ValueError):
            jalali.to_gregorian(1404, 12, 30)  # 1404 is not a leap year

    def test_weekday_name(self):
        self.assertEqual(jalali.WEEKDAYS[date(2026, 11, 18).weekday()], "چهارشنبه")
        self.assertEqual(jalali.WEEKDAYS[date(2026, 10, 23).weekday()], "جمعه")

    def test_parse_accepts_persian_digits_and_both_calendars(self):
        self.assertEqual(jalali.parse("۱۴۰۵/۰۸/۲۷"), ("j", (1405, 8, 27)))
        self.assertEqual(jalali.parse("2026-11-18"), ("g", date(2026, 11, 18)))
        self.assertEqual(jalali.as_gregorian("1405-08-27"), date(2026, 11, 18))

    def test_cli(self):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            self.assertEqual(jalali.main(["--fa", "to-jalali", "2026-11-18"]), 0)
        self.assertIn("چهارشنبه ۲۷ آبان ۱۴۰۵", out.getvalue())
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            jalali.main(["diff", "1405/01/01", "1405/12/29"])
        self.assertIn("364", out.getvalue())
        with contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(jalali.main(["to-gregorian", "1405/13/01"]), 2)


class NumberWordTests(unittest.TestCase):
    def test_cardinals(self):
        cases = {
            0: "صفر", 7: "هفت", 11: "یازده", 21: "بیست و یک", 100: "صد", 123: "صد و بیست و سه",
            1000: "هزار", 1001: "هزار و یک", 1234: "هزار و دویست و سی و چهار", 2000: "دو هزار",
            2026: "دو هزار و بیست و شش", 100000: "صد هزار", 1000000: "یک میلیون",
            1001000: "یک میلیون و هزار", 1500000: "یک میلیون و پانصد هزار", 10 ** 9: "یک میلیارد",
            1234567: "یک میلیون و دویست و سی و چهار هزار و پانصد و شصت و هفت", -5: "منفی پنج",
        }
        for n, words in cases.items():
            self.assertEqual(n2w.cardinal(n), words, n)

    def test_ordinals(self):
        cases = {1: "اول", 2: "دوم", 3: "سوم", 10: "دهم", 13: "سیزدهم", 20: "بیستم", 21: "بیست و یکم",
                 23: "بیست و سوم", 30: f"سی{ZWNJ}ام", 31: "سی و یکم", 100: "صدم"}
        for n, words in cases.items():
            self.assertEqual(n2w.ordinal(n), words, n)

    def test_decimals(self):
        self.assertEqual(n2w.to_words("3.14"), "سه ممیز چهارده صدم")
        self.assertEqual(n2w.to_words("0.5"), "صفر ممیز پنج دهم")
        self.assertEqual(n2w.to_words("0.05"), "صفر ممیز پنج صدم")
        self.assertEqual(n2w.to_words("2.50"), "دو ممیز پنج دهم")

    def test_input_formats_and_units(self):
        self.assertEqual(n2w.to_words("۱٬۲۵۰٬۰۰۰"), "یک میلیون و دویست و پنجاه هزار")
        self.assertEqual(n2w.to_words("2,500,000", unit="تومان"), "دو میلیون و پانصد هزار تومان")
        self.assertEqual(n2w.to_words("21", as_ordinal=True), "بیست و یکم")

    def test_limits(self):
        with self.assertRaises(ValueError):
            n2w.cardinal(10 ** 18)


if __name__ == "__main__":
    unittest.main()
