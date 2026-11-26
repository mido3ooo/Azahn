from datetime import datetime
from zoneinfo import ZoneInfo
import os
import requests

TIMEZONE = ZoneInfo("Africa/Cairo")
CITY = "Cairo"
COUNTRY = "Egypt"
METHOD = 5  # الهيئة المصرية العامة للمساحة

PRAYER_NAMES_AR = {
    "Fajr": "صلاة الفجر",
    "Dhuhr": "صلاة الظهر",
    "Asr": "صلاة العصر",
    "Maghrib": "صلاة المغرب",
    "Isha": "صلاة العشاء",
}

WEEKDAYS_AR = {
    "Saturday": "السبت",
    "Sunday": "الأحد",
    "Monday": "الإثنين",
    "Tuesday": "الثلاثاء",
    "Wednesday": "الأربعاء",
    "Thursday": "الخميس",
    "Friday": "الجمعة",
}

MONTHS_AR = {
    1: "يناير",
    2: "فبراير",
    3: "مارس",
    4: "أبريل",
    5: "مايو",
    6: "يونيو",
    7: "يوليو",
    8: "أغسطس",
    9: "سبتمبر",
    10: "أكتوبر",
    11: "نوفمبر",
    12: "ديسمبر",
}


def format_arabic_date(dt: datetime) -> str:
    day_name = WEEKDAYS_AR.get(dt.strftime("%A"), dt.strftime("%A"))
    month_name = MONTHS_AR[dt.month]
    return f"{day_name} {dt.day} {month_name} {dt.year}"


def fetch_cairo_timings(dt: datetime) -> dict:
    date_str = dt.strftime("%d-%m-%Y")
    url = f"https://api.aladhan.com/v1/timingsByCity/{date_str}"
    params = {
        "city": CITY,
        "country": COUNTRY,
        "method": METHOD,
    }
    response = requests.get(url, params=params, timeout=15)
    response.raise_for_status()
    data = response.json()
    return data["data"]["timings"]


def build_message(prayer_ar: str, dt: datetime) -> str:
    formatted_date = format_arabic_date(dt)
    return f"{prayer_ar}\n{formatted_date}"


def send_to_channel(message: str) -> None:
    """
    مكان ربط خدمة الإرسال لاحقاً (Webhook / API).
    إذا عرّفت WEBHOOK_URL في Secrets داخل GitHub سيبعت طلب POST تلقائياً.
    """
    webhook_url = os.getenv("WEBHOOK_URL")
    print("الرسالة الجاهزة للإرسال:")
    print("-" * 25)
    print(message)
    print("-" * 25)

    if webhook_url:
        res = requests.post(webhook_url, json={"text": message}, timeout=15)
        res.raise_for_status()
        print("تم إرسال الطلب إلى Webhook بنجاح.")
    else:
        print("تنبيه: لم يتم ضبط WEBHOOK_URL بعد (الوضع التجريبي/السجل فقط).")


def main():
    now = datetime.now(TIMEZONE)
    timings = fetch_cairo_timings(now)
    current_hm = now.strftime("%H:%M")

    print(f"التوقيت الحالي في القاهرة: {now.strftime('%Y-%m-%d %H:%M:%S')}")

    matched = False
    for eng_key, ar_name in PRAYER_NAMES_AR.items():
        # بعض استجابات API تأتي بصيغة "HH:MM (EET)" لذلك نأخذ أول 5 أحرف فقط
        prayer_hm = timings[eng_key][:5]
        if prayer_hm == current_hm:
            matched = True
            msg = build_message(ar_name, now)
            send_to_channel(msg)

    if not matched:
        print("لا يوجد موعد صلاة مطابق للدقيقة الحالية.")


if __name__ == "__main__":
    main()
