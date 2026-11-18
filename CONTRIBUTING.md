# مشارکت / Contributing

خوشحال می‌شویم مهارت تازه اضافه کنی یا خطایی را درست کنی.

## یک مهارت تازه
1. پوشه‌ی `skills/<نام-انگلیسی-با-خط‌تیره>/` بساز.
2. فایل `SKILL.md` با این سرآیند:
   ```yaml
   ---
   name: نام-پوشه
   description: چه کار می‌کند و کِی فعال شود (حداکثر ۱۰۲۴ نویسه، بدون < و >)
   ---
   ```
3. اگر کار تکراری و دقیق است (محاسبه، تبدیل، فایل‌سازی)، به‌جای توضیح، یک اسکریپت **فقط با کتابخانه‌ی استاندارد پایتون** در `scripts/` بگذار و برایش تست بنویس.
4. متن‌های مرجع بلند را در `references/` بگذار تا `SKILL.md` کوتاه بماند.
5. اجرا کن:
   ```bash
   python scripts/validate_skills.py
   python -m unittest discover -s tests -v
   ```

## قواعد
- هر ادعا و مثال را آزمایش کن؛ خروجی ننوشته‌ی تست‌نشده نگذار.
- محتوای حقوقی، پزشکی و مالی: فقط راهنمای عمومی، با یادآوری مراجعه به متخصص.
- فونت، متن یا داده‌ی دارای حق نشر (بدون مجوز) اضافه نکن.
- مثال‌ها نباید اطلاعات واقعی افراد داشته باشند.

---

**English:** add `skills/<kebab-name>/SKILL.md` (frontmatter `name` = folder, `description` ≤ 1024 chars, no angle brackets), keep scripts stdlib-only with tests, and run the validator and unit tests before opening a PR.
