# app.py
import json
import os
import re
from datetime import datetime
from zoneinfo import ZoneInfo

import gspread
import streamlit as st
from dotenv import load_dotenv
from google import genai
from google.oauth2.service_account import Credentials

from rag_engine import RAGEngine
from tarot import render_lucky_cookie_tarot

load_dotenv(".env")

# =========================
# Page Config
# =========================
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


def parse_order_from_message(message: str):
    normalized = normalize_thai_numbers(message).lower()
    menu_name = None
    price = None

    for name in sorted(MENU_PRICES.keys(), key=lambda x: -len(x)):
        if name.lower() in normalized:
            menu_name = name
            price = MENU_PRICES[name]
            break

    if not menu_name:
        return None

    if any(term in normalized for term in DemiNORE_ORDER_TERMS):
        return None

    order_intent = any(keyword in normalized for keyword in ORDER_KEYWORDS)
    quantity_match = re.search(r"(\d+)\s*(?:ชิ้น)?", normalized)
    quantity = int(quantity_match.group(1)) if quantity_match else None

    if quantity is not None:
        return {
            "menu": menu_name,
            "quantity": quantity,
            "price": price,
        }

    if order_intent:
        return {
            "menu": menu_name,
            "quantity": None,
            "price": price,
        }

    return None

api_key = os.getenv("GOOGLE_API_KEY")
client = genai.Client(api_key=api_key) if api_key else None


# =========================
# RAG / Chatbot
# =========================
@st.cache_resource
def load_rag():
    return RAGEngine(KB_PATH)


def clean_answer(text: str) -> str:
    text = text.strip()
    text = re.sub(r"^#{1,6}\s*", "", text, flags=re.MULTIDemi)
    text = text.replace("===", "")
    text = text.replace("\\n", "\n")
    return text.strip()


def build_prompt(user_question: str, context: str) -> str:
    return f"""คุณคือ Demi ผู้ช่วย AI ของร้าน CookieCloudyDay
หน้าที่ของคุณคือช่วยตอบคำถามลูกค้าเกี่ยวกับเมนู ราคา เวลาเปิดร้าน การจัดส่ง และช่องทางสั่งซื้อ

ให้ตอบโดยอ้างอิงจากข้อมูลร้านด้านล่างเป็นหลัก
ห้ามคัดลอกข้อมูลร้านทั้งก้อนออกมาตอบ ให้สรุปเฉพาะคำตอบที่เกี่ยวข้องกับคำถามเท่านั้น
ห้ามตอบด้วย markdown heading เช่น #, ##, ===
ให้ตอบเป็นข้อความธรรมดาหรือ bullet list เท่านั้น

ถ้าลูกค้าถามกว้าง ๆ เช่น "ขอเมนูหน่อย", "มีอะไรขายบ้าง", "แนะนำเมนูหน่อย"
ให้สรุปรายการเมนูหรือแนะนำเมนูจากข้อมูลที่มีได้

ถ้าลูกค้าถามเรื่องราคา ให้บอกราคาตามข้อมูลที่มีแบบสั้นและอ่านง่าย
ถ้าลูกค้าถามเรื่องสุขภาพ แพ้อาหาร ส่วนผสมเฉพาะ หรือข้อมูลที่ไม่มีในข้อมูลร้าน
ให้ตอบว่าไม่พบข้อมูลนี้ในข้อมูลร้าน และแนะนำให้ติดต่อร้านโดยตรง
ถ้าไม่พบข้อมูลจริง ๆ ให้บอกว่าไม่ทราบ อย่าแต่งข้อมูลเอง

ข้อมูลร้าน:
{context}

คำถาม: {user_question}
"""


