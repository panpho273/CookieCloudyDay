# app.py
import json
import os
import re
from collections import Counter
import random
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
from urllib import request, parse

import gspread
import streamlit as st
from dotenv import load_dotenv
from google import genai
from google.oauth2.service_account import Credentials

from rag_engine import RAGEngine
from tarot import render_lucky_cookie_tarot
from order_service import save_order
from sales_logger import get_worksheet
from hot_menu_service import build_hot_menu_reply, get_hot_menu_number_map
import customer_language as cl

load_dotenv(".env")

# FORCE_MITR_FONT_FOR_PORTAL

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Mitr:wght@300;400;500;600;700&display=swap');

    html, body, div, span, p, label, input, textarea, button,
    [data-baseweb="popover"],
    [data-baseweb="popover"] *,
    [data-baseweb="menu"],
    [data-baseweb="menu"] *,
    [data-baseweb="select"],
    [data-baseweb="select"] *,
    [role="listbox"],
    [role="listbox"] *,
    [role="option"],
    [role="option"] * {
        font-family: 'Mitr', sans-serif !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# =========================
# Gemini Client Init
# =========================
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
MODEL_NAME = os.getenv("MODEL_NAME", "gemini-2.5-flash")

client = None
if GOOGLE_API_KEY:
    try:
        client = genai.Client(api_key=GOOGLE_API_KEY)
    except Exception as e:
        print("Gemini client init error:", repr(e))
        client = None


# =========================
# Page Config
# =========================

# ===== CookieCloudyDay Promotion Helpers =====
def clean_user_message(text):
    if not text:
        return ""

    text = text.replace("\u00A0", " ")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def is_promotion_question(message):
    message = clean_user_message(message).lower()

    promo_keywords = [
        "รับโปร",
        "โปร",
        "โปรโมชั่น",
        "โปรโมชัน",
        "มีโปรไหม",
        "มีโปรมั้ย",
        "โปรวันนี้",
        "ส่วนลด",
        "ลดราคา",
        "โปรร้าน",
        "โปรคุกกี้",
        "cookie fortune",
        "cookie club",
    ]

    return any(word in message for word in promo_keywords)


def get_promotion_reply():
    return """
ตอนนี้ CookieCloudyDay มีโปรโมชันของร้านตามนี้ค่ะ ☁️🍪

🔮 ซื้อครบ 150 บาท
รับสิทธิ์สุ่มไพ่ Cookie Fortune ฟรี 1 ใบ พร้อมข้อความน่ารักจากร้าน

🎉 สมาชิกใหม่ลด 10%
รับส่วนลดสำหรับออเดอร์แรกของสมาชิกใหม่

🎂 โปรวันเกิด
สมาชิกที่มีวันเกิดรับส่วนลดหรือของแถมจาก Cookie Club

🍪 Cookie Club
สมัครสมาชิกก่อนสั่งซื้อ เพื่อใช้สิทธิ์โปรโมชันของร้าน ทั้งส่วนลด ของแถม และสุ่มไพ่ Cookie Fortune เมื่อซื้อครบ 150 บาท
"""
# ===== End Promotion Helpers =====


# ===== CookieCloudyDay Chat Helpers =====
def clean_user_message(text):
    if not text:
        return ""

    text = text.replace("\u00A0", " ")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def is_promotion_question(message):
    message = clean_user_message(message).lower()

    promo_keywords = [
        "รับโปร",
        "โปร",
        "โปรโมชั่น",
        "โปรโมชัน",
        "มีโปรไหม",
        "มีโปรมั้ย",
        "โปรวันนี้",
        "ส่วนลด",
        "ลดราคา",
        "โปรร้าน",
        "โปรคุกกี้",
        "cookie fortune",
        "cookie club",
    ]

    return any(word in message for word in promo_keywords)


def get_promotion_reply():
    return """
ตอนนี้ CookieCloudyDay มีโปรโมชันของร้านตามนี้ค่ะ ☁️🍪

🔮 ซื้อครบ 150 บาท
รับสิทธิ์สุ่มไพ่ Cookie Fortune ฟรี 1 ใบ พร้อมข้อความน่ารักจากร้าน

🎉 สมาชิกใหม่ลด 10%
รับส่วนลดสำหรับออเดอร์แรกของสมาชิกใหม่

🎂 โปรวันเกิด
สมาชิกที่มีวันเกิดรับส่วนลดหรือของแถมจาก Cookie Club

🍪 Cookie Club
สมัครสมาชิกก่อนสั่งซื้อ เพื่อใช้สิทธิ์โปรโมชันของร้าน ทั้งส่วนลด ของแถม และสุ่มไพ่ Cookie Fortune เมื่อซื้อครบ 150 บาท
"""


def is_price_question(message):
    message = clean_user_message(message).lower()

    price_keywords = [
        "แพงมั้ย",
        "แพงไหม",
        "ราคาแรงไหม",
        "ราคาแรงมั้ย",
        "คุ้มไหม",
        "คุ้มมั้ย",
        "ราคาเท่าไหร่",
        "กี่บาท",
        "แพงปะ",
        "แพงป่ะ",
    ]

    return any(word in message for word in price_keywords)


def get_price_friendly_reply():
    return """
ไม่แพงเลยค่า ถ้าเทียบกับคุกกี้โฮมเมดที่ทำสด ๆ และใช้วัตถุดิบดี ๆ ☁️🍪

ถ้าอยากเริ่มแบบคุ้ม ๆ Demi แนะนำดูเมนูยอดนิยม หรือใช้โปรของร้านก่อนก็ได้นะคะ

บอกงบมาได้เลย เช่น “มีงบ 100 บาท” เดี๋ยว Demi ช่วยจัดเมนูให้น่ารัก ๆ ค่า 🤎
"""

def is_casual_chat(message):
    message = clean_user_message(message).lower()

    casual_keywords = [
        "น่ารัก",
        "น่ากิน",
        "หิว",
        "อยากกิน",
        "เลือกไม่ถูก",
        "แนะนำหน่อย",
        "กินไรดี",
        "อร่อยไหม",
        "อร่อยมั้ย",
        "ดีไหม",
        "ดีมั้ย",
    ]

    return any(word in message for word in casual_keywords)


def get_casual_friendly_reply():
    return """
ได้เลยค่า Demi ช่วยแนะนำให้นะคะ ☁️🍪

ถ้าอยากกินแบบเพลิน ๆ แนะนำเมนูยอดนิยมของร้านก่อนเลยค่ะ  
หรือถ้าบอกแนวที่ชอบมา เช่น หวานน้อย ช็อกโกแลต นุ่ม ๆ กรุบ ๆ Demi จะช่วยเลือกให้เหมาะกับคุณลูกค้าเลยค่า 🤎
"""

# ===== End CookieCloudyDay Chat Helpers =====



# ===== CookieCloudyDay Best Seller From Sheet =====
def is_best_seller_question(message):
    message = clean_user_message(message).lower()

    keywords = [
        "เมนูแนะนำ",
        "แนะนำเมนู",
        "แนะนำหน่อย",
        "เมนูขายดี",
        "ขายดี",
        "ยอดนิยม",
        "กินไรดี",
        "สั่งอะไรดี",
        "คุกกี้ไหนดี",
        "เมนูไหนดี",
        "อะไรอร่อย",
        "อร่อยสุด",
    ]

    return any(word in message for word in keywords)


def get_best_seller_reply_from_sheet():
    try:
        worksheet = get_worksheet()
        rows = worksheet.get_all_records()

        if not rows:
            return "ตอนนี้ Demi ยังไม่มีข้อมูลยอดขายใน Google Sheet พอจะสรุปเมนูขายดีค่ะ ☁️🍪"

        counter = Counter()

        for row in rows:
            menu_name = (
                row.get("menu_name")
                or row.get("menu")
                or row.get("product_name")
                or row.get("product")
                or row.get("item_name")
                or row.get("item")
                or row.get("name")
                or row.get("เมนู")
                or row.get("ชื่อเมนู")
                or row.get("สินค้า")
                or row.get("รายการ")
            )

            qty = (
                row.get("quantity")
                or row.get("qty")
                or row.get("amount")
                or row.get("จำนวน")
                or 1
            )

            if menu_name:
                try:
                    qty = int(float(qty))
                except Exception:
                    qty = 1

                counter[str(menu_name).strip()] += qty

        if not counter:
            headers = list(rows[0].keys()) if rows else []
            return (
                "Demi เชื่อม Google Sheet ได้แล้วค่ะ แต่ยังหาคอลัมน์ชื่อเมนูไม่เจอ ☁️🍪\n\n"
                "หัวตารางที่เจอคือ:\n"
                + ", ".join(headers)
                + "\n\nส่งหัวตารางนี้ให้คนแก้โค้ดดู แล้วจะจับชื่อคอลัมน์ให้ตรงค่ะ"
            )

        top_menus = counter.most_common(3)

        reply = "เมนูขายดีที่ Demi สรุปจาก Google Sheet ให้ค่ะ ☁️🍪\n\n"

        for i, (menu, total) in enumerate(top_menus, start=1):
            reply += f"{i}. {menu} — ขายไป {total} ชิ้น\n"

        reply += "\nถ้าบอกงบมาได้เลยนะคะ เดี๋ยว Demi ช่วยจัดเมนูให้คุ้ม ๆ ค่า 🤎"
        return reply

    except Exception as e:
        return (
            "Demi ยังดึงข้อมูลจาก Google Sheet ไม่สำเร็จค่ะ ☁️🍪\n\n"
            f"สาเหตุที่ระบบแจ้ง: {e}"
        )
# ===== End CookieCloudyDay Best Seller From Sheet =====



# ===== CCD BEST SELLER V2 START =====
def _ccd_is_bestseller_question_v2(message):
    message = clean_user_message(message).lower()

    keywords = [
        "เมนูแนะนำ",
        "แนะนำเมนู",
        "แนะนำหน่อย",
        "เมนูขายดี",
        "ขายดี",
        "ยอดนิยม",
        "กินไรดี",
        "สั่งอะไรดี",
        "คุกกี้ไหนดี",
        "เมนูไหนดี",
        "อะไรอร่อย",
        "อร่อยสุด",
    ]

    return any(word in message for word in keywords)


def _ccd_pick_value(row, keys):
    for key in keys:
        if key in row and row.get(key) not in [None, ""]:
            return row.get(key)
    return None


def _ccd_get_bestseller_reply_v2():
    try:
        worksheet = get_worksheet()
        rows = worksheet.get_all_records()

        if not rows:
            return "ตอนนี้ Demi ยังไม่มีข้อมูลเมนูจาก Google Sheet ค่ะ ☁️🍪"

        menu_keys = [
            "menu_name", "menu", "product_name", "product",
            "item_name", "item", "name",
            "เมนู", "ชื่อเมนู", "สินค้า", "รายการ"
        ]

        qty_keys = [
            "quantity", "qty", "amount", "จำนวน", "จำนวนชิ้น"
        ]

        price_keys = [
            "price", "unit_price", "total_price", "total",
            "ราคา", "ราคาต่อชิ้น", "ยอดรวม"
        ]

        counter = Counter()
        latest_price = {}

        for row in rows:
            menu_name = _ccd_pick_value(row, menu_keys)
            if not menu_name:
                continue

            menu_name = str(menu_name).strip()

            qty = _ccd_pick_value(row, qty_keys)
            try:
                qty = int(float(qty))
            except Exception:
                qty = 1

            price = _ccd_pick_value(row, price_keys)
            if price not in [None, ""]:
                price_text = str(price).strip().replace("บาท", "").strip()
                latest_price[menu_name] = price_text

            counter[menu_name] += qty

        if not counter:
            return "Demi ยังสรุปเมนูแนะนำจากข้อมูลร้านไม่ได้ตอนนี้ค่ะ ☁️🍪"

        top_menus = counter.most_common(5)

        reply_lines = []
        reply_lines.append("ได้เลยค่ะ Demi แนะนำเมนูขายดีจากข้อมูลล่าสุดของร้านให้นะคะ ☁️🍪")
        reply_lines.append("")

        for index, (menu, _) in enumerate(top_menus, start=1):
            price = latest_price.get(menu)
            reply_lines.append(f"🍪 เมนูที่ {index}: {menu}")
            if price:
                reply_lines.append(f"   ราคา {price} บาท")
            else:
                reply_lines.append("   ราคาเช็กกับร้านได้เลยค่ะ")
            reply_lines.append("")

        reply_lines.append("✨ โปรของร้าน")
        reply_lines.append("ซื้อครบ 150 บาท รับสิทธิ์สุ่มไพ่ Cookie Fortune ฟรี 1 ใบ 🔮")
        reply_lines.append("")
        reply_lines.append("ถ้าลูกค้าสนใจ สั่งได้เลยแบบนี้ค่ะ")
        reply_lines.append("เช่น “เมนูที่ 1 รับ 2 ชิ้น” หรือ “เอาเมนูที่ 2 จำนวน 1 ชิ้น” 🤎")
        reply_lines.append("")
        reply_lines.append("ถ้าอยากดูเมนูเพิ่มเติม พิมพ์ว่า “เมนูทั้งหมด” ได้เลยนะคะ")

        return "\n".join(reply_lines)

    except Exception as e:
        return "Demi ยังดึงเมนูจาก Google Sheet ไม่สำเร็จค่ะ ☁️🍪\n\nสาเหตุ: " + str(e)

# ===== CCD BEST SELLER V2 END =====



# ===== Cute Short Chat Reply START =====
def _ccd_is_short_casual_question(message):
    message = clean_user_message(message).lower().strip()

    casual_keywords = [
        "แพงจัง",
        "แพงอะ",
        "แพงอ่ะ",
        "แพงไหม",
        "แพงมั้ย",
        "เหรอ",
        "จริงดิ",
        "จริงหรอ",
        "อร่อยไหม",
        "อร่อยมั้ย",
        "น่ากิน",
        "หิว",
        "เลือกไม่ถูก",
        "กินไรดี",
        "ดีไหม",
        "ดีมั้ย",
    ]

    return any(word in message for word in casual_keywords)


def _ccd_get_short_cute_reply(message):
    message = clean_user_message(message).lower().strip()

    if "แพง" in message:
        return "ไม่แพงมากค่า ถ้าเทียบกับคุกกี้โฮมเมดทำสด ๆ ☁️🍪 ถ้าบอกงบมา Demi ช่วยเลือกเมนูคุ้ม ๆ ให้ได้นะคะ 🤎"

    if "เหรอ" in message or "หรอ" in message or "จริงดิ" in message:
        return "ใช่ค่า ☁️🍪 Demi ช่วยแนะนำเมนู โปร หรือช่วยเลือกคุกกี้ให้ได้นะคะ"

    if "อร่อย" in message or "น่ากิน" in message or "หิว" in message:
        return "น่ากินมากค่า 🍪🤎 ถ้าชอบแนวช็อกโกแลต คาราเมล หรือหวานน้อย บอก Demi ได้เลยนะคะ"

    if "เลือกไม่ถูก" in message or "กินไรดี" in message:
        return "งั้น Demi แนะนำให้เริ่มจากเมนูขายดีของร้านก่อนเลยค่ะ ☁️🍪 พิมพ์ว่า “เมนูแนะนำ” ได้เลยนะคะ"

    return "ได้เลยค่า ☁️🍪 Demi ช่วยแนะนำเมนู ราคา โปร หรือช่วยเลือกคุกกี้ให้น่ารัก ๆ ได้นะคะ"
# ===== Cute Short Chat Reply END =====



# ===== CCD CUTE CUSTOMER CHAT START =====
def _ccd_is_cute_customer_chat(message):
    message = clean_user_message(message).lower().strip()

    keywords = [
        "แพงจัง", "แพงอะ", "แพงอ่ะ", "แพงไหม", "แพงมั้ย",
        "น่ารัก", "ดีจัง", "บริการดี", "บริการดีจัง",
        "ชอบ", "ชอบมาก", "ประทับใจ",
        "อร่อยไหม", "อร่อยมั้ย", "น่ากิน", "หิว",
        "ขอบคุณ", "ขอบใจ", "โอเค", "เหรอ", "หรอ", "จริงดิ",
        "เลือกไม่ถูก", "กินไรดี", "สั่งไรดี"
    ]

    return any(word in message for word in keywords)


def _ccd_should_show_review_form(message):
    message = clean_user_message(message).lower().strip()

    review_keywords = [
        "บริการดี",
        "บริการดีจัง",
        "ดีจัง",
        "น่ารัก",
        "ชอบ",
        "ชอบมาก",
        "ประทับใจ",
        "ขอบคุณ",
        "ร้านดี",
    ]

    return any(word in message for word in review_keywords)


def _ccd_get_cute_customer_reply(message):
    message = clean_user_message(message).lower().strip()

    if "แพง" in message:
        return "ไม่แพงมากค่า เมื่อเทียบกับคุกกี้โฮมเมดทำสด ๆ และวัตถุดิบดี ๆ ☁️🍪 ถ้าบอกงบมา Demi ช่วยเลือกเมนูคุ้ม ๆ ให้ได้นะคะ 🤎"

    if "บริการดี" in message or "ดีจัง" in message or "ประทับใจ" in message:
        return "ขอบคุณมากเลยค่า ดีใจที่ชอบบริการของร้านนะคะ ☁️🍪 ถ้าสะดวก Demi ขอชวนให้คะแนนร้านนิดนึงนะคะ 🤎"

    if "น่ารัก" in message or "ชอบ" in message:
        return "แง ขอบคุณมากค่า ดีใจสุด ๆ เลย ☁️🍪 ถ้าชอบร้านเรา ฝากให้คะแนนเล็ก ๆ น้อย ๆ ได้นะคะ 🤎"

    if "อร่อย" in message or "น่ากิน" in message or "หิว" in message:
        return "น่ากินจริงค่า 🍪🤎 ถ้าชอบแนวช็อกโกแลต คาราเมล หรือหวานน้อย บอก Demi ได้เลยนะคะ เดี๋ยวช่วยเลือกให้ค่ะ"

    if "เลือกไม่ถูก" in message or "กินไรดี" in message or "สั่งไรดี" in message:
        return "งั้นเริ่มจากเมนูขายดีของร้านดีไหมคะ ☁️🍪 พิมพ์ว่า “เมนูแนะนำ” ได้เลย เดี๋ยว Demi สรุปให้ค่ะ"

    if "ขอบคุณ" in message or "ขอบใจ" in message:
        return "ยินดีมากค่า ☁️🍪 ถ้ามีอะไรให้ Demi ช่วยอีก พิมพ์มาได้เลยนะคะ 🤎"

    if "เหรอ" in message or "หรอ" in message or "จริงดิ" in message:
        return "ใช่ค่า ☁️🍪 Demi ช่วยเรื่องเมนู ราคา โปร หรือช่วยเลือกคุกกี้ให้ได้นะคะ"

    return "ได้เลยค่า ☁️🍪 Demi ช่วยแนะนำเมนู ราคา โปร หรือช่วยเลือกคุกกี้ให้น่ารัก ๆ ได้นะคะ"
# ===== CCD CUTE CUSTOMER CHAT END =====


st.set_page_config(
    page_title="Demi - CookieCloudyDay",
    page_icon="☁️",
    layout="centered",

)


# =========================
# Load CSS
# =========================
def load_css(file_path: str):
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


load_css("styles.css")


# =========================
# Config
# =========================
MODEL = "gemini-2.5-flash"
KB_PATH = "knowledge/cookiecloudyday_kb.txt"
THAI_TZ = ZoneInfo("Asia/Bangkok")

MENU_PRICES = {
    "คุกกี้ช็อกโกแลตชิพ": 45,
    "คุกกี้เนยสด": 55,
    "คุกกี้ช็อกโกแลตลาวา": 59,
    "คุกกี้ดับเบิลช็อกโกแลต": 59,
    "คุกกี้มัทฉะไวท์ช็อก": 59,
    "คุกกี้โอรีโอ้ครีม": 50,
    "คุกกี้คาราเมลอัลมอนด์": 55,
    "คุกกี้โกโก้เฮเซลนัท": 59,
    "คุกกี้เรดเวลเวต": 55,
    "คุกกี้บราวนี่ฟัดจ์": 55,
    "คุกกี้สตรอว์เบอร์รีชีสเค้ก": 59,
    "คุกกี้วานิลลานมสด": 45,
    "คุกกี้แมคคาเดเมียไวท์ช็อก": 65,
}

ORDER_KEYWORDS = ["สั่ง", "เอา", "ขอ", "อยากได้", "อยากสั่ง", "ซื้อ"]
DemiNORE_ORDER_TERMS = ["ราคา", "กี่บาท", "กี่โมง", "เวลา", "เมนู", "มีอะไรขาย", "มีอะไร"]

THAI_NUMBERS = str.maketrans(
    "๐๑๒๓๔๕๖๗๘๙",
    "0123456789",
)


def normalize_thai_numbers(text: str) -> str:
    return text.translate(THAI_NUMBERS)


def normalize_user_prompt(text: str) -> str:
    if text is None:
        return ""

    cleaned = str(text).replace("\r\n", "\n").strip()
    cleaned = re.sub(r"\n{2,}", "\n", cleaned)
    cleaned = re.sub(r"\s*\n\s*", " ", cleaned)
    cleaned = re.sub(r"\s{2,}", " ", cleaned)
    return cleaned.strip()


def parse_order_from_message(message: str):
    menu_prices = {}

    # อ่านเมนูจาก shop_menu.json
    try:
        menu_prices.update(cl.load_menu_prices_from_json("shop_menu.json"))
    except Exception:
        pass

    # สำรองจากตัวแปรเดิมใน app.py
    try:
        menu_prices.update(MENU_PRICES)
    except Exception:
        pass

    try:
        menu_prices.update(MENU_ITEMS)
    except Exception:
        pass

    # map เลขเมนูจากเมนูขายดี Top 5
    try:
        menu_number_map = get_dynamic_menu_number_map()
    except Exception:
        menu_number_map = {}

    return cl.extract_order_from_text(
        message=message,
        menu_prices=menu_prices,
        menu_number_map=menu_number_map,
    )
def load_rag():
    return RAGEngine(KB_PATH)


def get_genai_client():
    """Initialize and return Google Gemini API client."""
    try:
        api_key = get_secret_value("GOOGLE_API_KEY")
        if api_key:
            return genai.Client(api_key=api_key)
    except Exception:
        pass
    return None


def clean_answer(text: str) -> str:
    text = text.strip()
    text = re.sub(r"^#{1,6}\s*", "", text, flags=re.MULTILINE)
    text = text.replace("===", "")
    text = text.replace("\n", "\n")
    return text.strip()


def build_prompt(user_question: str, context: str) -> str:
    return f"""คุณคือ Demi ผู้ช่วย AI ของร้าน CookieCloudyDay

บทบาท:
- ตอบเหมือนพนักงานร้านคุกกี้ที่สุภาพ น่ารัก และเป็นธรรมชาติ
- ช่วยแนะนำเมนู ราคา เวลาเปิดร้าน โปรโมชัน และวิธีสั่งซื้อ
- คิดคำแนะนำเองได้ เช่น จัดกลุ่มเมนูตามรสชาติ แนะนำตามความชอบ หรือเสนอเซ็ตตัวอย่าง
- แต่ต้องคิดภายในกรอบข้อมูลร้านเท่านั้น

กฎสำคัญ:
- ใช้ Knowledge Base ด้านล่างเป็นข้อมูลหลัก
- ห้ามแต่งชื่อเมนูใหม่
- ห้ามแต่งราคาใหม่
- ห้ามบอกให้ลูกค้าไปติดต่อช่องทางภายนอก
- ลูกค้าสั่งผ่าน Demi ได้เลย
- ถ้าลูกค้าพิมพ์ชื่อเมนูพร้อมจำนวน ให้ถือว่าเป็นออเดอร์
- ถ้าไม่แน่ใจ ให้ถามกลับสั้น ๆ เพื่อเก็บข้อมูลเพิ่ม
- ห้ามตอบว่า “ระบบ AI ตอบไม่ได้ชั่วคราว”
- ห้ามตอบเป็น markdown heading เช่น #, ##, ===

แนวทางตอบ:
- ถ้าลูกค้าถามเมนู ให้ตอบจากข้อมูลร้านแบบเป็นธรรมชาติ
- ถ้าลูกค้าถามเมนูทั้งหมด ให้แสดงเมนูทั้งหมดที่มีในข้อมูลร้าน
- ถ้าลูกค้าบอกซื้อ/สั่งแต่ยังไม่ระบุเมนู ให้ถามว่ารับคุกกี้อะไรดี พร้อมแนะนำแนวรสชาติ
- ถ้าลูกค้าถามนอกเหนือข้อมูลร้าน ให้ตอบตามจริงว่าไม่มีข้อมูลนั้นในร้าน

Knowledge Base:
{context}

คำถามลูกค้า:
{user_question}
"""

def fallback_answer(user_question: str) -> str:
    q = (user_question or "").lower().strip()

    if "เปิด" in q or "กี่โมง" in q or "เวลา" in q:
        return "ร้าน CookieCloudyDay เปิดทุกวัน เวลา 10:00–20:00 น. ค่ะ"

    if "สั่ง" in q or "ซื้อ" in q or "ออเดอร์" in q:
        return (
            "ได้เลยค่ะ รับคุกกี้อะไรดีคะ 🍪\n\n"
            "ลูกค้าบอกแนวที่ชอบได้ เช่น ช็อกโกแลต เนยสด มัทฉะ คาราเมล "
            "หรือพิมพ์ชื่อเมนูพร้อมจำนวนได้เลยค่ะ"
        )

    if "โปร" in q or "โปรโมชั่น" in q or "แถม" in q or "ไพ่" in q or "ทาโร่" in q:
        return (
            "โปรเปิดร้านตอนนี้คือ ซื้อครบ 150 บาทขึ้นไป "
        )

    if "เมนู" in q or "มีอะไร" in q or "ขายอะไร" in q or "ราคา" in q:
        return (
            "ร้านมีเมนูคุกกี้หลายแนว ทั้งช็อกโกแลต เนยสด มัทฉะ คาราเมล ผลไม้ และเมนูพรีเมียมค่ะ 🍪\n\n"
            "ลูกค้าบอกแนวที่ชอบได้เลย เดี๋ยว Demi ช่วยแนะนำให้ "
            "หรือพิมพ์ว่า “เมนูทั้งหมด” เพื่อดูครบทุกเมนูค่ะ"
        )

    return (
        "Demi ช่วยได้ค่ะ 🍪 ลูกค้าถามเรื่องเมนู ราคา เวลาเปิดร้าน โปรโมชัน "
        "หรือพิมพ์ชื่อเมนูพร้อมจำนวนเพื่อสั่งได้เลยค่ะ"
    )

# =========================
# Google Sheets
# =========================
def get_secret_value(name: str) -> str:
    value = os.getenv(name, "").strip()
    if value:
        return value

    try:
        secret_value = st.secrets.get(name, "")
        if isinstance(secret_value, str):
            return secret_value.strip()
    except Exception:
        pass

    return ""


def get_sheet_id() -> str:
    return get_secret_value("GOOGLE_SHEETS_ID")


def get_sheet_client():
    import base64

    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]

    # Streamlit Cloud: ใช้ Base64 secret เท่านั้น
    json_b64 = get_secret_value("GOOGLE_SERVICE_ACCOUNT_JSON_B64")

    if json_b64:
        try:
            json_text = base64.b64decode(json_b64).decode("utf-8")
            info = json.loads(json_text)
            creds = Credentials.from_service_account_info(info, scopes=scopes)
            return gspread.authorize(creds)
        except Exception as e:
            raise RuntimeError(
                "ตั้งค่า GOOGLE_SERVICE_ACCOUNT_JSON_B64 ใน Streamlit Secrets ไม่ถูกต้อง "
                f"รายละเอียด: {e}"
            )

    # Local / Codespaces
    if os.path.exists("service-account.json"):
        creds = Credentials.from_service_account_file(
            "service-account.json",
            scopes=scopes,
        )
        return gspread.authorize(creds)

    raise RuntimeError(
        "ยังไม่ได้ตั้งค่า GOOGLE_SERVICE_ACCOUNT_JSON_B64 ใน Streamlit Secrets "
        "หรือไม่มีไฟล์ service-account.json ตอนรันในเครื่อง"
    )


