import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
for name in ("persian-exam-builder", "persian-rtl-documents"):
    sys.path.insert(0, str(ROOT / "skills" / name / "scripts"))

import exam_tools  # noqa: E402

try:
    import docx  # noqa: F401
    import rtl_docx  # noqa: E402
    HAVE_DOCX = True
except ImportError:
    HAVE_DOCX = False

MCQ = {"type": "mcq", "question": "کدام فرمول درست است؟", "options": ["=SUM(B:B)", "SUM B", "+B", "B=SUM"], "answer": 0}


class ExamTests(unittest.TestCase):
    def test_escape(self):
        self.assertEqual(exam_tools.esc("a=b {c} #d ~e: f"), r"a\=b \{c\} \#d \~e\: f")

    def test_answer_letter_and_index(self):
        self.assertEqual(exam_tools.answer_index({"answer": "C"}), 2)
        self.assertEqual(exam_tools.answer_index({"answer": 1}), 1)

    def test_gift_mcq(self):
        out = exam_tools.to_gift([MCQ])
        self.assertIn("=\\=SUM(B\\:B)", out)
        self.assertEqual(out.count("\n~"), 3)

    def test_gift_tf_and_short(self):
        out = exam_tools.to_gift([{"type": "tf", "question": "q", "answer": False},
                                  {"type": "short", "question": "s", "answer": ["x", "y"]}])
        self.assertIn("{FALSE}", out)
        self.assertIn("=x\n=y", out)

    def test_validate(self):
        bad = [{"type": "mcq", "question": "", "options": ["a", "a"], "answer": 5},
               {"type": "tf", "question": "q", "answer": "yes"},
               {"type": "mcq", "question": "q", "options": ["الف", "همه‌ی موارد"], "answer": 0},
               {"type": "zzz", "question": "q"}]
        problems = exam_tools.validate(bad)
        self.assertGreaterEqual(len(problems), 5)
        self.assertEqual(exam_tools.validate([MCQ]), [])

    def test_balance(self):
        qs = [dict(MCQ, answer=i % 4) for i in range(8)]
        self.assertEqual(exam_tools.balance(qs)["counts"], {"A": 2, "B": 2, "C": 2, "D": 2})

    def test_cli(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "q.json"
            p.write_text(json.dumps([MCQ], ensure_ascii=False), encoding="utf-8")
            r = subprocess.run([sys.executable, str(ROOT / "skills/persian-exam-builder/scripts/exam_tools.py"), "gift", str(p)],
                               capture_output=True, encoding="utf-8")
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertIn("::Q01::", r.stdout)


@unittest.skipUnless(HAVE_DOCX, "python-docx not installed")
class RtlDocxTests(unittest.TestCase):
    def test_markdown_to_rtl_docx(self):
        md = "# عنوان\n\nمتن **مهم**.\n\n- یک\n- دو\n\n| الف | ب |\n| --- | --- |\n| ۱ | ۲ |\n"
        doc = rtl_docx.build_from_markdown(md)
        with tempfile.TemporaryDirectory() as d:
            path = str(Path(d) / "t.docx")
            rtl_docx.save(doc, path)
            import zipfile
            xml = zipfile.ZipFile(path).read("word/document.xml").decode("utf-8")
            self.assertIn("<w:bidi", xml)
            self.assertIn("<w:rtl", xml)
            self.assertIn("<w:bidiVisual", xml)
            self.assertIn("عنوان", xml)


if __name__ == "__main__":
    unittest.main()
