---
name: persian-rtl-documents
description: Create Persian right-to-left documents that look correct - Word (.docx), PDF from HTML, Excel sheets, and charts with Persian labels. Handles RTL direction, mirrored tables, Persian fonts, mixed Persian/English/number text, and page numbers. Use when the user wants a فایل ورد فارسی، گزارش PDF فارسی، جدول راست‌چین، اکسل راست‌به‌چپ، نمودار با متن فارسی, or when Persian text comes out left-aligned, reversed or with broken punctuation in a generated file.
---

# اسناد فارسی (راست‌به‌چپ)

مشکل همیشگی: فایلِ ساخته‌شده با کد، فارسی را **چپ‌چین** یا **برعکس** نشان می‌دهد، لیست‌ها و جدول‌ها آینه نیستند، و نقطه و پرانتز جابه‌جا می‌شوند. این مهارت راه درست ساخت هر فرمت را می‌دهد. همه‌ی روش‌های زیر آزمایش و رندر شده‌اند.

## ۱. Word (.docx): راه سریع

اگر محتوا را به‌صورت Markdown داری، اسکریپت همین مهارت مستقیم فایل راست‌چین می‌سازد (نیاز: `pip install python-docx`):

```bash
python3 scripts/rtl_docx.py report.md report.docx --page-numbers
python3 scripts/rtl_docx.py report.md report.docx --font Vazirmatn --size 12
python3 scripts/rtl_docx.py --demo demo.docx       # نمونه‌ی آماده
```

پشتیبانی: تیتر `# ## ###`، پاراگراف، فهرست `-`، فهرست شماره‌دار `1.`، جدول `| a | b |`، `**پررنگ**` و `<!-- pagebreak -->`.

برای کنترل بیشتر، به‌صورت کتابخانه:

```python
import sys; sys.path.insert(0, "scripts")
from rtl_docx import new_document, add_heading, add_paragraph, add_bullets, add_table, add_page_numbers, save

doc = new_document(font="Tahoma", size=12)
add_heading(doc, "گزارش ماهانه", 1)
add_paragraph(doc, "این متن **راست‌چین** است.", align="justify")
add_bullets(doc, ["مورد اول", "مورد دوم"])
add_table(doc, [["نام", "نمره"], ["علی", "۱۸"]])
add_page_numbers(doc)
save(doc, "report.docx")
```

### چرا خود `python-docx` کافی نیست

برای RTL واقعی در Word باید همه‌ی این‌ها تنظیم شود، و اسکریپت همه را انجام می‌دهد:

- `w:bidi` روی هر پاراگراف و روی سبک‌ها (جهت پاراگراف)
- `w:rtl` روی هر run (جهت متن)
- فونت **complex-script** (`w:cs`) و اندازه‌ی `w:szCs` (وگرنه Word فونت و اندازه‌ی لاتین را برای فارسی نمی‌خواند)
- `w:bidiVisual` روی جدول (ستون اول سمت راست)
- `w:bidi` روی بخش (section) و زبان `fa-IR` برای غلط‌یاب
- **ترتیب عناصر XML** (Word اگر ترتیب را رعایت نکنی فایل را خراب اعلام می‌کند)
- حذف «فونت تم» در تیترها که نام فونت را نادیده می‌گیرد

### فونت

- `Tahoma` و `Arial` روی هر ویندوزی هستند و فارسی را درست نشان می‌دهند (پیش‌فرض ما: Tahoma).
- `Vazirmatn` فونت متن‌باز و زیباست، ولی باید روی **سیستم خواننده** نصب باشد؛ وگرنه Word فونت دیگری می‌گذارد. اگر فایل را برای دیگران می‌فرستی، PDF بده.
- فونت‌های تجاری (مثل IRANSans، B Nazanin) را بدون اجازه در سند یا ریپو قرار نده.

## ۲. PDF: از طریق HTML

ساده‌ترین مسیر PDF فارسی با کیفیت: HTML راست‌چین ← PDF با Chromium. (کتابخانه‌هایی مثل ReportLab به‌طور پیش‌فرض حروف را متصل نمی‌کنند و فارسی خراب می‌شود؛ ازشان دوری کن مگر برای این کار آماده باشی.)

```html
<!doctype html>
<html lang="fa" dir="rtl">
<head><meta charset="utf-8">
<style>
  @page { size: A4; margin: 20mm; }
  body { font-family: Vazirmatn, "Noto Naskh Arabic", Tahoma, sans-serif; line-height: 1.9; font-size: 12pt; }
  table { width: 100%; border-collapse: collapse }
  th, td { border: 1px solid #999; padding: 4px 8px; text-align: right }
  code, .ltr { direction: ltr; unicode-bidi: isolate; display: inline-block }  /* کد و متن لاتین وسط جمله */
</style></head>
<body>…</body></html>
```

```python
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    b = p.chromium.launch(); page = b.new_page()
    page.goto("file:///abs/path/report.html")
    page.pdf(path="report.pdf", format="A4", print_background=True, prefer_css_page_size=True)
    b.close()
```

(یا از Chrome: `chrome --headless --print-to-pdf=report.pdf report.html`.)

## ۳. Excel (.xlsx)

```python
import openpyxl
from openpyxl.styles import Alignment
wb = openpyxl.Workbook(); ws = wb.active
ws.sheet_view.rightToLeft = True                       # ستون A سمت راست
ws.append(["نام", "درس", "نمره"])
for row in ws.iter_rows():
    for c in row:
        c.alignment = Alignment(horizontal="right", readingOrder=2)   # 2 = راست‌به‌چپ
wb.save("report.xlsx")
```

## ۴. نمودار با متن فارسی (matplotlib)

اگر حروف جدا یا برعکس دیده شد:

```python
# pip install arabic-reshaper python-bidi
import arabic_reshaper
from bidi.algorithm import get_display
fa = lambda s: get_display(arabic_reshaper.reshape(s))
plt.title(fa("فروش ماهانه"))
```

و یک فونت دارای حروف فارسی تنظیم کن (`plt.rcParams["font.family"] = "Vazirmatn"` یا `"DejaVu Sans"`).

## قواعد متن مخلوط (فارسی + لاتین + عدد)

- ارقام را یکدست کن (همه فارسی یا همه لاتین): مهارت `persian-text-normalizer`.
- عبارت لاتین یا کد وسط جمله‌ی فارسی را ایزوله کن (`unicode-bidi: isolate` در CSS)، وگرنه نقطه و پرانتز کنارش جابه‌جا می‌شود.
- پایان جمله‌ای که به لاتین ختم می‌شود: نقطه ممکن است سمت اشتباه بیفتد؛ جمله را طوری بازنویس کن که به کلمه‌ی فارسی ختم شود، یا عبارت لاتین را ایزوله کن.
- تاریخ عددی («۱۴۰۵/۰۸/۲۷») را با ارقام فارسی بنویس تا ترتیبش به‌هم نخورد.

## بررسی نهایی (حتماً)

سند را **رندر و نگاه کن**، نه فقط ذخیره:

```bash
soffice --headless --convert-to pdf report.docx && pdftoppm -r 70 -png report.pdf page
```

- متن و تیترها راست‌چین‌اند؟ بولت‌ها سمت راست‌اند؟
- ستون اول جدول سمت راست است؟
- پرانتز، نقطه و علامت‌ها سر جایشان‌اند؟
- شماره‌ی صفحه هست؟