def append_order_to_sheet(menu_name: str, quantity: int, price: int):
    import base64
    import json
    import os
    import re
    from pathlib import Path
    from urllib import parse, request

    menu_name = str(menu_name).strip()
    quantity = int(quantity)
    price = int(price)
    total = quantity * price

    base_dir = Path(__file__).resolve().parent

    def read_secret(name: str) -> str:
        try:
            return str(st.secrets.get(name, "")).strip()
        except Exception:
            return ""

    def decode_b64(value: str) -> str:
        value = (value or "").strip()

        if not value:
            return ""

        if value.startswith("http://") or value.startswith("https://"):
            return value

        try:
            padding = "=" * (-len(value) % 4)
            decoded = base64.b64decode(value + padding).decode("utf-8").strip()
            if decoded.startswith("http://") or decoded.startswith("https://"):
                return decoded
        except Exception:
            pass

        return value

    web_app_url = (
        decode_b64(read_secret("SHEET_WEB_APP_URL_B64"))
        or decode_b64(read_secret("SHEET_WEB_APP_URL"))
        or decode_b64(os.getenv("SHEET_WEB_APP_URL_B64", ""))
        or decode_b64(os.getenv("SHEET_WEB_APP_URL", ""))
    )

    if not web_app_url:
        for script_path in [base_dir / "script.js", Path.cwd() / "script.js"]:
            try:
                if script_path.exists():
                    script_text = script_path.read_text(encoding="utf-8")
                    match = re.search(r'const\s+SHEET_WEB_APP_URL\s*=\s*"([^"]+)"', script_text)
                    if match:
                        web_app_url = decode_b64(match.group(1).strip())
                        break
            except Exception:
                pass

    if not web_app_url or not web_app_url.startswith("https://"):
        raise RuntimeError("ไม่พบ SHEET_WEB_APP_URL_B64 หรือ URL ที่ decode แล้วใช้งานได้")

    payload = {
        "menu": menu_name,
        "menuName": menu_name,
        "menu_name": menu_name,
        "name": menu_name,
        "quantity": str(quantity),
        "qty": str(quantity),
        "price": str(price),
        "total": str(total),
        "source": "streamlit_popup",
    }

    print("append_order_to_sheet payload:", payload)
    print("append_order_to_sheet url prefix:", web_app_url[:60])

    # ใช้ form-urlencoded เพราะ Apps Script รับผ่าน e.parameter ได้ง่ายกว่า
    data = parse.urlencode(payload).encode("utf-8")

    req = request.Request(
        web_app_url,
        data=data,
        method="POST",
        headers={
            "Content-Type": "application/x-www-form-urlencoded;charset=utf-8",
        },
    )

    with request.urlopen(req, timeout=30) as res:
        response_text = res.read().decode("utf-8", errors="replace")

    print("append_order_to_sheet response:", response_text)

    try:
        response_json = json.loads(response_text)
        if response_json.get("ok") is False:
            raise RuntimeError(response_text)
    except json.JSONDecodeError:
        pass

    return total

