<div dir="ltr">

[English](README.md) · **فارسی**

</div>

<div dir="rtl">

# مهارت‌های فارسی برای Claude · Persian Skills

مجموعه‌ای از **Agent Skills** برای کسانی که با Claude به فارسی کار می‌کنند: معلم، دانشجو، کارمند، مدرس کامپیوتر. هر مهارت یک پوشه‌ی `SKILL.md` است و جاهایی که دقت لازم است (تاریخ شمسی، عدد به حروف، نیم‌فاصله، ورد راست‌چین) یک **اسکریپت تست‌شده** دارد، یعنی Claude حدس نمی‌زند، محاسبه می‌کند.

> A collection of Agent Skills (SKILL.md + tested stdlib-only scripts) that teach Claude the everyday Persian tasks it tends to get wrong: Jalali dates, ZWNJ/half-space typography, numbers in words, RTL Word/PDF/Excel files, formal letters, exams and lesson plans.

![tests](https://github.com/Mohammadsdq/persian-skills/actions/workflows/ci.yml/badge.svg)
![license](https://img.shields.io/badge/license-MIT-blue)

## مهارت‌ها

| مهارت | کار | اسکریپت |
| --- | --- | --- |
| `persian-text-normalizer` | یکدست‌سازی متن: ي/ك عربی، ارقام، نیم‌فاصله (می‌خواهم، کتاب‌ها)، نقطه‌گذاری فارسی | `normalize.py` |
| `jalali-date` | تبدیل شمسی/میلادی، اختلاف و جمع تاریخ، تقویم ماه | `jalali.py` |
| `persian-number-words` | عدد به حروف، ترتیبی، اعشار، مبلغ با واحد (برای چک و قرارداد) | `num2words_fa.py` |
| `persian-rtl-documents` | ساخت Word، PDF، Excel و نمودار فارسیِ راست‌به‌چپ بدون به‌هم‌ریختگی | `rtl_docx.py` |
| `persian-formal-letter` | نامه‌ی اداری، درخواست، شکایت، استعفا، قدردانی (۷ قالب) | قالب‌ها |
| `persian-proofreader` | ویرایش و غلط‌گیری با فهرست خطاهای رایج | مرجع |
| `persian-exam-builder` | طراحی آزمون، خروجی Moodle (GIFT)، بررسی توازن گزینه‌ها، نمونه برای ICDL | `exam_tools.py` |
| `persian-lesson-plan` | طرح درس، اهداف رفتاری، جزوه | قالب |

## نمونه‌ی خروجی واقعی

<div dir="ltr">

```text
$ echo "كتاب هاي من ,  مي خواهم  ١٢٣ نفر" | python normalize.py -
کتاب‌های من، می‌خواهم ۱۲۳ نفر

$ python num2words_fa.py 1405
هزار و چهارصد و پنج

$ python jalali.py --fa to-jalali 2026-03-21
شمسی:   شنبه ۱ فروردین ۱۴۰۵   (۱۴۰۵/۰۱/۰۱)
میلادی: 2026-03-21
```

</div>

## نصب

### Claude Code

macOS / Linux:

<div dir="ltr">

```bash
git clone https://github.com/Mohammadsdq/persian-skills.git
mkdir -p ~/.claude/skills && cp -r persian-skills/skills/* ~/.claude/skills/
```

</div>

Windows (PowerShell):

<div dir="ltr">

```powershell
git clone https://github.com/Mohammadsdq/persian-skills.git
New-Item -ItemType Directory -Force "$env:USERPROFILE\.claude\skills" | Out-Null
Copy-Item -Recurse persian-skills\skills\* "$env:USERPROFILE\.claude\skills\"
```

</div>

### claude.ai (آپلود zip)

<div dir="ltr">

```bash
python scripts/package_skills.py     # می‌سازد: dist/<نام-مهارت>.zip
```

</div>

سپس در Claude: **Settings ← Capabilities ← Skills** و zip هر مهارت را آپلود کن. (مسیر منو ممکن است با نسخه‌ها تغییر کند.)

بعد از نصب فقط فارسی بخواه: «این متن رو ویرایش کن»، «۱۴۰۵/۰۸/۲۷ چند شنبه است؟»، «گزارش رو به‌صورت ورد راست‌چین بساز».

## نیازمندی‌ها

- اسکریپت‌ها فقط پایتون ۳.۹+ و کتابخانه‌ی استاندارد دارند.
- استثنا: `rtl_docx.py` به `pip install python-docx` نیاز دارد.

## توسعه

<div dir="ltr">

```bash
python scripts/validate_skills.py
python -m unittest discover -s tests -v
```

</div>

## مشارکت

مهارت تازه، قالب نامه، یا خطایی که دیدی؟ [CONTRIBUTING.md](CONTRIBUTING.md) را ببین. Issue و PR خوش‌آمد است.

## محدودیت‌ها (صادقانه)

- تاریخ شمسی با الگوریتم محاسباتی (جلالی) کار می‌کند؛ برای تاریخ‌های بسیار دور یا تقویم رسمی تعطیلات، به منبع رسمی نگاه کن.
- نیم‌فاصله‌گذاری قاعده‌محور است و جای ویراستار را نمی‌گیرد.
- قالب نامه‌ها و سرفصل‌های آزمون راهنما هستند، نه متن رسمی سازمانی.
- فونت‌ها همراه ریپو نیست؛ Vazirmatn را جدا نصب کن.

## مجوز

MIT

</div>
