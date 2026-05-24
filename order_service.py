import os
from datetime import datetime
from zoneinfo import ZoneInfo

import requests
from dotenv import load_dotenv

from sales_logger import log_sale

load_dotenv(".env")

THAI_TZ = ZoneInfo("Asia/Bangkok")

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")


def send_telegram_message(message: str):
    """
    ส่งข้อความเข้า Telegram
    """
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("⚠️ ไม่พบ TELEGRAM_BOT_TOKEN หรือ TELEGRAM_CHAT_ID ในไฟล์ .env")
        return False

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"

    data = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
    }

    response = requests.post(url, data=data, timeout=20)
    response.raise_for_status()

    return True


def normalize_order_item(item):
    """
    แปลง item ให้เป็นรูปแบบมาตรฐาน:
    {
        "menu": str,
        "quantity": int,
        "price": int
    }

    รองรับ key หลายแบบ เผื่อใน app.py ใช้ชื่อไม่เหมือนกัน
    """
    menu = (
        item.get("menu")
        or item.get("menu_name")
        or item.get("name")
        or item.get("title")
        or ""
    )

    quantity = (
        item.get("quantity")
        or item.get("qty")
        or item.get("amount")
        or 1
    )

    price = (
        item.get("price")
        or item.get("unit_price")
        or item.get("cost")
        or 0
    )

    menu = str(menu).strip()
    quantity = int(quantity)
    price = int(price)

    if not menu:
        raise ValueError("ไม่พบชื่อเมนูในออเดอร์")

    if quantity <= 0:
        raise ValueError("จำนวนสินค้าต้องมากกว่า 0")

    if price < 0:
        raise ValueError("ราคาสินค้าต้องไม่ติดลบ")

    return {
        "menu": menu,
        "quantity": quantity,
        "price": price,
    }


def save_single_order(menu_name: str, quantity: int, price: int):
    """
    บันทึกออเดอร์ 1 รายการลง Google Sheet
    """
    menu_name = str(menu_name).strip()
    quantity = int(quantity)
    price = int(price)

    if not menu_name:
        raise ValueError("ไม่พบชื่อเมนู")

    if quantity <= 0:
        raise ValueError("จำนวนสินค้าต้องมากกว่า 0")

    if price < 0:
        raise ValueError("ราคาสินค้าต้องไม่ติดลบ")

    log_sale(menu_name, quantity, price)

    total = quantity * price

    message = f"""🍪 มีออเดอร์ใหม่ CookieCloudyDay

รายการ: {menu_name}
จำนวน: {quantity} ชิ้น
ราคา: {price} บาท
ยอดรวม: {total} บาท

✅ บันทึกลง Google Sheet แล้ว"""

    send_telegram_message(message)

    return {
        "menu": menu_name,
        "quantity": quantity,
        "price": price,
        "total": total,
    }


def save_order_items(order_items):
    """
    บันทึกหลายรายการลง Google Sheet
    แล้วส่งสรุปเข้า Telegram เป็นข้อความเดียว

    order_items ต้องเป็น list เช่น:
    [
        {"menu": "คุกกี้ช็อกโกแลตชิพ", "quantity": 1, "price": 45},
        {"menu": "คุกกี้คอร์นเฟลกคาราเมล", "quantity": 2, "price": 55}
    ]
    """
    if not order_items:
        raise ValueError("ยังไม่มีรายการออเดอร์")

    saved_items = []
    grand_total = 0
    total_quantity = 0

    for item in order_items:
        normalized = normalize_order_item(item)

        menu = normalized["menu"]
        quantity = normalized["quantity"]
        price = normalized["price"]
        total = quantity * price

        log_sale(menu, quantity, price)

        saved_items.append({
            "menu": menu,
            "quantity": quantity,
            "price": price,
            "total": total,
        })

        grand_total += total
        total_quantity += quantity

    now = datetime.now(THAI_TZ).strftime("%Y-%m-%d %H:%M")

    item_lines = []
    for index, item in enumerate(saved_items, start=1):
        item_lines.append(
            f'{index}. {item["menu"]} x {item["quantity"]} = {item["total"]} บาท'
        )

    item_text = "\n".join(item_lines)

    message = f"""🍪 มีออเดอร์ใหม่ CookieCloudyDay

เวลา: {now}

รายการ:
{item_text}

รวมจำนวน: {total_quantity} ชิ้น
ยอดรวมทั้งหมด: {grand_total} บาท

✅ บันทึกลง Google Sheet แล้ว"""

    send_telegram_message(message)

    return {
        "items": saved_items,
        "total_quantity": total_quantity,
        "grand_total": grand_total,
    }


def save_order(menu_name: str, quantity: int, price: int):
    """
    ชื่อสั้นไว้เรียกจาก app.py
    ใช้กับออเดอร์ 1 รายการ
    """
    return save_single_order(menu_name, quantity, price)