# =========================
# UI Header
# =========================

# ===== Demi deterministic customer replies =====

MENU_ITEMS = {
    "คุกกี้ช็อกโกแลตชิพ": 45,
    "คุกกี้เนยสด": 55,
    "คุกกี้ช็อกโกแลตลาวา": 59,
    "คุกกี้ดับเบิลช็อกโกแลต": 59,
    "คุกกี้มัทฉะไวท์ช็อก": 59,
    "คุกกี้โอรีโอ้ครีม": 50,
    "คุกกี้คาราเมลอัลมอนด์": 55,
    "คุกกี้โกโก้เฮเซลนัท": 59,
    "คุกกี้เรดเวลเวต": 55,
    "คุกกี้บราวนี่ฟัดจ์": 55,
    "คุกกี้สตรอว์เบอร์รีชีสเค้ก": 59,
    "คุกกี้วานิลลานมสด": 45,
    "คุกกี้แมคคาเดเมียไวท์ช็อก": 65,
}

HOT_MENU_REPLY = """ได้เลยค่ะ รับคุกกี้อะไรดีคะ 🍪

วันนี้เมนูยอดฮิตของ CookieCloudyDay มี:
1. คุกกี้ช็อกโกแลตชิพ ราคา 45 บาท
2. คุกกี้แมคคาเดเมียไวท์ช็อก ราคา 65 บาท
3. คุกกี้เนยสด ราคา 55 บาท
4. คุกกี้สตรอว์เบอร์รีชีสเค้ก ราคา 59 บาท
5. คุกกี้ช็อกโกแลตลาวา ราคา 59 บาท

ลูกค้าพิมพ์ชื่อเมนูพร้อมจำนวนได้เลย เช่น
“เอาคุกกี้ช็อกโกแลตชิพ 2 ชิ้น”"""