def fallback_answer(user_question: str) -> str:
    q = user_question.lower()

    if "เปิด" in q or "กี่โมง" in q or "เวลา" in q:
        return "ร้าน CookieCloudyDay เปิดทุกวัน เวลา 10:00–20:00 น. ค่ะ"

    if "ราคา" in q:
        return """ขออภัยค่ะ ตอนนี้ระบบ AI ตอบไม่ได้ชั่วคราว แต่ Demi มีข้อมูลราคาของร้านดังนี้ค่ะ

- คุกกี้ช็อกโกแลตชิพ 45 บาท
- คุกกี้เนยสด 55 บาท
- คุกกี้ช็อกโกแลตลาวา 59 บาท
- คุกกี้ดับเบิลช็อกโกแลต 59 บาท
- คุกกี้มัทฉะไวท์ช็อก 59 บาท
- คุกกี้โอรีโอ้ครีม 50 บาท
- คุกกี้คาราเมลอัลมอนด์ 55 บาท
- คุกกี้โกโก้เฮเซลนัท 59 บาท
- คุกกี้เรดเวลเวต 55 บาท
- คุกกี้บราวนี่ฟัดจ์ 55 บาท
- คุกกี้สตรอว์เบอร์รีชีสเค้ก 59 บาท
- คุกกี้วานิลลานมสด 45 บาท
- คุกกี้แมคคาเดเมียไวท์ช็อก 65 บาท"""

    if "เมนู" in q or "ขายอะไร" in q or "มีอะไรขาย" in q or "ขอเมนู" in q:
        return """ขออภัยค่ะ ตอนนี้ระบบ AI ตอบไม่ได้ชั่วคราว แต่เมนูของร้าน CookieCloudyDay มีดังนี้ค่ะ

- คุกกี้ช็อกโกแลตชิพ
- คุกกี้เนยสด
- คุกกี้ช็อกโกแลตลาวา
- คุกกี้ดับเบิลช็อกโกแลต
- คุกกี้มัทฉะไวท์ช็อก
- คุกกี้โอรีโอ้ครีม
- คุกกี้คาราเมลอัลมอนด์
- คุกกี้โกโก้เฮเซลนัท
- คุกกี้เรดเวลเวต
- คุกกี้บราวนี่ฟัดจ์
- คุกกี้สตรอว์เบอร์รีชีสเค้ก
- คุกกี้วานิลลานมสด
- คุกกี้แมคคาเดเมียไวท์ช็อก"""

    if "ทุเรียน" in q:
        return "จากข้อมูลเมนูของทางร้านในตอนนี้ ยังไม่มีคุกกี้รสทุเรียนในเมนูนะคะ"

    if "เบอร์" in q or "โทร" in q:
        return "ข้อมูลเบอร์โทรของร้านยังไม่ได้ระบุไว้นะคะ สามารถติดต่อทางร้านได้ทาง Demi ค่ะ"

    if "ส่ง" in q or "จัดส่ง" in q:
        return "ร้าน CookieCloudyDay มีบริการจัดส่ง และสามารถรับหน้าร้านได้ค่ะ"

    if "สั่งซื้อ" in q or "สั่ง" in q:
        return "ลูกค้าสามารถสั่งซื้อผ่าน Demi ได้เลยค่ะ รับเมนูอะไรดีคะ 🍪"

    return "ขออภัยค่ะ ตอนนี้ระบบ AI ตอบไม่ได้ชั่วคราว กรุณาลองใหม่อีกครั้ง หรือสอบถามทางร้านผ่าน Demi ค่ะ"


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
    sheet_id = get_sheet_id()

    if not sheet_id:
        raise RuntimeError("ยังไม่ได้ตั้งค่า GOOGLE_SHEETS_ID ใน Secrets")

    now = datetime.now(THAI_TZ)
    today = now.strftime("%Y-%m-%d")
    total = quantity * price

    client_sheet = get_sheet_client()
    spreadsheet = client_sheet.open_by_key(sheet_id)
    worksheet = spreadsheet.sheet1

    # ให้ตรงกับหัวตารางเดิม:
    # วันที่ | เมนู | จำนวน | ราคา | ยอดรวม
    worksheet.append_row(
        [
            today,
            menu_name,
            quantity,
            price,
            total,
        ],
        value_input_option="USER_ENTERED",
    )

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
1. คุกกี้ช็อกโกแลตชิพ — 45 บาท
2. คุกกี้แมคคาเดเมียไวท์ช็อก — 65 บาท
3. คุกกี้เนยสด — 55 บาท
4. คุกกี้สตรอว์เบอร์รีชีสเค้ก — 59 บาท
5. คุกกี้ช็อกโกแลตลาวา — 59 บาท

