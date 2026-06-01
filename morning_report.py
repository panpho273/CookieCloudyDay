import os
from datetime import datetime
from zoneinfo import ZoneInfo

import requests
from dotenv import load_dotenv
from sales_logger import get_worksheet

load_dotenv(".env")

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

THAI_TIMEZONE = ZoneInfo("Asia/Bangkok")


def get_now_thai_time():
    """คืนค่าวันและเวลาปัจจุบันตามเวลาไทย"""
    return datetime.now(THAI_TIMEZONE)


def get_period_text(hour):
    """เลือกชื่อรายงานตามช่วงเวลาจริง"""
    if 5 <= hour < 12:
        return "รายงานเช้า"
    elif 12 <= hour < 17:
        return "รายงานบ่าย"
    elif 17 <= hour < 21:
        return "รายงานเย็น"
    else:
        return "รายงานดึก"


def get_today_sales():
    """
    อ่านข้อมูลยอดขายจาก Google Sheet
    ใช้ get_worksheet() จาก sales_logger.py เพื่อให้มั่นใจว่าอ่านชีทเดียวกับที่บันทึกยอดขาย
    """
    sheet = get_worksheet()
    rows = sheet.get_all_records()

    now = get_now_thai_time()
    today = now.strftime("%Y-%m-%d")

    today_rows = []

    for row in rows:
        row_date = str(row.get("วันที่", "")).strip()

        if row_date == today:
            today_rows.append(row)

    return now, today, today_rows


def send_telegram_message(message):
    """ส่งข้อความเข้า Telegram"""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        raise RuntimeError("ไม่พบ TELEGRAM_BOT_TOKEN หรือ TELEGRAM_CHAT_ID ในไฟล์ .env")

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"

    data = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
    }

    response = requests.post(url, data=data)
    response.raise_for_status()


def create_report():
    """สร้างข้อความสรุปยอดขาย"""
    now, today, sales = get_today_sales()

    period_text = get_period_text(now.hour)
    current_time = now.strftime("%H:%M")

    if not sales:
        return f"""☀️ {period_text} CookieCloudyDay
วันที่ {today}
เวลา {current_time} น.

วันนี้ยังไม่มียอดขายนะ 🍪"""

    total_sales = 0
    total_items = 0
    menu_summary = {}

    for row in sales:
        menu = str(row.get("เมนู", "")).strip()

        try:
            quantity = int(row.get("จำนวน", 0))
        except ValueError:
            quantity = 0

        try:
            total = float(row.get("ยอดรวม", 0))
        except ValueError:
            total = 0

        total_items += quantity
        total_sales += total

        if menu:
            menu_summary[menu] = menu_summary.get(menu, 0) + quantity

    if menu_summary:
        best_menu = max(menu_summary, key=menu_summary.get)
    else:
        best_menu = "-"

    message = f"""☀️ {period_text} CookieCloudyDay
วันที่ {today}
เวลา {current_time} น.

🍪 จำนวนชิ้นที่ขายได้: {total_items}
💰 ยอดขายรวม: {total_sales:.2f} บาท
⭐ เมนูขายดี: {best_menu}

ขอให้วันนี้เป็นวันที่ดีอีกวันนะ ☁️"""

    return message


if __name__ == "__main__":
    report = create_report()

    print(report)

    send_telegram_message(report)

    print("✅ ส่งรายงานเข้า Telegram สำเร็จ")