PROMO_REPLY = """ตอนนี้ CookieCloudyDay มีโปรน่ารัก ๆ ค่ะ ☁️🍪





รับโปรไหนดีคะ"""

def normalize_thai_text(text: str) -> str:
    return str(text or "").strip().lower()

def build_order_success_reply(menu_name: str, quantity: int, total: int) -> str:
    return (
        "รับออเดอร์เรียบร้อยค่ะ 🍪\n\n"
        f"รายการ: {menu_name}\n"
        f"จำนวน: {quantity} ชิ้น\n"
        f"ยอดรวม: {total} บาท\n\n"
        "ขอบคุณที่สั่งคุกกี้กับ CookieCloudyDay นะคะ ☁️"
    )

def _to_int(value, default=0):
    try:
        if value is None or value == "":
            return default
        return int(float(str(value).replace(",", "").strip()))
    except Exception:
        return default

@st.cache_data(ttl=300)
def get_default_hot_menus(limit=5):
    try:
        with open("shop_menu.json", "r", encoding="utf-8") as f:
            menus = json.load(f)

        result = []
        for item in menus[:limit]:
            result.append({
                "menu": item.get("name"),
                "price": int(item.get("price", 0)),
                "quantity": 0,
            })

        if result:
            return result
    except Exception:
        pass

    return [
        {"menu": "คุกกี้ช็อกโกแลตชิพ", "price": 45, "quantity": 0},
        {"menu": "คุกกี้เนยสด", "price": 55, "quantity": 0},
        {"menu": "คุกกี้ช็อกโกแลตลาวา", "price": 65, "quantity": 0},
    ][:limit]