ลูกค้าพิมพ์ชื่อเมนูพร้อมจำนวนได้เลย เช่น
“เอาคุกกี้ช็อกโกแลตชิพ 2 ชิ้น”"""

PROMO_REPLY = """ตอนนี้ CookieCloudyDay มีโปรน่ารัก ๆ ค่ะ ☁️🍪

1. Cloudy Set
ซื้อคุกกี้ครบ 3 ชิ้น ลด 10 บาท

2. Sweet Pair
ซื้อคุกกี้ช็อกโกแลตชิพ 2 ชิ้น เหลือ 85 บาท

3. Premium Treat
ซื้อคุกกี้แมคคาเดเมียไวท์ช็อก 2 ชิ้น เหลือ 125 บาท

4. Lucky Cookie Tarot
ซื้อคุกกี้ครบ 3 ชิ้น และยอดรวม 150 บาทขึ้นไป รับสิทธิ์สุ่มไพ่คุกกี้พร้อมคำทำนายฟรี 🔮

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

def direct_customer_answer(message: str):
    q = normalize_thai_text(message)

    order_intents = [
        "สั่งของ", "อยากสั่ง", "อยากสั่งซื้อ", "ขอสั่ง", "สั่งยังไง",
        "ซื้อยังไง", "สั่งซื้อ", "order", "ซื้อคุกกี้"
    ]
    menu_intents = [
        "มีเมนู", "เมนูอะไร", "เมนูทั้งหมด", "ขายอะไร", "มีอะไรขาย",
        "แนะนำเมนู", "แนะนำหน่อย", "เมนูแนะนำ", "เมนูยอดฮิต"
    ]
    promo_intents = [
        "โปร", "โปรโมชั่น", "โปรโมชัน", "ลดราคา", "มีโปรไหม", "มีโปรอะไร"
    ]
    time_intents = [
        "เปิดกี่โมง", "ร้านเปิด", "ปิดกี่โมง", "เวลาเปิด", "เปิดไหม"
    ]
    tarot_intents = [
        "สุ่มไพ่", "คำทำนาย", "ดูดวง", "ไพ่คุกกี้", "วันนี้เหมาะกับคุกกี้อะไร"
    ]

    if any(word in q for word in promo_intents):
        return PROMO_REPLY

    if any(word in q for word in time_intents):
        return "ร้าน CookieCloudyDay เปิดทุกวัน เวลา 10:00–20:00 น. ค่ะ ☁️🍪"

    if any(word in q for word in tarot_intents):
        return (
            "ได้เลยค่ะ 🔮🍪\n\n"
            "Lucky Cookie Tarot คือโปรสุ่มไพ่คุกกี้พร้อมคำทำนายประจำวัน\n"
            "เมื่อสั่งคุกกี้ครบ 3 ชิ้น และยอดรวม 150 บาทขึ้นไป "
            "ลูกค้าจะได้รับสิทธิ์สุ่มไพ่ฟรีค่ะ"
        )

    if any(word in q for word in order_intents):
        return HOT_MENU_REPLY

    if any(word in q for word in menu_intents):
        return HOT_MENU_REPLY

    return None


# ===== Dynamic best-seller menus from Google Sheets =====

DEFAULT_HOT_MENUS = [
    {"menu": "คุกกี้ช็อกโกแลตชิพ", "price": 45, "quantity": 0},
    {"menu": "คุกกี้แมคคาเดเมียไวท์ช็อก", "price": 65, "quantity": 0},
    {"menu": "คุกกี้เนยสด", "price": 55, "quantity": 0},
    {"menu": "คุกกี้สตรอว์เบอร์รีชีสเค้ก", "price": 59, "quantity": 0},
    {"menu": "คุกกี้ช็อกโกแลตลาวา", "price": 59, "quantity": 0},
]

