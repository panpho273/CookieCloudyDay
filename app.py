# app.py
import json
import os
import re
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
    normalized = normalize_thai_numbers(message or "").lower().strip()

    # คำถามทั่วไป ไม่ใช่ออเดอร์
    question_terms = [
        "กี่บาท", "กี่โมง", "เวลาเปิด", "ร้านเปิด",
        "มีอะไร", "เมนูอะไร", "ขายอะไร", "ราคาเท่าไหร่",
        "โปรอะไร", "โปรโมชั่นอะไร"
    ]
    if any(term in normalized for term in question_terms):
        return None

    # ต้องมีเจตนาสั่ง หรือมีจำนวนพร้อมหน่วย
    order_intent = any(keyword in normalized for keyword in ORDER_KEYWORDS)
    quantity_match = re.search(r"(\d+)\s*(ชิ้น|อัน|กล่อง)?", normalized)
    quantity = int(quantity_match.group(1)) if quantity_match else None

    if not order_intent and quantity is None:
        return None

    # อ่านเมนูจาก shop_menu.json เป็นหลัก
    menu_sources = []

    try:
        with open("shop_menu.json", "r", encoding="utf-8") as f:
            shop_menus = json.load(f)

        for item in shop_menus:
            if not isinstance(item, dict):
                continue

            name = item.get("name") or item.get("menu") or item.get("title")
            price = item.get("price") or item.get("cookie_price") or 0

            if name:
                menu_sources.append((str(name), int(price)))
    except Exception:
        pass

    # สำรองจาก MENU_PRICES เก่า
    for name, price in MENU_PRICES.items():
        menu_sources.append((name, price))

    unique_menus = {}
    for name, price in menu_sources:
        unique_menus[name] = price

    def clean_text(value):
        value = str(value).lower()
        value = value.replace("คุกกี้", "")
        value = value.replace(" ", "")
        value = value.replace("-", "")
        value = value.replace("_", "")
        value = re.sub(r"\d+", "", value)

        for word in [
            "ชิ้น", "อัน", "กล่อง", "จำนวน",
            "เอา", "รับ", "ซื้อ", "สั่ง", "ขอ", "อยากได้", "อยากสั่ง"
        ]:
            value = value.replace(word, "")

        return value.strip()

    cleaned_message = clean_text(normalized)

    matched_name = None
    matched_price = 0

    for name in sorted(unique_menus.keys(), key=lambda x: -len(x)):
        name_lower = name.lower()
        name_clean = clean_text(name)

        # รองรับทั้งพิมพ์ชื่อเต็มและพิมพ์แบบไม่มีคำว่า “คุกกี้”
        if name_lower in normalized or (name_clean and name_clean in cleaned_message):
            matched_name = name
            matched_price = unique_menus[name]
            break

    if not matched_name:
        return None

    # ถ้าระบุเมนูแต่ไม่ระบุจำนวน ให้ถามจำนวนต่อ ไม่บันทึกมั่ว
    if quantity is None:
        return {
            "menu": matched_name,
            "menu_name": matched_name,
            "name": matched_name,
            "quantity": None,
            "price": matched_price,
            "need_quantity": True,
        }

    return {
        "menu": matched_name,
        "menu_name": matched_name,
        "name": matched_name,
        "quantity": quantity,
        "price": matched_price,
    }

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
- ถ้าลูกค้าถามโปร ให้ตอบโปร Lucky Cookie Tarot
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
            "ได้สุ่ม Lucky Cookie Tarot พร้อมรับฟรีคุกกี้ตามไพ่ที่สุ่มได้ 1 ชิ้นค่ะ 🔮"
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
    from urllib import request

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

        # ถ้าเป็น URL จริงอยู่แล้ว ใช้ได้เลย
        if value.startswith("http://") or value.startswith("https://"):
            return value

        # ถ้าเป็น base64 ให้ decode
        try:
            padding = "=" * (-len(value) % 4)
            decoded = base64.b64decode(value + padding).decode("utf-8").strip()

            if decoded.startswith("http://") or decoded.startswith("https://"):
                return decoded
        except Exception:
            pass

        return value

    web_app_url = ""

    # 1) รองรับ secret แบบ base64 โดยตรง
    web_app_url = decode_b64(read_secret("SHEET_WEB_APP_URL_B64"))

    # 2) รองรับกรณีใส่ base64 ไว้ในชื่อเดิม SHEET_WEB_APP_URL
    if not web_app_url:
        web_app_url = decode_b64(read_secret("SHEET_WEB_APP_URL"))

    # 3) รองรับ env แบบ base64
    if not web_app_url:
        web_app_url = decode_b64(os.getenv("SHEET_WEB_APP_URL_B64", ""))

    # 4) รองรับ env แบบเดิม
    if not web_app_url:
        web_app_url = decode_b64(os.getenv("SHEET_WEB_APP_URL", ""))

    # 5) fallback อ่านจาก script.js
    if not web_app_url:
        possible_script_paths = [
            base_dir / "script.js",
            Path.cwd() / "script.js",
        ]

        for script_path in possible_script_paths:
            try:
                if not script_path.exists():
                    continue

                script_text = script_path.read_text(encoding="utf-8")
                match = re.search(r'const\s+SHEET_WEB_APP_URL\s*=\s*"([^"]+)"', script_text)

                if match:
                    web_app_url = decode_b64(match.group(1).strip())
                    break
            except Exception:
                pass

    if not web_app_url or not web_app_url.startswith("https://"):
        raise RuntimeError(
            "ไม่พบ SHEET_WEB_APP_URL ที่ใช้งานได้ "
            "ให้ใส่ SHEET_WEB_APP_URL_B64 เป็นค่า base64 ของ Apps Script Web App URL"
        )

    payload = {
        "menu": menu_name,
        "menuName": menu_name,
        "menu_name": menu_name,
        "name": menu_name,
        "quantity": quantity,
        "qty": quantity,
        "price": price,
        "total": total,
        "source": "streamlit_popup",
    }

    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")

    req = request.Request(
        web_app_url,
        data=data,
        method="POST",
        headers={"Content-Type": "application/json"},
    )

    with request.urlopen(req, timeout=30) as res:
        response_text = res.read().decode("utf-8", errors="replace")

    print("append_order_to_sheet response:", response_text)

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
            return get_default_hot_menus(limit)

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
            return get_default_hot_menus(limit)

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

        return result or get_default_hot_menus(limit)

    except Exception:
        return get_default_hot_menus(limit)

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