def get_top_selling_menus(limit=5):
    """
    อ่านยอดขายจริงจาก Google Sheet แล้วจัดอันดับเมนูขายดี
    อ่านแบบตรงคอลัมน์:
    A = วันที่, B = เมนู, C = จำนวน, D = ราคา, E = ยอดรวม
    """
    try:
        sheet = get_worksheet()
        values = sheet.get_all_values()

        summary = {}

        # ข้ามแถวหัวตาราง
        for row in values[1:]:
            # เติมช่องว่างกัน index error
            row = row + [""] * 5

            menu = str(row[1]).strip()

            if not menu:
                continue

            try:
                quantity = int(float(str(row[2]).replace(",", "").strip() or 0))
            except Exception:
                quantity = 0

            try:
                price = int(float(str(row[3]).replace(",", "").strip() or 0))
            except Exception:
                price = 0

            try:
                total = float(str(row[4]).replace(",", "").strip() or 0)
            except Exception:
                total = quantity * price

            if quantity <= 0:
                continue

            if menu not in summary:
                summary[menu] = {
                    "menu": menu,
                    "quantity": 0,
                    "total": 0,
                    "price": price,
                }

            summary[menu]["quantity"] += quantity
            summary[menu]["total"] += total

            if price:
                summary[menu]["price"] = price

        ranked = sorted(
            summary.values(),
            key=lambda item: (item["quantity"], item["total"]),
            reverse=True,
        )

        print("DEBUG top menus:", ranked[:limit])

        return ranked[:limit] if ranked else get_default_hot_menus(limit)

    except Exception as e:
        print("get_top_selling_menus error:", repr(e))
        return get_default_hot_menus(limit)


def get_hot_menu_reply():
    top_menus = get_top_selling_menus(limit=5)

    lines = ["ได้เลยค่ะ รับคุกกี้อะไรดีคะ 🍪", "", "วันนี้เมนูยอดฮิตของ CookieCloudyDay คือ:"]

    for index, item in enumerate(top_menus, start=1):
        menu = item["menu"]
        price = item["price"] or MENU_PRICE_MAP.get(menu, 0)
        if price:
            lines.append(f"{index}. {menu} ราคา {price} บาท")
        else:
            lines.append(f"{index}. {menu}")

    lines += [
        "",
        "ลูกค้าพิมพ์ชื่อเมนูพร้อมจำนวนได้เลย เช่น",
        "“เอาคุกกี้ช็อกโกแลตชิพ 2 ชิ้น”",
        "",
        "หรือพิมพ์เป็นเลขเมนูก็ได้ เช่น “รับเมนู 1 จำนวน 3 ชิ้น”"
    ]

    return "\n".join(lines)

def get_dynamic_menu_number_map():
    return get_hot_menu_number_map(limit=5)

def normalize_menu_number_order(message: str) -> str:
    text = str(message or "").strip()
    menu_map = get_dynamic_menu_number_map()

    # รองรับ:
    # รับเมนู 1 รับ 4 ชิ้น
    # เมนู 2 3 ชิ้น
    # เอาเมนูที่ 3 จำนวน 2 ชิ้น
    # ขอเบอร์ 1 5 ชิ้น
    pattern = r"(?:เมนูที่|เมนู|เบอร์|ตัวที่)\s*(\d+).*?(\d+)\s*(?:ชิ้น|อัน|กล่อง)?"
    match = re.search(pattern, text)

    if match:
        menu_no = match.group(1)
        quantity = match.group(2)
        menu_name = menu_map.get(menu_no)

        if menu_name:
            return f"เอา{menu_name} {quantity} ชิ้น"

    return text

rag = load_rag()
client = get_genai_client()