MENU_PRICE_MAP = {
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

def _to_int(value, default=0):
    try:
        if value is None or value == "":
            return default
        return int(float(str(value).replace(",", "").strip()))
    except Exception:
        return default

@st.cache_data(ttl=300)
def get_top_selling_menus(limit=5):
    """
    อ่านยอดขายจาก Google Sheets แล้วสรุป Top menu ตามจำนวนขายจริง
    cache 5 นาที เพื่อไม่ให้โหลดชีทถี่เกินไป
    """
    try:
        import os
        import gspread
        from collections import defaultdict

        sheet_id = os.getenv("GOOGLE_SHEETS_ID", "").strip()
        cred_file = (
            os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "").strip()
            or "service-account.json"
        )

        if not sheet_id:
            return DEFAULT_HOT_MENUS[:limit]

        gc = gspread.service_account(filename=cred_file)
        sh = gc.open_by_key(sheet_id)
        ws = sh.sheet1
        rows = ws.get_all_records()

        summary = defaultdict(lambda: {"quantity": 0, "total": 0, "price": 0})

        for row in rows:
            menu = (
                row.get("เมนู")
                or row.get("menu")
                or row.get("Menu")
                or row.get("ชื่อเมนู")
                or ""
            )
            menu = str(menu).strip()
            if not menu:
                continue

            quantity = _to_int(
                row.get("จำนวน")
                or row.get("quantity")
                or row.get("Quantity")
                or 0
            )

            price = _to_int(
                row.get("ราคา")
                or row.get("price")
                or row.get("Price")
                or MENU_PRICE_MAP.get(menu, 0)
            )

            total = _to_int(
                row.get("ยอดรวม")
                or row.get("total")
                or row.get("Total")
                or (quantity * price)
            )

            summary[menu]["quantity"] += quantity
            summary[menu]["total"] += total
            summary[menu]["price"] = price or MENU_PRICE_MAP.get(menu, 0)

        if not summary:
            return DEFAULT_HOT_MENUS[:limit]

        top = sorted(
            summary.items(),
            key=lambda item: (item[1]["quantity"], item[1]["total"]),
            reverse=True
        )

        result = []
        for menu, data in top[:limit]:
            result.append({
                "menu": menu,
                "price": data["price"] or MENU_PRICE_MAP.get(menu, 0),
                "quantity": data["quantity"],
            })

        return result or DEFAULT_HOT_MENUS[:limit]

    except Exception:
        return DEFAULT_HOT_MENUS[:limit]

def get_hot_menu_reply():
    top_menus = get_top_selling_menus(limit=5)

    lines = ["ได้เลยค่ะ รับคุกกี้อะไรดีคะ 🍪", "", "วันนี้เมนูยอดฮิตของ CookieCloudyDay คือ:"]

    for index, item in enumerate(top_menus, start=1):
        menu = item["menu"]
        price = item["price"] or MENU_PRICE_MAP.get(menu, 0)
        if price:
            lines.append(f"{index}. {menu} — {price} บาท")
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
    top_menus = get_top_selling_menus(limit=5)
    return {
        str(index): item["menu"]
        for index, item in enumerate(top_menus, start=1)
    }

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

