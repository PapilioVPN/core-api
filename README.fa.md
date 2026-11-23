<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="assets/banner.png">
    <source media="(prefers-color-scheme: light)" srcset="assets/banner-light.png">
    <img alt="PapilioVPN Core API" src="assets/banner-light.png" width="100%">
  </picture>
</p>

<h1 align="center">PapilioVPN Core API</h1>

<p align="center" lang="fa" dir="rtl">API مرکزی مدیریت PapilioVPN. نسخهٔ ۰٫۰٫۰ شامل مدیریت دسترسی و سلامت سیستم است.</p>

<p align="center">
  <a href="README.md" lang="en"><img src="assets/flags/gb.svg" width="24" alt=""> English</a> · <strong lang="fa"><img src="assets/flags/ir-lion-and-sun.svg" width="24" alt=""> فارسی</strong> · <a href="README.ru.md" lang="ru"><img src="assets/flags/ru.svg" width="24" alt=""> Русский</a> · <a href="README.zh-CN.md" lang="zh-CN"><img src="assets/flags/cn.svg" width="24" alt=""> 简体中文</a>
</p>

<p align="center">
  <a href="https://github.com/PapilioVPN/core-api/actions/workflows/check.yml"><img alt="Checks" src="https://github.com/PapilioVPN/core-api/actions/workflows/check.yml/badge.svg?branch=main"></a>
</p>

<p align="center">
  <a href="#quick-start">نصب سریع</a> ·
  <a href="#capabilities">قابلیت‌ها</a> ·
  <a href="#management">APIهای مدیریتی</a> ·
  <a href="#development">توسعه</a>
</p>

<a name="quick-start"></a>

## نصب سریع

در لینوکس amd64 با Docker Engine و Compose v2، بستهٔ اجرا را از یک
[اجرای موفق Checks](https://github.com/PapilioVPN/core-api/actions/workflows/check.yml) بگیرید. فایل دانلودشده را از حالت ZIP خارج
کنید و به‌جای `YOUR_COMMIT_SHA` شناسهٔ کامیت در نام فایل را بگذارید.
نصب اولیه ایمیج‌های PostgreSQL و Redis را دریافت می‌کند.

```bash
archive=core-api-0.0.0-linux-amd64-YOUR_COMMIT_SHA.tar.gz
sha256sum -c "$archive.sha256" && tar -xzf "$archive"
cd core-api
./install.sh runtime
./run.sh runtime up
./run.sh runtime owner
curl -fsS http://127.0.0.1:8000/health
```

نصاب اطلاعات محرمانه را در `.local/runtime` می‌سازد. هنگام ارتقا این
پوشه و volume مربوط به PostgreSQL را نگه دارید. دستور owner نام، شمارهٔ
موبایل و رمز عبور را می‌پرسد و در هر دیتابیس یک Super Admin می‌سازد. آدرس
پیش‌فرض API، `127.0.0.1:8000` است. برای اجرا پشت پراکسی معکوس TLS،
`CORE_BIND` و `CORE_PORT` را هنگام بالا آوردن سرویس تنظیم کنید.

با دستورهای زیر وضعیت سرویس‌ها و لاگ‌ها را ببینید، migrationها را اجرا
کنید یا سرویس‌ها را متوقف کنید. داده‌های PostgreSQL پس از توقف باقی می‌مانند.

```bash
./run.sh runtime status
./run.sh runtime logs
./run.sh runtime migrate
./run.sh runtime stop
```

پروفایل jobs، پردازش‌های Scheduler، beat و Events را همراه با NATS
JetStream بالا می‌آورد. Scheduler تاریخچهٔ توکن‌های تمدید منقضی‌شده را پاک می‌کند.

```bash
CORE_JOBS=1 ./run.sh runtime up
```

<a name="capabilities"></a>

## قابلیت‌ها

| بخش | عملیات موجود |
| --- | --- |
| احراز هویت | ورود با رمز عبور، چرخش و ابطال توکن تمدید. |
| کاربران | ایجاد، مشاهده، ویرایش و حذف کاربران، تخصیص نقش و مدیریت رمز عبور. مشاهده و ویرایش پروفایل و رمز عبور خود. |
| نقش‌ها و مجوزها | ایجاد، مشاهده، ویرایش و حذف نقش‌ها و scopeها، و تخصیص تکی و گروهی scope به نقش. |
| سیستم | سلامت PostgreSQL و Redis و مشاهدهٔ وضعیت CPU، حافظه، دیسک، شبکه، حسگرها و پردازش‌ها با دسترسی لازم. |

<a name="management"></a>

## APIهای مدیریتی

مسیر `GET /health` وضعیت اتصال و ساعت سرور PostgreSQL را برمی‌گرداند.
فیلدهای `mobile` و `password` را به `POST /admin/auth/tokens` بفرستید.
توکن دسترسی را به صورت Bearer برای `GET /admin/account/me` و با مجوز لازم
برای مسیرهای `/admin/users`، `/admin/roles`، `/admin/scopes` و
`/admin/health` استفاده کنید.

<a name="development"></a>

## توسعه

برای ساخت و نصب از کد، در ریشهٔ ریپو دستور `./install.sh runtime` را
اجرا کنید. نصب از ایمیج موجود در رجیستری با
`./install.sh runtime IMAGE@sha256:DIGEST` انجام می‌شود. برای اجرای مستقیم
پایتون از `config.yml.sample` استفاده کنید و `PAPILIO_CONFIG` را روی فایل
تنظیمات خود قرار دهید.

برای بررسی‌ها به Python 3.13 و Docker نیاز دارید. تست‌ها روی یک PostgreSQL
ایزوله اجرا می‌شوند. wheel، بستهٔ اجرا و checksum در `dist/` ساخته می‌شوند.

```bash
./install.sh test
bash scripts/ci/check.sh
bash scripts/ci/package.sh
```