st.markdown(
    """
    <section class="hero-card">
        <div class="hero-content">
            <div class="hero-kicker">CookieCloudyDay Assistant</div>
            <h1><span class="hero-cloud">☁️</span>Demi ผู้ช่วย AI ของร้านคุกกี้</h1>
            <p>ถามเมนู เวลาเปิดร้าน ราคา หรือให้ Demi ช่วยแนะนำคุกกี้ที่เหมาะกับคุณได้เลยค่ะ</p>
        </div>
    </section>
    """,
    unsafe_allow_html=True,
)




def build_new_menu_reply(limit=5):
    """
    ตอบเมนูใหม่/เมนูน่าลอง โดยสุ่มจาก shop_menu.json
    ไม่โชว์ยอดขายหลังร้านให้ลูกค้าเห็น
    """
    try:
        menus = load_popup_menu_items()
    except Exception:
        menus = []

    if not menus:
        return (
            "ได้เลยค่า 🍪\n\n"
            "ตอนนี้ Demi ยังโหลดเมนูใหม่ให้ไม่ได้แป๊บนึงนะคะ "
            "ลูกค้าพิมพ์ว่า “เมนูทั้งหมด” เพื่อดูเมนูที่มีในร้านได้เลยค่ะ"
        )

    # ถือว่าเมนูท้ายไฟล์คือกลุ่มที่เพิ่งเพิ่ม/เมนูใหม่กว่า
    recent_pool = menus[-12:] if len(menus) > 12 else menus[:]

    count = min(limit, len(recent_pool))
    picked = random.SystemRandom().sample(recent_pool, count)

    lines = [
        "ได้เลยค่าา 🍪",
        "",
        "ถ้าถามหาเมนูใหม่ ๆ หรือเมนูน่าลอง ตอนนี้ Demi แนะนำประมาณนี้ค่ะ:",
        "",
    ]

    for index, item in enumerate(picked, start=1):
        name = item.get("name", "เมนูคุกกี้")
        price = int(item.get("price", 0) or 0)

        if price:
            lines.append(f"{index}. {name} ราคา {price} บาท")
        else:
            lines.append(f"{index}. {name}")

    lines += [
        "",
        "ถ้าชอบแนวไหนบอก Demi ได้เลยน้า เช่น ชอบช็อกโกแลต ชอบกรอบ ๆ หรือชอบหวานน้อย",
        "หรือพิมพ์ชื่อเมนูพร้อมจำนวนได้เลย เช่น “เอาเมนู 1 จำนวน 2 ชิ้น”",
    ]

    return "\n".join(lines)


def direct_customer_answer(message: str):
    q = (message or "").lower().strip()

    new_menu_keywords = [
        "เมนูใหม่",
        "มีเมนูใหม่ไหม",
        "เมนูที่เพิ่งเพิ่ม",
        "เมนูมาใหม่",
        "คุกกี้ใหม่",
        "แนะนำเมนูใหม่",
        "ตัวใหม่",
        "เมนูน่าลอง",
    ]

    if any(keyword in q for keyword in new_menu_keywords):
        return build_new_menu_reply(limit=5)

    if cl.is_order_start(q):
        return build_hot_menu_reply()

    if cl.is_hot_menu_question(q):
        return build_hot_menu_reply()

    if any(keyword in q for keyword in ["โปร", "โปรโมชั่น", "แถม", "รับโปร", "ไพ่", "ทาโร่"]):
        st.session_state["show_lucky_tarot"] = False
        st.session_state.pop("lucky_tarot_card", None)
        st.session_state.pop("lucky_cookie_promo", None)
        return PROMO_REPLY

    flavor_preference = cl.detect_flavor_preference(q)
    if flavor_preference:
        return cl.build_flavor_reply(flavor_preference)

    if cl.has_order_intent(q):
        return None
    return None
def load_popup_menu_items():
    base_dir = Path(__file__).resolve().parent

    possible_paths = [
        base_dir / "shop_menu.json",
        Path.cwd() / "shop_menu.json",
        base_dir / "knowledge" / "shop_menu.json",
    ]

    for menu_path in possible_paths:
        try:
            if not menu_path.exists():
                continue

            with open(menu_path, "r", encoding="utf-8") as f:
                menus = json.load(f)

            result = []
            for item in menus:
                if not isinstance(item, dict):
                    continue

                name = item.get("name") or item.get("menu") or item.get("title")
                price = item.get("price") or item.get("cookie_price") or 0

                if name:
                    result.append({
                        "name": str(name),
                        "price": int(price),
                    })

            if result:
                return result
        except Exception:
            pass

    # fallback: ถ้า shop_menu.json ไม่อยู่ใน Streamlit ให้ดึงจาก knowledge แทน
    kb_paths = [
        base_dir / "knowledge" / "cookiecloudyday_kb.txt",
        Path.cwd() / "knowledge" / "cookiecloudyday_kb.txt",
    ]

    for kb_path in kb_paths:
        try:
            if not kb_path.exists():
                continue

            text = kb_path.read_text(encoding="utf-8")
            result = []

            for line in text.splitlines():
                match = re.search(r"\d+\.\s*(คุกกี้.+?)\s+ราคา\s+(\d+)\s+บาท", line)
                if match:
                    result.append({
                        "name": match.group(1).strip(),
                        "price": int(match.group(2)),
                    })

            if result:
                return result
        except Exception:
            pass

    return []

def send_realtime_order_to_telegram(menu_name, quantity, price, total):
    token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    chat_id = os.getenv("TELEGRAM_CHAT_ID", "").strip()

    if not token or not chat_id:
        return False

    try:
        from urllib import parse, request

        message = (
            "🍪 CookieCloudyDay มีออเดอร์ใหม่\n"
            f"เมนู: {menu_name}\n"
            f"จำนวน: {quantity} ชิ้น\n"
            f"ราคา/ชิ้น: {price:,} บาท\n"
            f"ยอดรวม: {total:,} บาท"
        )

        url = f"https://api.telegram.org/bot{token}/sendMessage"
        payload = parse.urlencode({
            "chat_id": chat_id,
            "text": message,
        }).encode("utf-8")

        req = request.Request(url, data=payload, method="POST")
        with request.urlopen(req, timeout=20) as res:
            res.read()

        return True
    except Exception:
        return False


def is_menu_popup_request(message: str):
    q = (message or "").lower().strip()
    keywords = [
        "เมนูทั้งหมด",
        "ดูเมนูทั้งหมด",
        "เปิดเมนู",
        "เลือกเมนู",
        "มีเมนูอะไรบ้าง",
        "เมนูอื่น",
        "มีเมนูใหม่",
    ]
    return any(k in q for k in keywords)