def direct_customer_answer(message: str):
    q = str(message or "").strip().lower()

    order_intents = [
        "สั่งของ", "อยากสั่ง", "อยากสั่งซื้อ", "ขอสั่ง", "สั่งยังไง",
        "ซื้อยังไง", "สั่งซื้อ", "order", "ซื้อคุกกี้"
    ]

    menu_intents = [
        "มีเมนู", "เมนูอะไร", "เมนูทั้งหมด", "ขายอะไร", "มีอะไรขาย",
        "แนะนำเมนู", "แนะนำหน่อย", "เมนูแนะนำ", "เมนูยอดฮิต"
    ]

    promo_intents = [
        "โปร", "โปรโมชั่น", "โปรโมชัน", "ลดราคา", "มีโปรไหม", "มีโปรอะไร"
    ]

    time_intents = [
        "เปิดกี่โมง", "ร้านเปิด", "ปิดกี่โมง", "เวลาเปิด", "เปิดไหม"
    ]

    tarot_intents = [
        "สุ่มไพ่", "คำทำนาย", "ดูดวง", "ไพ่คุกกี้", "วันนี้เหมาะกับคุกกี้อะไร"
    ]

    if any(word in q for word in promo_intents):
        return (
            "ตอนนี้ CookieCloudyDay มีโปรน่ารัก ๆ ค่ะ ☁️🍪\n\n"
            "1. Cloudy Set\n"
            "ซื้อคุกกี้ครบ 3 ชิ้น ลด 10 บาท\n\n"
            "2. Sweet Pair\n"
            "ซื้อคุกกี้ช็อกโกแลตชิพ 2 ชิ้น เหลือ 85 บาท\n\n"
            "3. Premium Treat\n"
            "ซื้อคุกกี้แมคคาเดเมียไวท์ช็อก 2 ชิ้น เหลือ 125 บาท\n\n"
            "4. Lucky Cookie Tarot\n"
            "ซื้อคุกกี้ครบ 3 ชิ้น และยอดรวม 150 บาทขึ้นไป รับสิทธิ์สุ่มไพ่คุกกี้พร้อมคำทำนายฟรี 🔮\n\n"
            "รับโปรไหนดีคะ"
        )

    if any(word in q for word in time_intents):
        return "ร้าน CookieCloudyDay เปิดทุกวัน เวลา 10:00–20:00 น. ค่ะ ☁️🍪"

    if any(word in q for word in tarot_intents):
        return (
            "ได้เลยค่ะ 🔮🍪\n\n"
            "Lucky Cookie Tarot คือโปรสุ่มไพ่คุกกี้พร้อมคำทำนายประจำวัน\n"
            "เมื่อสั่งคุกกี้ครบ 3 ชิ้น และยอดรวม 150 บาทขึ้นไป "
            "ลูกค้าจะได้รับสิทธิ์สุ่มไพ่ฟรีค่ะ"
        )

    if any(word in q for word in order_intents):
        return get_hot_menu_reply()

    if any(word in q for word in menu_intents):
        return get_hot_menu_reply()

    return None

rag = load_rag()

st.title("☁️ Demi ผู้ช่วย AI ของร้าน CookieCloudyDay")
st.caption("ถามเรื่องเมนู เวลาเปิด ราคา หรือข้อมูลร้านได้เลย")


# =========================
# Chatbot
# =========================
if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

prompt = st.chat_input("ถามอะไรเกี่ยวกับร้านได้เลย...")

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.chat_message("user"):
        st.write(prompt)

    normalized_prompt = normalize_menu_number_order(prompt)
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
                saved_total = append_order_to_sheet(menu_name, quantity, price)

                # Lucky Cookie Tarot promo: ครบ 3 ชิ้น และยอดรวม 150 บาทขึ้นไป
                try:
                    _promo_quantity = int(quantity)
                except Exception:
                    _promo_quantity = 0
                try:
                    _promo_total = int(saved_total)
                except Exception:
                    _promo_total = 0
                if _promo_quantity >= 3 and _promo_total >= 150:
                    st.session_state['lucky_cookie_promo'] = {
                        'quantity': _promo_quantity,
                        'total': _promo_total,
                    }
                    st.session_state['show_lucky_tarot'] = False
                    st.session_state.pop('lucky_tarot_card', None)
                else:
                    st.session_state.pop('lucky_cookie_promo', None)
                    st.session_state['show_lucky_tarot'] = False

                answer = build_order_success_reply(menu_name, quantity, saved_total)

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
                    model=MODEL_NAME,
                    contents=full_prompt,
                )
                answer = response.text.strip() if response.text else fallback_answer(prompt)
            except Exception:
                answer = fallback_answer(prompt)

    answer = clean_answer(answer)

    st.session_state.messages.append({"role": "assistant", "content": answer})

    with st.chat_message("assistant"):
        st.write(answer)


DEMI_CUSTOMER_RULES = """
กฎการตอบลูกค้าของ Demi:
- ห้ามตอบให้ลูกค้าไปติดต่อช่องทางอื่น
- ห้ามบอกว่าไม่มีช่องทางสั่งซื้อ
- ถ้าลูกค้าพิมพ์ว่า สั่งของ / อยากสั่งซื้อ / สั่งยังไง ให้แนะนำเมนูยอดฮิตและบอกให้พิมพ์ชื่อเมนูพร้อมจำนวน
- ห้ามพูดคำว่า Google Sheets, Telegram, backend, database, tool หรือระบบหลังบ้านกับลูกค้า
- ถ้ารับออเดอร์แล้ว ให้ตอบว่า รับออเดอร์เรียบร้อยค่ะ พร้อมรายการ จำนวน และยอดรวม
"""


render_lucky_cookie_tarot()