rag = load_rag()

st.title("☁️ Demi ผู้ช่วย AI ของร้าน CookieCloudyDay")
st.caption("ถามเรื่องเมนู เวลาเปิด ราคา หรือข้อมูลร้านได้เลย")


def direct_customer_answer(message: str):
    q = (message or "").lower().strip()

    if q in ["ซื้อ", "สั่ง", "สั่งซื้อ", "ออเดอร์", "order"]:
        return (
            "ได้เลยค่ะ รับคุกกี้อะไรดีคะ 🍪\n\n"
            "ถ้าชอบเข้ม ๆ แนะนำแนวช็อกโกแลตหรือบราวนี่\n"
            "ถ้าชอบละมุน ๆ แนะนำแนวเนยสด วานิลลา หรือเลมอนบัตเตอร์\n"
            "ถ้าชอบพรีเมียม แนะนำแนวแมคคาเดเมีย พิสตาชิโอ หรือบิสคอฟค่ะ\n\n"
            "ลูกค้าพิมพ์ชื่อเมนูพร้อมจำนวนได้เลย เช่น “เอาคุกกี้เลมอนบัตเตอร์ 3 ชิ้น”"
        )

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

    menu_names = [f"{item['name']} — {item['price']} บาท" for item in menus]

    selected_label = st.selectbox(
        "เลือกเมนู",
        menu_names,
        key="popup_selected_menu",
    )

    selected_index = menu_names.index(selected_label)
    selected_item = menus[selected_index]

    quantity = st.number_input(
        "จำนวน",
        min_value=1,
        max_value=999,
        value=1,
        step=1,
        key="popup_quantity",
    )

    total = int(selected_item["price"]) * int(quantity)

    st.info(
        f"รายการ: {selected_item['name']}\n\n"
        f"จำนวน: {int(quantity)} ชิ้น\n\n"
        f"ยอดรวม: {total:,} บาท"
    )

    col1, col2 = st.columns(2)

    with col1:
        if st.button("บันทึกออเดอร์", type="primary", use_container_width=True):
            menu_name = str(selected_item["name"])
            price = int(selected_item["price"])
            qty = int(quantity)
            total = price * qty

            # บันทึกลง Google Sheets ด้วยค่าจาก popup โดยตรง
            try:
                saved_total = append_order_to_sheet(menu_name, qty, price)
                if saved_total:
                    total = int(saved_total)
            except TypeError:
                # เผื่อฟังก์ชันเก่ารับแค่ 2 args
                append_order_to_sheet(menu_name, qty)
                total = price * qty

            # ส่ง Telegram real-time ถ้าตั้ง token/chat id แล้ว
            send_realtime_order_to_telegram(menu_name, qty, price, total)

            promo_text = ""
            if total >= 150:
                st.session_state["lucky_cookie_promo"] = {
                    "quantity": qty,
                    "total": total,
                    "menu": menu_name,
                }
                st.session_state["show_lucky_tarot"] = True
                st.session_state.pop("lucky_tarot_card", None)
                promo_text = "\n\n🎁 ออเดอร์นี้เข้าโปร Lucky Cookie Tarot แล้วค่ะ กดรับไพ่และคำทำนายได้เลย"
            else:
                st.session_state.pop("lucky_cookie_promo", None)
                st.session_state["show_lucky_tarot"] = False

            answer = (
                f"รับออเดอร์เรียบร้อยค่ะ 🍪\n\n"
                f"รายการ: {menu_name}\n"
                f"จำนวน: {qty} ชิ้น\n"
                f"ยอดรวม: {total:,} บาท"
                f"{promo_text}\n\n"
                f"ขอบคุณที่สั่งคุกกี้กับ CookieCloudyDay นะคะ ☁️"
            )

            st.session_state.messages.append({
                "role": "assistant",
                "content": answer,
            })

            st.session_state.show_menu_order_popup = False
            st.rerun()

    with col2:
        if st.button("ปิด", use_container_width=True):
            st.session_state.show_menu_order_popup = False
            st.rerun()

# =========================
# Chatbot
# =========================
if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])


if st.session_state.get("show_menu_order_popup"):
    render_menu_order_popup()

prompt = st.chat_input("ถามอะไรเกี่ยวกับร้านได้เลย...")



if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.chat_message("user"):
        st.write(prompt)

    normalized_prompt = normalize_menu_number_order(prompt)

    if is_menu_popup_request(normalized_prompt):
        st.session_state.show_menu_order_popup = True

        answer = (
            "ได้เลยค่ะ เปิดเมนูทั้งหมดให้เลือกแล้วนะคะ 🍪\n\n"
            "ลูกค้าสามารถเลือกเมนูและจำนวนจากหน้าต่าง popup ได้เลยค่ะ"
        )

        with st.chat_message("assistant", avatar="🤖"):
            st.markdown(answer)

        st.session_state.messages.append({
            "role": "assistant",
            "content": answer,
        })

        st.rerun()

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