@st.dialog("🍪 เลือกเมนู CookieCloudyDay")
def render_menu_order_popup():
    menus = load_popup_menu_items()

    if not menus:
        st.error("ยังโหลดเมนูไม่ได้ค่ะ กรุณาตรวจสอบ shop_menu.json")
        return

    st.markdown(
        """
        <div class="order-popup-shell">
            <div class="order-popup-title-row">
                <div>
                    <div class="order-popup-kicker">🍪 CookieCloudyDay</div>
                    <div class="order-popup-title">เลือกคุกกี้ที่อยากสั่ง</div>
                    <div class="order-popup-subtitle">
                        เลือกเมนูและจำนวนได้เลยน้า เดี๋ยว Demi สรุปออเดอร์ให้ค่ะ
                    </div>
                </div>
            </div>
        """,
        unsafe_allow_html=True,
    )

    # แสดงแค่ชื่อเมนูใน dropdown เพราะราคาสรุปอยู่ในกล่องออเดอร์แล้ว
    menu_names = [str(item["name"]) for item in menus]

    selected_label = st.selectbox(
        "เมนูที่อยากสั่ง",
        menu_names,
        key="popup_selected_menu",
    )

    selected_index = menu_names.index(selected_label)
    selected_item = menus[selected_index]

    quantity = st.number_input(
        "อยากรับกี่ชิ้น",
        min_value=1,
        max_value=999,
        value=1,
        step=1,
        key="popup_quantity",
    )

    menu_name_preview = str(selected_item["name"])
    price_preview = int(selected_item["price"])
    qty_preview = int(quantity)
    total = price_preview * qty_preview

    st.markdown(
        f"""
        <div class="order-summary-box">
            <div class="order-summary-title">สรุปออเดอร์ของคุณ</div>
            <div class="order-summary-row">
                <span>เมนู</span>
                <strong>{menu_name_preview}</strong>
            </div>
            <div class="order-summary-row">
                <span>จำนวน</span>
                <strong>{qty_preview} ชิ้น</strong>
            </div>
            <div class="order-summary-total">
                <span>รวมทั้งหมด</span>
                <strong>{total:,} บาท</strong>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col1, col2 = st.columns(2)

    with col1:
        if st.button("เพิ่มลงออเดอร์", type="primary", use_container_width=True):
            menu_name = menu_name_preview
            price = price_preview
            qty = qty_preview
            total = price * qty

            save_result = save_order(menu_name, qty, price)
            total = int(save_result["total"])

            promo_text = ""
            if total >= 150:
                st.session_state["lucky_cookie_promo"] = {
                    "quantity": qty,
                    "total": total,
                    "menu": menu_name,
                }
                st.session_state.pop("lucky_tarot_card", None)
                st.session_state["show_lucky_tarot"] = True
            else:
                st.session_state.pop("lucky_cookie_promo", None)
                st.session_state["show_lucky_tarot"] = False

            answer = (
                f"เรียบร้อยค่า เพิ่มออเดอร์ให้แล้วนะคะ 🍪\n\n"
                f"เมนู: {menu_name}\n"
                f"จำนวน: {qty} ชิ้น\n"
                f"รวมทั้งหมด: {total:,} บาท"
                f"{promo_text}\n\n"
                f"ขอบคุณที่สั่งคุกกี้กับ CookieCloudyDay นะคะ ☁️"
            )

            st.session_state.messages.append({
                "role": "assistant",
                "content": answer,
            })

            st.session_state.show_menu_order_popup = False
    
    with col2:
        if st.button("ยกเลิก", use_container_width=True):
            st.session_state.show_menu_order_popup = False
    
    st.markdown("</div>", unsafe_allow_html=True)


# =========================
# Session State Init
# =========================
if "messages" not in st.session_state:
    st.session_state["messages"] = []

if "show_menu_order_popup" not in st.session_state:
    st.session_state["show_menu_order_popup"] = False

if "show_lucky_tarot" not in st.session_state:
    st.session_state["show_lucky_tarot"] = False

if st.session_state.get("show_lucky_tarot") and not st.session_state.get("lucky_cookie_promo"):
    st.session_state["show_lucky_tarot"] = False


def render_chat_history():
    for message in st.session_state.get("messages", []):
        role = message.get("role")
        content = message.get("content", "")
        if role == "user":
            with st.chat_message("user", avatar="🙂"):
                st.write(content)
        else:
            with st.chat_message("assistant", avatar="🤖"):
                st.write(content)

# กัน st.dialog ซ้อนกัน: ถ้าโปรไพ่กำลังจะขึ้น ต้องปิด popup เมนูก่อน
if st.session_state.get("show_lucky_tarot"):
    st.session_state["show_menu_order_popup"] = False
elif st.session_state.get("show_menu_order_popup"):
    render_menu_order_popup()

render_chat_history()








# ===== CCD REVIEW FORM START =====
st.markdown("""
<style>
.cookie-review-box {
    background: rgba(255, 255, 255, 0.72);
    border: 1.5px solid rgba(167, 119, 255, 0.28);
    border-radius: 28px;
    padding: 22px 24px;
    margin: 18px 0 22px 0;
    box-shadow: 0 12px 32px rgba(145, 103, 255, 0.10);
}

.cookie-review-title {
    font-size: 24px;
    font-weight: 800;
    color: #4b2a1f;
    margin-bottom: 6px;
}

.cookie-review-subtitle {
    color: #8a6f68;
    font-size: 15px;
    margin-bottom: 14px;
}

div[data-testid="stRadio"] label {
    background: #ffffff;
    border: 1.5px solid #e8dcff;
    border-radius: 18px;
    padding: 8px 12px;
    margin-right: 6px;
    box-shadow: 0 6px 14px rgba(141, 92, 246, 0.08);
}

div[data-testid="stRadio"] label:hover {
    border-color: #9b6df3;
    box-shadow: 0 8px 18px rgba(141, 92, 246, 0.16);
}

textarea {
    border: 1.5px solid #c7adff !important;
    border-radius: 18px !important;
    background: #fffaff !important;
    color: #4b2a1f !important;
}

div[data-testid="stFormSubmitButton"] button {
    background: linear-gradient(135deg, #9b6df3, #7f56d9) !important;
    color: white !important;
    border: none !important;
    border-radius: 999px !important;
    padding: 10px 24px !important;
    font-weight: 700 !important;
    box-shadow: 0 10px 22px rgba(127, 86, 217, 0.28) !important;
}

div[data-testid="stFormSubmitButton"] button:hover {
    transform: translateY(-1px);
    box-shadow: 0 14px 26px rgba(127, 86, 217, 0.35) !important;
}
</style>
""", unsafe_allow_html=True)


def _ccd_save_review_to_sheet(rating, review_text):
    worksheet = get_worksheet()

    now = datetime.now(ZoneInfo("Asia/Bangkok"))
    date_text = now.strftime("%Y-%m-%d")
    time_text = now.strftime("%H:%M:%S")

    review_text = str(review_text).strip()
    if not review_text:
        review_text = "ลูกค้าให้คะแนน แต่ไม่ได้พิมพ์ข้อความรีวิว"

    worksheet.append_row(
        [
            date_text,
            time_text,
            int(rating),
            review_text,
            "CookieCloudyDay Website",
        ],
        value_input_option="USER_ENTERED",
    )


if st.session_state.get("show_review_form", False):
    st.markdown('<div class="cookie-review-box">', unsafe_allow_html=True)
    st.markdown('<div class="cookie-review-title">ให้คะแนนร้าน CookieCloudyDay หน่อยนะคะ ☁️🍪</div>', unsafe_allow_html=True)
    st.markdown('<div class="cookie-review-subtitle">เลือกดาวแล้วฝากรีวิวสั้น ๆ ให้ร้านได้เลยค่ะ</div>', unsafe_allow_html=True)

    with st.form("cookiecloudyday_review_form"):
        rating = st.radio(
            "ความประทับใจของลูกค้า",
            options=[1, 2, 3, 4, 5],
            index=4,
            horizontal=True,
            format_func=lambda x: "⭐" * x,
        )

        review_text = st.text_area(
            "รีวิวสั้น ๆ ให้ร้านได้เลยค่ะ",
            placeholder="เช่น บริการน่ารัก คุกกี้อร่อยมาก",
        )

        submitted_review = st.form_submit_button("ส่งรีวิว")

        if submitted_review:
            try:
                _ccd_save_review_to_sheet(rating, review_text)
                st.session_state.show_review_form = False
                st.success(f"ขอบคุณสำหรับ {rating} ดาวนะคะ 🤎 รีวิวถูกบันทึกเข้าชีทแล้วค่ะ")
                st.rerun()
            except Exception as e:
                st.error(f"บันทึกรีวิวลงชีทไม่สำเร็จค่ะ: {e}")

    st.markdown("</div>", unsafe_allow_html=True)
# ===== CCD REVIEW FORM END =====


prompt = st.chat_input("ถามอะไรเกี่ยวกับร้านได้เลย...")



if prompt:
    # CCD_CUTE_CHAT_DIRECT_START
    if _ccd_is_cute_customer_chat(prompt):
        answer = _ccd_get_cute_customer_reply(prompt)

        if _ccd_should_show_review_form(prompt):
            st.session_state.show_review_form = True

        if "messages" not in st.session_state:
            st.session_state.messages = []

        st.session_state.messages.append({"role": "user", "content": prompt})
        st.session_state.messages.append({"role": "assistant", "content": answer})
        st.rerun()
    # CCD_CUTE_CHAT_DIRECT_END


    # CCD_SHORT_CUTE_DIRECT_START
    if _ccd_is_short_casual_question(prompt):
        answer = _ccd_get_short_cute_reply(prompt)

        if "messages" not in st.session_state:
            st.session_state.messages = []

        st.session_state.messages.append({"role": "user", "content": prompt})
        st.session_state.messages.append({"role": "assistant", "content": answer})
        st.rerun()
    # CCD_SHORT_CUTE_DIRECT_END


    # CCD_BEST_SELLER_DIRECT_V2_START
    prompt = clean_user_message(prompt)

    if _ccd_is_bestseller_question_v2(prompt):
        answer = _ccd_get_bestseller_reply_v2()

        if "messages" not in st.session_state:
            st.session_state.messages = []

        st.session_state.messages.append({"role": "user", "content": prompt})
        st.session_state.messages.append({"role": "assistant", "content": answer})
        st.rerun()
    # CCD_BEST_SELLER_DIRECT_V2_END


    # BEST_SELLER_DIRECT_START
    prompt = clean_user_message(prompt)

    if is_best_seller_question(prompt):
        answer = get_best_seller_reply_from_sheet()

        st.session_state.messages.append({"role": "user", "content": prompt})
        st.session_state.messages.append({"role": "assistant", "content": answer})
        st.rerun()
    # BEST_SELLER_DIRECT_END


    prompt = normalize_user_prompt(prompt)
    if prompt:
        st.session_state.messages.append({"role": "user", "content": prompt})

        with st.chat_message("user", avatar="🙂"):
            st.write(prompt)

        normalized_prompt = normalize_menu_number_order(prompt)

        if is_menu_popup_request(normalized_prompt):
            st.session_state.show_menu_order_popup = True

            answer = (
                "ได้เลยค่ะ เปิดเมนูทั้งหมดให้เลือกแล้วนะคะ 🍪\n\n"
                "ลูกค้าสามารถเลือกเมนูและจำนวนจากหน้าต่าง popup ได้เลยค่ะ"
            )
            st.session_state.messages.append({
                "role": "assistant",
                "content": answer,
            })

    
        promo_keywords = ["โปร", "โปรโมชั่น", "แถม", "รับโปร", "ไพ่", "ทาโร่"]
        if any(keyword in normalized_prompt for keyword in promo_keywords):
            st.session_state["show_lucky_tarot"] = False
            st.session_state.pop("lucky_tarot_card", None)
            st.session_state.pop("lucky_cookie_promo", None)
            answer = PROMO_REPLY
    else:
        order_data = parse_order_from_message(normalized_prompt)
        direct_answer = direct_customer_answer(prompt)

        if order_data:
            try:
                menu_name = (
                    order_data.get("menu_name")
                    or order_data.get("menu")
                    or order_data.get("name")
                )
                quantity = int(order_data.get("quantity", 1))
                price = int(order_data.get("price") or MENU_ITEMS.get(menu_name, 0))

                if not menu_name or quantity <= 0 or price <= 0:
                    answer = "ขออภัยค่ะ Demi ยังอ่านออเดอร์ไม่ครบ รบกวนพิมพ์ชื่อเมนูและจำนวนอีกครั้งนะคะ เช่น “เอาคุกกี้ช็อกโกแลตชิพ 2 ชิ้น”"
                else:
                    save_result = save_order(menu_name, quantity, price)
                    saved_total = int(save_result["total"])

                    try:
                        _promo_quantity = int(quantity)
                    except Exception:
                        _promo_quantity = 0

                    try:
                        _promo_total = int(saved_total)
                    except Exception:
                        _promo_total = 0

                    if _promo_total >= 150:
                        from tarot import draw_random_card
                        card = draw_random_card()
                        st.session_state["lucky_cookie_promo"] = {
                            "ordered_menu": menu_name,
                            "quantity": _promo_quantity,
                            "total": _promo_total,
                            "card_name": card.get("name"),
                            "freebie_cookie": card.get("cookie"),
                            "freebie_text": card.get("freebie_text"),
                        }
                        st.session_state["show_lucky_tarot"] = True
                        st.session_state["lucky_tarot_card"] = card
                    else:
                        st.session_state.pop("lucky_cookie_promo", None)
                        st.session_state["show_lucky_tarot"] = False
                        st.session_state.pop("lucky_tarot_card", None)

                    answer = build_order_success_reply(menu_name, quantity, saved_total)

                    if _promo_total >= 150:
                        promo = st.session_state.get("lucky_cookie_promo", {})
                        freebie_cookie = promo.get("freebie_cookie", "คุกกี้")

            except Exception:
                answer = "ขออภัยค่ะ ตอนนี้ Demi รับออเดอร์ไม่สำเร็จ ลองพิมพ์ชื่อเมนูและจำนวนอีกครั้งนะคะ"

        elif direct_answer:
            answer = direct_answer

        else:
            context_chunks = rag.search(prompt, top_k=5)
            context = "\n\n".join(context_chunks)
            full_prompt = build_prompt(prompt, context)

            if not client:
                answer = fallback_answer(prompt)
            else:
                try:
                    response = client.models.generate_content(
                        model=MODEL,
                        contents=full_prompt,
                    )
                    answer = response.text.strip() if response.text else fallback_answer(prompt)
                except Exception:
                    answer = fallback_answer(prompt)

        answer = answer if "answer" in locals() else fallback_answer(prompt)
    if is_promotion_question(prompt):
        answer = get_promotion_reply()

    if is_price_question(prompt):
        answer = get_price_friendly_reply()
    elif is_promotion_question(prompt):
        answer = get_promotion_reply()

    try:
        answer
    except NameError:
        answer = fallback_answer(prompt)

    if is_price_question(prompt):

        answer = get_price_friendly_reply()

    elif is_promotion_question(prompt):

        answer = get_promotion_reply()

    elif is_casual_chat(prompt):

        answer = get_casual_friendly_reply()


    try:

        answer

    except NameError:

        answer = fallback_answer(prompt)


    try:


        answer


    except NameError:


        answer = fallback_answer(prompt)



    answer = clean_answer(answer)

    st.session_state.messages.append({"role": "assistant", "content": answer})

    st.rerun()
# แสดง Lucky Tarot dialog ถ้าลูกค้าเข้าเงื่อนไขโปร
# ต้องอยู่นอก if prompt เพราะ popup จะ st.rerun() แล้วไม่มี prompt ใหม่
if st.session_state.get("show_lucky_tarot"):
    render_lucky_cookie_tarot()


DEMI_CUSTOMER_RULES = """
กฎการตอบลูกค้าของ Demi:
- ห้ามตอบให้ลูกค้าไปติดต่อช่องทางอื่น
- ห้ามบอกว่าไม่มีช่องทางสั่งซื้อ
- ถ้าลูกค้าพิมพ์ว่า สั่งของ / อยากสั่งซื้อ / สั่งยังไง ให้แนะนำเมนูยอดฮิตและบอกให้พิมพ์ชื่อเมนูพร้อมจำนวน
- ห้ามพูดคำว่า Google Sheets, Telegram, backend, database, tool หรือระบบหลังบ้านกับลูกค้า
- ถ้ารับออเดอร์แล้ว ให้ตอบว่า รับออเดอร์เรียบร้อยค่ะ พร้อมรายการ จำนวน และยอดรวม
"""








